-- Scientific prose uses characters that most text fonts lack (Greek letters, relations,
-- arrows, Unicode sub- and superscripts). xelatex drops a missing character from the PDF
-- and only logs a warning. For LaTeX output this filter wraps each such character in
-- \makedocchar{codepoint}{fallback}, defined in the layout header, which uses the text
-- font's own glyph when it has one and the fallback otherwise. Math and code are untouched.

if not FORMAT:match("latex") then
  return {}
end

local fallback = {
  [0x03B1] = [[\ensuremath{\alpha}]],
  [0x03B2] = [[\ensuremath{\beta}]],
  [0x03B3] = [[\ensuremath{\gamma}]],
  [0x03B4] = [[\ensuremath{\delta}]],
  [0x03B5] = [[\ensuremath{\varepsilon}]],
  [0x03B6] = [[\ensuremath{\zeta}]],
  [0x03B7] = [[\ensuremath{\eta}]],
  [0x03B8] = [[\ensuremath{\theta}]],
  [0x03B9] = [[\ensuremath{\iota}]],
  [0x03BA] = [[\ensuremath{\kappa}]],
  [0x03BB] = [[\ensuremath{\lambda}]],
  [0x03BD] = [[\ensuremath{\nu}]],
  [0x03BE] = [[\ensuremath{\xi}]],
  [0x03C0] = [[\ensuremath{\pi}]],
  [0x03C1] = [[\ensuremath{\rho}]],
  [0x03C3] = [[\ensuremath{\sigma}]],
  [0x03C2] = [[\ensuremath{\varsigma}]],
  [0x03C4] = [[\ensuremath{\tau}]],
  [0x03C5] = [[\ensuremath{\upsilon}]],
  [0x03C6] = [[\ensuremath{\varphi}]],
  [0x03D5] = [[\ensuremath{\phi}]],
  [0x03C7] = [[\ensuremath{\chi}]],
  [0x03C8] = [[\ensuremath{\psi}]],
  [0x03C9] = [[\ensuremath{\omega}]],
  [0x03D1] = [[\ensuremath{\vartheta}]],
  [0x03F5] = [[\ensuremath{\epsilon}]],
  [0x0393] = [[\ensuremath{\Gamma}]],
  [0x0394] = [[\ensuremath{\Delta}]],
  [0x0398] = [[\ensuremath{\Theta}]],
  [0x039B] = [[\ensuremath{\Lambda}]],
  [0x039E] = [[\ensuremath{\Xi}]],
  [0x03A0] = [[\ensuremath{\Pi}]],
  [0x03A3] = [[\ensuremath{\Sigma}]],
  [0x03A5] = [[\ensuremath{\Upsilon}]],
  [0x03A6] = [[\ensuremath{\Phi}]],
  [0x03A8] = [[\ensuremath{\Psi}]],
  [0x03A9] = [[\ensuremath{\Omega}]],
  [0x2264] = [[\ensuremath{\leq}]],
  [0x2265] = [[\ensuremath{\geq}]],
  [0x2248] = [[\ensuremath{\approx}]],
  [0x2260] = [[\ensuremath{\neq}]],
  [0x2261] = [[\ensuremath{\equiv}]],
  [0x226A] = [[\ensuremath{\ll}]],
  [0x226B] = [[\ensuremath{\gg}]],
  [0x223C] = [[\ensuremath{\sim}]],
  [0x2243] = [[\ensuremath{\simeq}]],
  [0x2245] = [[\ensuremath{\cong}]],
  [0x221D] = [[\ensuremath{\propto}]],
  [0x221E] = [[\ensuremath{\infty}]],
  [0x2202] = [[\ensuremath{\partial}]],
  [0x2207] = [[\ensuremath{\nabla}]],
  [0x2211] = [[\ensuremath{\sum}]],
  [0x220F] = [[\ensuremath{\prod}]],
  [0x222B] = [[\ensuremath{\int}]],
  [0x221A] = [[\ensuremath{\surd}]],
  [0x2208] = [[\ensuremath{\in}]],
  [0x2209] = [[\ensuremath{\notin}]],
  [0x2282] = [[\ensuremath{\subset}]],
  [0x2286] = [[\ensuremath{\subseteq}]],
  [0x222A] = [[\ensuremath{\cup}]],
  [0x2229] = [[\ensuremath{\cap}]],
  [0x2205] = [[\ensuremath{\emptyset}]],
  [0x2200] = [[\ensuremath{\forall}]],
  [0x2203] = [[\ensuremath{\exists}]],
  [0x2192] = [[\ensuremath{\rightarrow}]],
  [0x2190] = [[\ensuremath{\leftarrow}]],
  [0x2194] = [[\ensuremath{\leftrightarrow}]],
  [0x21D2] = [[\ensuremath{\Rightarrow}]],
  [0x21D0] = [[\ensuremath{\Leftarrow}]],
  [0x21D4] = [[\ensuremath{\Leftrightarrow}]],
  [0x2191] = [[\ensuremath{\uparrow}]],
  [0x2193] = [[\ensuremath{\downarrow}]],
  [0x21A6] = [[\ensuremath{\mapsto}]],
  [0x2213] = [[\ensuremath{\mp}]],
  [0x22C5] = [[\ensuremath{\cdot}]],
  [0x2217] = [[\ensuremath{\ast}]],
  [0x2218] = [[\ensuremath{\circ}]],
  [0x2295] = [[\ensuremath{\oplus}]],
  [0x2297] = [[\ensuremath{\otimes}]],
  [0x2227] = [[\ensuremath{\wedge}]],
  [0x2228] = [[\ensuremath{\vee}]],
  [0x00AC] = [[\ensuremath{\neg}]],
  [0x2113] = [[\ensuremath{\ell}]],
  [0x210F] = [[\ensuremath{\hbar}]],
  [0x2220] = [[\ensuremath{\angle}]],
  [0x22A5] = [[\ensuremath{\perp}]],
  [0x2225] = [[\ensuremath{\parallel}]],
  [0x2223] = [[\ensuremath{\mid}]],
  [0x2272] = [[\ensuremath{\lesssim}]],
  [0x2273] = [[\ensuremath{\gtrsim}]],
  [0x227A] = [[\ensuremath{\prec}]],
  [0x227B] = [[\ensuremath{\succ}]],
  [0x27E8] = [[\ensuremath{\langle}]],
  [0x27E9] = [[\ensuremath{\rangle}]],
  [0x2605] = [[\ensuremath{\star}]],
  [0x2299] = [[\ensuremath{\odot}]],
  [0x2032] = [[\ensuremath{\prime}]],
  [0x2033] = [[\ensuremath{\prime\prime}]],
  [0x2080] = [[\textsubscript{0}]],
  [0x2081] = [[\textsubscript{1}]],
  [0x2082] = [[\textsubscript{2}]],
  [0x2083] = [[\textsubscript{3}]],
  [0x2084] = [[\textsubscript{4}]],
  [0x2085] = [[\textsubscript{5}]],
  [0x2086] = [[\textsubscript{6}]],
  [0x2087] = [[\textsubscript{7}]],
  [0x2088] = [[\textsubscript{8}]],
  [0x2089] = [[\textsubscript{9}]],
  [0x208A] = [[\textsubscript{+}]],
  [0x208B] = [[\textsubscript{-}]],
  [0x208C] = [[\textsubscript{=}]],
  [0x208D] = [[\textsubscript{(}]],
  [0x208E] = [[\textsubscript{)}]],
  [0x2090] = [[\textsubscript{a}]],
  [0x2091] = [[\textsubscript{e}]],
  [0x2092] = [[\textsubscript{o}]],
  [0x2093] = [[\textsubscript{x}]],
  [0x2095] = [[\textsubscript{h}]],
  [0x2096] = [[\textsubscript{k}]],
  [0x2097] = [[\textsubscript{l}]],
  [0x2098] = [[\textsubscript{m}]],
  [0x2099] = [[\textsubscript{n}]],
  [0x209A] = [[\textsubscript{p}]],
  [0x209B] = [[\textsubscript{s}]],
  [0x209C] = [[\textsubscript{t}]],
  [0x1D62] = [[\textsubscript{i}]],
  [0x2C7C] = [[\textsubscript{j}]],
  [0x1D63] = [[\textsubscript{r}]],
  [0x1D64] = [[\textsubscript{u}]],
  [0x1D65] = [[\textsubscript{v}]],
  [0x2070] = [[\textsuperscript{0}]],
  [0x2074] = [[\textsuperscript{4}]],
  [0x2075] = [[\textsuperscript{5}]],
  [0x2076] = [[\textsuperscript{6}]],
  [0x2077] = [[\textsuperscript{7}]],
  [0x2078] = [[\textsuperscript{8}]],
  [0x2079] = [[\textsuperscript{9}]],
  [0x207A] = [[\textsuperscript{+}]],
  [0x207B] = [[\textsuperscript{-}]],
  [0x207C] = [[\textsuperscript{=}]],
  [0x207D] = [[\textsuperscript{(}]],
  [0x207E] = [[\textsuperscript{)}]],
  [0x207F] = [[\textsuperscript{n}]],
  [0x2071] = [[\textsuperscript{i}]],
  [0x2009] = [[\,]],
  [0x202F] = [[\,]],
  [0x2003] = [[\quad{}]],
  [0x2002] = [[\enspace{}]],
  [0x2011] = [[\mbox{-}]],
  [0x2713] = [[\ensuremath{\checkmark}]],
  [0x2717] = [[\ensuremath{\times}]],
  [0x2030] = [[\textperthousand{}]],
  [0x2044] = [[/]],
  [0x03BC] = [[\char"00B5\relax{}]],
}

local function replace(el)
  if not el.text:find("[\194-\244]") then
    return nil
  end
  local out, plain = {}, {}
  local function flush()
    if #plain > 0 then
      out[#out + 1] = pandoc.Str(table.concat(plain))
      plain = {}
    end
  end
  for _, code in utf8.codes(el.text) do
    local replacement = fallback[code]
    if replacement then
      flush()
      out[#out + 1] = pandoc.RawInline("latex", string.format("\\makedocchar{%04X}{%s}", code, replacement))
    else
      plain[#plain + 1] = utf8.char(code)
    end
  end
  flush()
  return out
end

local function needs_fallback(text)
  for _, code in utf8.codes(text) do
    if fallback[code] then
      return true
    end
  end
  return false
end

-- Pandoc builds PDF metadata and bookmarks from plain text and drops raw LaTeX, so the
-- fallbacks above would remove these characters from the PDF title, author and outline.
-- The two passes below run before the replacement and keep the original characters there.

-- Record the plain title and author for the PDF metadata fields.
local function keep_plain_metadata(meta)
  for _, key in ipairs({ "title", "author" }) do
    local plain_key = key .. "-meta"
    if meta[key] and not meta[plain_key] then
      local value = meta[key]
      if pandoc.utils.type(value) == "List" then
        local names = pandoc.List()
        for _, item in ipairs(value) do
          names:insert(pandoc.utils.stringify(item))
        end
        meta[plain_key] = table.concat(names, "; ")
      else
        meta[plain_key] = pandoc.utils.stringify(value)
      end
    end
  end
  return meta
end

-- Write a heading that needs fallbacks as LaTeX ourselves, giving hyperref the original
-- text for the bookmark.
local commands = { "section", "subsection", "subsubsection", "paragraph", "subparagraph" }

local function heading_with_bookmark(header)
  local plain = pandoc.utils.stringify(header.content)
  local command = commands[header.level]
  if not command or not needs_fallback(plain) then
    return nil
  end
  local content = pandoc.Plain(header.content):walk({ Str = replace })
  local typeset = pandoc.write(pandoc.Pandoc({ content }), "latex"):gsub("%s+$", "")
  local escaped = pandoc.write(pandoc.Pandoc({ pandoc.Plain({ pandoc.Str(plain) }) }), "latex"):gsub("%s+$", "")
  -- Name each fallback character by code point: written literally, some of them make
  -- LaTeX report on every run that labels have changed.
  local bookmark = {}
  for _, code in utf8.codes(escaped) do
    bookmark[#bookmark + 1] = fallback[code] and string.format('\\unichar{"%04X}', code) or utf8.char(code)
  end
  escaped = table.concat(bookmark)
  local label = header.identifier ~= "" and ("\\label{" .. header.identifier .. "}") or ""
  return pandoc.RawBlock(
    "latex",
    string.format("\\%s{\\texorpdfstring{%s}{%s}}%s", command, typeset, escaped, label)
  )
end

return {
  { Meta = keep_plain_metadata },
  { Header = heading_with_bookmark },
  { Str = replace },
}
