from __future__ import annotations

import sys
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


if __name__ == "__main__":
    unittest.main()
