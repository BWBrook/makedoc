from __future__ import annotations

import sys
import shutil
import subprocess
import tempfile
import zipfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from normalize_docx_styles import (
    LINE_ATTR,
    LINE_NUMBERING_COUNTBY_ATTR,
    LINE_NUMBERING_DISTANCE_ATTR,
    LINE_NUMBERING_RESTART_ATTR,
    LINE_NUMBERING_START_ATTR,
    LINE_RULE_ATTR,
    LNNUMTYPE_TAG,
    NS,
    SECTPR_TAG,
    W_NS,
    normalize_heading_styles,
    normalize_line_numbering,
    normalize_line_spacing,
    normalize_document_layout,
    rewrite_docx,
    serialize_xml,
)


STYLE_ID_ATTR = f"{{{W_NS}}}styleId"


class NormalizeDocxStylesTests(unittest.TestCase):
    def test_normalize_heading_styles_updates_heading_only(self) -> None:
        styles_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:rPr>
      <w:color w:val="4472C4" w:themeColor="accent1" />
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:rPr>
      <w:color w:val="00FF00" />
    </w:rPr>
  </w:style>
</w:styles>
"""

        normalized = normalize_heading_styles(styles_xml, "000000")
        root = ET.fromstring(normalized)
        styles = {style.attrib[STYLE_ID_ATTR]: style for style in root.findall("w:style", NS)}

        heading_color = styles["Heading1"].find("w:rPr/w:color", NS)
        self.assertIsNotNone(heading_color)
        self.assertEqual(heading_color.attrib[f"{{{W_NS}}}val"], "000000")
        self.assertNotIn(f"{{{W_NS}}}themeColor", heading_color.attrib)

        normal_color = styles["Normal"].find("w:rPr/w:color", NS)
        self.assertIsNotNone(normal_color)
        self.assertEqual(normal_color.attrib[f"{{{W_NS}}}val"], "00FF00")

    def test_normalize_line_spacing_updates_paragraph_styles(self) -> None:
        styles_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Heading1" />
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:pPr />
  </w:style>
  <w:style w:type="character" w:styleId="Emphasis" />
</w:styles>
"""

        normalized = normalize_line_spacing(styles_xml, "1.25")
        root = ET.fromstring(normalized)
        for style in root.findall("w:style", NS):
            if style.attrib.get(f"{{{W_NS}}}type") != "paragraph":
                continue
            spacing = style.find("w:pPr/w:spacing", NS)
            self.assertIsNotNone(spacing)
            self.assertEqual(spacing.attrib[LINE_ATTR], "300")
            self.assertEqual(spacing.attrib[LINE_RULE_ATTR], "auto")

    def test_normalize_line_numbering_adds_expected_page_settings(self) -> None:
        document_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p />
    <w:sectPr />
  </w:body>
</w:document>
"""

        normalized = normalize_line_numbering(document_xml, "page")
        root = ET.fromstring(normalized)
        sect_pr = root.find(f".//{SECTPR_TAG}")
        self.assertIsNotNone(sect_pr)
        line_numbering = sect_pr.find(LNNUMTYPE_TAG)
        self.assertIsNotNone(line_numbering)
        self.assertEqual(line_numbering.attrib[LINE_NUMBERING_RESTART_ATTR], "newPage")
        self.assertEqual(line_numbering.attrib[LINE_NUMBERING_COUNTBY_ATTR], "1")
        self.assertEqual(line_numbering.attrib[LINE_NUMBERING_DISTANCE_ATTR], "360")
        self.assertEqual(line_numbering.attrib[LINE_NUMBERING_START_ATTR], "1")

    def test_normalize_line_numbering_removes_existing_settings_when_disabled(self) -> None:
        document_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:sectPr>
      <w:lnNumType w:restart="continuous" w:countBy="1" w:distance="360" w:start="1" />
    </w:sectPr>
  </w:body>
</w:document>
"""

        normalized = normalize_line_numbering(document_xml, "none")
        root = ET.fromstring(normalized)
        sect_pr = root.find(f".//{SECTPR_TAG}")
        self.assertIsNotNone(sect_pr)
        self.assertIsNone(sect_pr.find(LNNUMTYPE_TAG))


    def test_namespace_prefixes_and_ignorable_declarations_survive(self) -> None:
        source = b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14"><w:body><w:sectPr/></w:body></w:document>'
        output = normalize_line_numbering(source, "continuous")
        self.assertIn(b"<w:document", output)
        self.assertIn(b'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"', output)
        self.assertIn(b'mc:Ignorable="w14"', output)
        self.assertNotIn(b"ns0:", output)
        ET.fromstring(output)

    def test_spacing_rows_and_heading_layout_preserve_content(self) -> None:
        source = b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><w:body><w:p/><w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:t>Heading</w:t></w:r></w:p><w:p><m:oMath><m:r><m:t>x</m:t></m:r></m:oMath></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>main_70</w:t></w:r></w:p></w:tc></w:tr></w:tbl><w:sectPr/></w:body></w:document>'
        output = normalize_document_layout(source, paper_size="letter", margin_unit="in",
            margins={side: 1.0 for side in ("top", "right", "bottom", "left")})
        root = ET.fromstring(output)
        self.assertEqual(root.find(".//w:pgSz", NS).get(f"{{{W_NS}}}w"), "12240")
        self.assertEqual(root.find(".//w:pgMar", NS).get(f"{{{W_NS}}}left"), "1440")
        paras = root.findall("w:body/w:p", NS)
        self.assertIsNotNone(paras[0].find("w:pPr/w:suppressLineNumbers", NS))
        self.assertIsNotNone(paras[1].find("w:pPr/w:keepNext", NS))
        self.assertIsNone(paras[2].find("w:pPr/w:suppressLineNumbers", NS))
        self.assertIsNotNone(root.find(".//w:trPr/w:cantSplit", NS))
        self.assertEqual(root.find(".//w:tblLayout", NS).get(f"{{{W_NS}}}type"), "autofit")
        self.assertEqual(list(ET.fromstring(source).itertext()), list(root.itertext()))

    def test_table_lead_in_chain_does_not_keep_table_cells_or_rows_together(self) -> None:
        source = f'''<w:document xmlns:w="{W_NS}"><w:body>
          <w:p><w:pPr><w:pStyle w:val="Heading2"/><w:keepNext w:val="0"/></w:pPr>
            <w:r><w:t>Table heading</w:t></w:r></w:p>
          <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Subcaption.</w:t></w:r></w:p>
          <w:p><w:r><w:t>Introduction immediately before the table.</w:t></w:r></w:p>
          <w:tbl>
            <w:tr><w:tc>
              <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Bold cell</w:t></w:r></w:p>
              <w:p><w:r><w:t>Cell lead-in.</w:t></w:r></w:p>
              <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Nested cell</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
              <w:p/>
            </w:tc></w:tr>
            <w:tr><w:tc><w:p><w:r><w:t>Second row</w:t></w:r></w:p></w:tc></w:tr>
          </w:tbl>
          <w:p><w:r><w:t>Following body.</w:t></w:r></w:p><w:sectPr/>
        </w:body></w:document>'''.encode()
        output = normalize_document_layout(source, paper_size="a4", margin_unit="cm",
            margins={side: 2.5 for side in ("top", "right", "bottom", "left")})
        root = ET.fromstring(output)
        body_paragraphs = root.findall("w:body/w:p", NS)
        for paragraph in body_paragraphs[:3]:
            self.assertEqual(paragraph.find("w:pPr/w:keepNext", NS).get(f"{{{W_NS}}}val"), "1")
        self.assertIsNone(body_paragraphs[3].find("w:pPr/w:keepNext", NS))
        for paragraph in root.findall(".//w:tc/w:p", NS):
            self.assertIsNone(paragraph.find("w:pPr/w:keepNext", NS))
        self.assertEqual(len(root.findall(".//w:trPr/w:cantSplit", NS)), 3)
        self.assertEqual(list(ET.fromstring(source).itertext()), list(root.itertext()))

    def test_list_lead_in_stops_at_first_item_even_when_items_are_bold(self) -> None:
        source = f'''<w:document xmlns:w="{W_NS}"><w:body>
          <w:p><w:pPr><w:pStyle w:val="Heading3"/></w:pPr><w:r><w:t>Heading</w:t></w:r></w:p>
          <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Covariates.</w:t></w:r>
            <w:r><w:t> The terms were:</w:t></w:r></w:p>
          <w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr>
            <w:r><w:rPr><w:b/></w:rPr><w:t>First item</w:t></w:r></w:p>
          <w:p><w:pPr><w:numPr><w:ilvl w:val="1"/><w:numId w:val="1"/></w:numPr></w:pPr>
            <w:r><w:rPr><w:b/></w:rPr><w:t>Nested item</w:t></w:r></w:p>
          <w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr>
            <w:r><w:t>Second item</w:t></w:r></w:p>
          <w:p><w:r><w:t>Following body.</w:t></w:r></w:p><w:sectPr/>
        </w:body></w:document>'''.encode()
        output = normalize_document_layout(source, paper_size="a4", margin_unit="cm",
            margins={side: 2.5 for side in ("top", "right", "bottom", "left")})
        root = ET.fromstring(output)
        paragraphs = root.findall("w:body/w:p", NS)
        for paragraph in paragraphs[:2]:
            self.assertIsNotNone(paragraph.find("w:pPr/w:keepNext", NS))
        for paragraph in paragraphs[2:]:
            self.assertIsNone(paragraph.find("w:pPr/w:keepNext", NS))

    def test_standalone_bold_rule_ignores_partial_bold_and_explicit_page_breaks(self) -> None:
        source = f'''<w:document xmlns:w="{W_NS}"><w:body>
          <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>S8a(i).</w:t></w:r>
            <w:r><w:t> </w:t></w:r>
            <w:r><w:rPr><w:b w:val="true"/></w:rPr><w:t>Support.</w:t></w:r></w:p>
          <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Partial.</w:t></w:r>
            <w:r><w:t> Plain body.</w:t></w:r></w:p>
          <w:p><w:r><w:rPr><w:b w:val="false"/></w:rPr><w:t>Not bold.</w:t></w:r></w:p>
          <w:p><w:r><w:br w:type="page"/></w:r></w:p>
          <w:p><w:pPr><w:numPr><w:numId w:val="1"/></w:numPr></w:pPr>
            <w:r><w:t>Item after explicit page break.</w:t></w:r></w:p>
          <w:p><w:pPr><w:numPr><w:numId w:val="0"/></w:numPr></w:pPr>
            <w:r><w:t>Unnumbered lead-in.</w:t></w:r></w:p>
          <w:p><w:pPr><w:numPr><w:numId w:val="2"/></w:numPr></w:pPr>
            <w:r><w:t>New list.</w:t></w:r></w:p><w:sectPr/>
        </w:body></w:document>'''.encode()
        output = normalize_document_layout(source, paper_size="a4", margin_unit="cm",
            margins={side: 2.5 for side in ("top", "right", "bottom", "left")})
        root = ET.fromstring(output)
        paragraphs = root.findall("w:body/w:p", NS)
        for index, paragraph in enumerate(paragraphs):
            with self.subTest(paragraph=index):
                self.assertEqual(paragraph.find("w:pPr/w:keepNext", NS) is not None,
                                 index in {0, 5})
        second = normalize_document_layout(output, paper_size="a4", margin_unit="cm",
            margins={side: 2.5 for side in ("top", "right", "bottom", "left")})
        self.assertEqual(output, second)

    @unittest.skipUnless(shutil.which("pandoc"), "Pandoc required for DOCX round-trip fixture")
    def test_docx_round_trip_preserves_math_links_alt_and_custom_user_metadata(self) -> None:
        from prepare_markdown_sources import FigureBlock, build_figure_blocks
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fixture.docx"
            image = SCRIPTS_DIR.parent / "testbed/manuscript/figures/fig1_dummy.png"
            description = "A synthetic curve used to test accessible image descriptions."
            figure = FigureBlock(raw=f"![{description}]({image}){{#fig-one width=60%}}",
                figure_id="fig-one", title=description, src=str(image), attrs="#fig-one width=60%")
            markdown = "# Heading\n\nEquation $x^2 + y^2$ and [a link](https://example.org).\n\n| Identifier | Value |\n|---|---|\n| main_70 | -0.1 |\n\n"
            markdown += build_figure_blocks([figure], "top", "captions_page")
            subprocess.run(["pandoc", "-f", "markdown", "-o", str(path)], input=markdown,
                           text=True, check=True, capture_output=True)
            with zipfile.ZipFile(path) as z:
                payloads = {name: z.read(name) for name in z.namelist()}
            before = ET.fromstring(payloads["word/document.xml"])
            payloads["docProps/custom.xml"] = b'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="2" name="bibliography"><vt:lpwstr>/private/server/refs.yaml</vt:lpwstr></property><property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="3" name="Project"><vt:lpwstr>Retain this user metadata</vt:lpwstr></property></Properties>'
            with zipfile.ZipFile(path, "w") as z:
                for name, payload in payloads.items():
                    z.writestr(name, payload)
            for _ in range(2):
                rewrite_docx(path, "000000", "1.5", "continuous",
                    margins={side: 2.5 for side in ("top", "right", "bottom", "left")})
            with zipfile.ZipFile(path) as z:
                document_xml = z.read("word/document.xml")
                document = ET.fromstring(document_xml)
                self.assertNotIn(b"ns0:", document_xml)
                self.assertEqual(list(before.itertext()), list(document.itertext()))
                props = ET.fromstring(z.read("docProps/custom.xml"))
                self.assertEqual([prop.get("name") for prop in props], ["Project"])
                self.assertNotIn(b"/private/server", z.read("docProps/custom.xml"))
                self.assertEqual(document.find(".//w:pgSz", NS).get(f"{{{W_NS}}}w"), "11906")
                self.assertEqual(document.find(".//w:pgMar", NS).get(f"{{{W_NS}}}left"), "1417")
                section_names = [node.tag.rsplit("}", 1)[-1] for node in document.find(".//w:sectPr", NS)]
                self.assertLess(section_names.index("pgSz"), section_names.index("pgMar"))
                self.assertLess(section_names.index("pgMar"), section_names.index("lnNumType"))
                descriptions = [item.get("descr") for item in document.iter() if item.tag.endswith("}docPr")]
                self.assertEqual(descriptions, [description])
                text = "".join(node.text or "" for node in document.findall(".//w:t", NS))
                self.assertEqual(text.count(description), 1)  # Only the caption-list entry is visible.
                footer = ET.fromstring(z.read("word/makedoc-page-footer.xml"))
                self.assertEqual(footer.find(".//w:fldSimple", NS).get(f"{{{W_NS}}}instr"), " PAGE ")
                rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
                footer_rels = [rel for rel in rels if rel.get("Target") == "makedoc-page-footer.xml"]
                self.assertEqual(len(footer_rels), 1)
                self.assertTrue(any(rel.get("Target") == "https://example.org" for rel in rels))
            result = subprocess.run(["pandoc", str(path), "-t", "markdown"], check=True,
                                    capture_output=True, text=True)
            self.assertIn("x", result.stdout)
            self.assertIn("https://example.org", result.stdout)
            self.assertIn("main_70", result.stdout)
            rewrite_docx(path, "000000", "single", "none", page_numbers="none")
            with zipfile.ZipFile(path) as z:
                document = ET.fromstring(z.read("word/document.xml"))
                self.assertIsNone(document.find(".//w:footerReference", NS))
                self.assertIsNone(document.find(".//w:lnNumType", NS))


if __name__ == "__main__":
    unittest.main()
