-- Arranges the parsed manuscript according to the build profile.
--
-- Input: the concatenated sources, where each file is preceded by a raw block of format
-- `makedoc-source` holding that file's directory, and a `makedoc` metadata map written by
-- build.py (placement, caption_position, placeholder_id, references_new_page, author_block).
--
-- It resolves image paths, inserts the author block, moves figures to where the profile
-- wants them, anchors the bibliography and inserts page breaks. Working on the parsed
-- document means code blocks, code spans and HTML comments can never be mistaken for
-- manuscript structure.
--
-- Problems the author must fix are reported as `[makedoc-error] ...` on stderr followed
-- by a Lua error; warnings as `[WARNING] ...`. build.py reads both.

local stringify = pandoc.utils.stringify

local function warn(message)
  io.stderr:write("[WARNING] " .. message .. "\n")
end

local function fail(message)
  io.stderr:write("[makedoc-error] " .. message .. "\n")
  error("makedoc")
end

local function words(text)
  local inlines = pandoc.List()
  for word in text:gmatch("%S+") do
    if #inlines > 0 then
      inlines:insert(pandoc.Space())
    end
    inlines:insert(pandoc.Str(word))
  end
  return inlines
end

-- Page breaks -------------------------------------------------------------------------

local function page_break()
  return {
    pandoc.RawBlock("latex", "\\clearpage"),
    pandoc.RawBlock("openxml", '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'),
  }
end

local function break_kind(block)
  if not block or block.t ~= "RawBlock" then
    return nil
  end
  if block.format == "latex" or block.format == "tex" then
    if block.text:find("\\clearpage", 1, true) or block.text:find("\\newpage", 1, true) then
      return "latex"
    end
  elseif block.format == "openxml" and block.text:find('w:type="page"', 1, true) then
    return "openxml"
  end
  return nil
end

-- Add a page break for whichever output format does not already have one at the end of
-- `blocks`, so an author's own \clearpage is not doubled in the PDF yet still gets its
-- DOCX counterpart.
local function append_break(blocks)
  local present = {}
  local index = #blocks
  while index > 0 and break_kind(blocks[index]) do
    present[break_kind(blocks[index])] = true
    index = index - 1
  end
  for _, block in ipairs(page_break()) do
    if not present[break_kind(block)] then
      blocks:insert(block)
    end
  end
end

-- Image paths -------------------------------------------------------------------------

local function percent_decode(text)
  return (text:gsub("%%(%x%x)", function(hex)
    return string.char(tonumber(hex, 16))
  end))
end

local function is_remote(src)
  return src:match("^%a[%w+.-]*:") ~= nil or src:sub(1, 2) == "//"
end

-- Remove "." and ".." components, which pandoc.path.normalize leaves in place.
local function collapse(path)
  local parts = pandoc.List()
  for _, part in ipairs(pandoc.path.split(path)) do
    if part == ".." and #parts > 0 and parts[#parts] ~= ".." and not parts[#parts]:match("[/\\]$") then
      parts:remove(#parts)
    elseif part ~= "." then
      parts:insert(part)
    end
  end
  return pandoc.path.join(parts)
end

local function resolve_image(image, source_dir)
  local src = image.src
  if src == "" or is_remote(src) then
    return image
  end
  local path = percent_decode(src)
  if path:sub(1, 2) == "~/" then
    path = pandoc.path.join({ os.getenv("HOME") or "~", path:sub(3) })
  end
  if pandoc.path.is_relative(path) then
    if not source_dir then
      return image
    end
    path = pandoc.path.join({ source_dir, path })
  end
  path = collapse(path)
  local handle = io.open(path, "rb")
  if not handle then
    fail("Image file not found: " .. percent_decode(src) .. " -> " .. path)
  end
  handle:close()
  image.src = path
  return image
end

local function resolve_images(blocks)
  local out = pandoc.List()
  local source_dir = nil
  for _, block in ipairs(blocks) do
    if block.t == "RawBlock" and block.format == "makedoc-source" then
      source_dir = block.text
    else
      local dir = source_dir
      out:insert(pandoc.walk_block(block, {
        RawBlock = function(raw)
          if raw.format == "makedoc-source" then
            fail("A source file ends inside an unclosed block (such as a ':::' div or a list), which "
              .. "swallowed the start of the next file, the one in " .. raw.text .. ". Close the block.")
          end
        end,
        Image = function(image)
          return resolve_image(image, dir)
        end,
      }))
    end
  end
  return out
end

-- Authors -----------------------------------------------------------------------------

local function insert_authors(blocks, author_block)
  local addition = author_block:clone()
  addition:extend(page_break())

  for index, block in ipairs(blocks) do
    if block.t == "Div" and block.identifier == "authors" then
      blocks:remove(index)
      for offset, item in ipairs(addition) do
        blocks:insert(index + offset - 1, item)
      end
      return blocks
    end
  end
  for index, block in ipairs(blocks) do
    if block.t == "Header" and block.level == 1 then
      for offset, item in ipairs(addition) do
        blocks:insert(index + offset, item)
      end
      return blocks
    end
  end
  fail('author_metadata is set but there is nowhere to put the authors. Add <div id="authors"></div> '
    .. "or start the manuscript with a '# Title' heading.")
end

-- Figures -----------------------------------------------------------------------------

-- A figure is a top-level paragraph holding nothing but an image. Pandoc parses that as a
-- Figure block when the image has a caption and as a plain paragraph when it has none.
-- Figure lines written one per line with no blank line between them arrive as a single
-- paragraph of images separated by soft breaks; each of those images is a figure too.
local function from_figure_block(block)
  local image = nil
  pandoc.walk_block(block, {
    Image = function(found)
      image = image or found
    end,
  })
  if not image then
    return nil
  end
  local id = block.identifier ~= "" and block.identifier or image.identifier
  return { block = block, image = image, id = id, caption = pandoc.utils.blocks_to_inlines(block.caption.long) }
end

local function from_image(image)
  local id = image.identifier
  if #image.caption == 0 then
    return { block = pandoc.Para({ image }), image = image, id = id, caption = image.caption }
  end
  -- Build the block Pandoc's reader would have made had the image stood alone.
  local inner = image:clone()
  inner.identifier = ""
  local block = pandoc.Figure({ pandoc.Plain({ inner }) }, { long = { pandoc.Plain(image.caption) } }, pandoc.Attr(id))
  return { block = block, image = inner, id = id, caption = image.caption }
end

local function images_only(block)
  if block.t ~= "Para" then
    return nil
  end
  local images = pandoc.List()
  for _, inline in ipairs(block.content) do
    if inline.t == "Image" then
      images:insert(inline)
    elseif inline.t ~= "SoftBreak" then
      return nil
    end
  end
  return #images > 0 and images or nil
end

-- Each figure leaves a marker where it stood, used by the in_place placement and removed
-- by the others.
local FIGURE_MARKER = "makedoc-figure"

local function extract_figures(blocks)
  local rest, figures = pandoc.List(), pandoc.List()
  for _, block in ipairs(blocks) do
    local found = pandoc.List()
    if block.t == "Figure" then
      local figure = from_figure_block(block)
      if figure then
        found:insert(figure)
      end
    else
      for _, image in ipairs(images_only(block) or {}) do
        found:insert(from_image(image))
      end
    end
    if #found == 0 then
      rest:insert(block)
    end
    for _, figure in ipairs(found) do
      figures:insert(figure)
      rest:insert(pandoc.RawBlock(FIGURE_MARKER, tostring(#figures)))
    end
  end
  return rest, figures
end

-- Main figures are numbered in order of appearance. An id ending in -s<number> marks a
-- supplementary figure, labelled with that number and placed after the main figures.
-- In running text an image with no caption is left unlabelled, so it takes no number.
local function label_figures(figures, in_text)
  local mains, supplements = pandoc.List(), pandoc.List()
  local main_count = 0
  for _, figure in ipairs(figures) do
    local number = figure.id:lower():match("%-s(%d+)$")
    if in_text and #figure.caption == 0 then
      figure.label = ""
      (number and supplements or mains):insert(figure)
    elseif number then
      figure.label = "Fig. S" .. number .. "."
      supplements:insert(figure)
    else
      main_count = main_count + 1
      figure.label = "Fig. " .. main_count .. "."
      mains:insert(figure)
    end
  end
  return mains, supplements
end

-- makedoc writes every arranged figure itself, as a caption paragraph ("Fig. 1. Text")
-- and an image paragraph, so the label is the only number on the page. For LaTeX the two
-- are handed to \makedocfigure... (layout.py), which keeps them together, centres the
-- image and limits its height to what the caption leaves of the page. The id sits on the
-- label because LaTeX output drops the id of an inline image.
local function caption_para(figure, with_text)
  local label = pandoc.Strong(words(figure.label))
  local line = pandoc.List({ figure.id ~= "" and pandoc.Span({ label }, pandoc.Attr(figure.id)) or label })
  if with_text and #figure.caption > 0 then
    line:insert(pandoc.Space())
    line:extend(figure.caption)
  end
  return pandoc.Para(line)
end

local function image_para(figure)
  local image = figure.image:clone()
  image.identifier = ""
  image.caption = figure.caption
  return pandoc.Para({ image })
end

local function rendered(figure, caption_position, with_text)
  local first, second, command = caption_para(figure, with_text), image_para(figure), "\\makedocfiguretop"
  if caption_position == "bottom" then
    first, second, command = second, first, "\\makedocfigurebottom"
  end
  return {
    pandoc.RawBlock("latex", command),
    first,
    pandoc.RawBlock("latex", "\\makedocsep"),
    second,
    pandoc.RawBlock("latex", "\\makedocend"),
  }
end

-- In running text an image with no caption is left as the author wrote it.
local function rendered_in_text(figure, caption_position)
  if #figure.caption == 0 then
    return { figure.block }
  end
  return rendered(figure, caption_position, true)
end

local function supplementary_heading()
  return pandoc.Header(2, words("Supplementary Information"), pandoc.Attr("supplementary-information"))
end

local function end_pages(mains, supplements, render)
  local out = pandoc.List()
  for _, figure in ipairs(mains) do
    out:extend(page_break())
    out:extend(render(figure))
  end
  if #supplements > 0 then
    if #mains > 0 then
      out:extend(page_break())
      out:insert(supplementary_heading())
    end
    for _, figure in ipairs(supplements) do
      out:extend(page_break())
      out:extend(render(figure))
    end
  end
  return out
end

local function without_markers(blocks, replacement)
  local out = pandoc.List()
  for _, block in ipairs(blocks) do
    if block.t == "RawBlock" and block.format == FIGURE_MARKER then
      if replacement then
        out:extend(replacement(tonumber(block.text)))
      end
    else
      out:insert(block)
    end
  end
  return out
end

local function place_figures(blocks, figures, config)
  if #figures == 0 then
    return blocks
  end
  local mains, supplements = label_figures(figures, config.placement == "inline" or config.placement == "in_place")
  local ordered = mains:clone()
  ordered:extend(supplements)

  if config.placement == "in_place" then
    return without_markers(blocks, function(index)
      return rendered_in_text(figures[index], config.caption_position)
    end)
  end
  blocks = without_markers(blocks)
  for _, figure in ipairs(figures) do
    if figure.id == "" then
      warn("a figure has no #id in its attributes, so the text cannot link to it: " .. figure.image.src)
    end
  end

  if config.placement == "captions_page" then
    blocks:extend(page_break())
    blocks:insert(pandoc.Header(2, words("Figure Captions"), pandoc.Attr("figure-captions")))
    for _, figure in ipairs(ordered) do
      local line = pandoc.List({ pandoc.Strong(words(figure.label)) })
      if #figure.caption > 0 then
        line:insert(pandoc.Space())
        line:extend(figure.caption)
      end
      blocks:insert(pandoc.Para(line))
    end
    blocks:extend(end_pages(mains, supplements, function(figure)
      return rendered(figure, "top", false)
    end))
    return blocks
  end

  if config.placement == "inline" then
    local inline_blocks = pandoc.List()
    for _, figure in ipairs(ordered) do
      inline_blocks:extend(rendered_in_text(figure, config.caption_position))
    end
    for index, block in ipairs(blocks) do
      if block.t == "Div" and block.identifier == config.placeholder_id then
        blocks:remove(index)
        for offset, item in ipairs(inline_blocks) do
          blocks:insert(index + offset - 1, item)
        end
        return blocks
      end
    end
    warn('no <div id="' .. config.placeholder_id .. '"></div> placeholder found; figures appended at the end')
    blocks:extend(inline_blocks)
    return blocks
  end

  blocks:extend(end_pages(mains, supplements, function(figure)
    return rendered(figure, config.caption_position, true)
  end))
  return blocks
end

-- Sections ----------------------------------------------------------------------------

local function heading_starts_with(block, word)
  if block.t ~= "Header" then
    return false
  end
  return stringify(block.content):lower():match("^%s*" .. word .. "%f[%W]") ~= nil
end

local function has_refs_div(blocks)
  local found = false
  pandoc.walk_block(pandoc.Div(blocks), {
    Div = function(div)
      found = found or div.identifier == "refs"
    end,
  })
  return found
end

-- The first Introduction heading starts a page. The bibliography goes under the first
-- References heading, or at the end of the text when there is none, so that figures
-- appended afterwards follow it.
local function arrange_sections(blocks, references_new_page)
  local out = pandoc.List()
  local anchored = has_refs_div(blocks)
  local intro_done, refs_done = false, false
  for _, block in ipairs(blocks) do
    if not intro_done and heading_starts_with(block, "introduction") then
      intro_done = true
      append_break(out)
      out:insert(block)
    elseif not refs_done and heading_starts_with(block, "references") then
      refs_done = true
      if references_new_page then
        append_break(out)
      end
      out:insert(block)
      if not anchored then
        out:insert(pandoc.Div({}, pandoc.Attr("refs")))
        anchored = true
      end
    else
      out:insert(block)
    end
  end
  if not anchored then
    out:insert(pandoc.Div({}, pandoc.Attr("refs")))
  end
  return out
end

-- Entry point -------------------------------------------------------------------------

local function setting(map, key, default)
  local value = map[key]
  if value == nil then
    return default
  end
  if type(value) == "boolean" then
    return value
  end
  return stringify(value)
end

local function meta_blocks(value)
  if value == nil then
    return nil
  end
  if pandoc.utils.type(value) == "Blocks" then
    return value
  end
  return pandoc.Blocks({ pandoc.Para(value) })
end

function Pandoc(doc)
  local map = doc.meta.makedoc or {}
  local config = {
    placement = setting(map, "placement", "pages"),
    caption_position = setting(map, "caption_position", "top"),
    placeholder_id = setting(map, "placeholder_id", "figures"),
    references_new_page = setting(map, "references_new_page", true),
  }
  local author_block = meta_blocks(map.author_block)
  doc.meta.makedoc = nil

  local blocks = resolve_images(doc.blocks)
  if author_block then
    blocks = insert_authors(blocks, author_block)
  end
  local figures
  blocks, figures = extract_figures(blocks)
  blocks = arrange_sections(blocks, config.references_new_page)
  blocks = place_figures(blocks, figures, config)
  return pandoc.Pandoc(blocks, doc.meta)
end
