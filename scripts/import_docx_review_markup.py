#!/usr/bin/env python3
"""Experimental DOCX-to-Markdown review-markup import spike.

This is not a production importer. It provides narrow evidence routes:

1. Compare original plain text with revised DOCX text and emit simple
   Makedoc review-markup tokens from a normalized word diff.
2. Read tiny DOCX OOXML containing native Word ``w:ins``/``w:del`` elements and
   emit insertion/deletion review-markup tokens in document order.
3. Write a separate revised-DOCX candidate Markdown file for simple prose
   paragraphs only.
4. Preflight original Markdown/plain-prose sources and report whether
   candidate generation is safe to attempt.

The prototype intentionally ignores layout, styles, tables, figures, comments,
citations, field codes, moves, and Markdown structure. It uses only Python
stdlib ZIP/XML parsing so the feasibility evidence is dependency-light.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from difflib import SequenceMatcher
from pathlib import Path
from xml.etree import ElementTree


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
DOCUMENT_XML = "word/document.xml"
REVIEW_TOKEN_RE = re.compile(r"\{\+\+|\{--|\{~~|\{>>")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
TABLE_SEPARATOR_RE = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
FRONT_MATTER_OR_THEMATIC_BREAK_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
IMAGE_RE = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)")
HTML_BLOCK_RE = re.compile(r"^\s*</?[A-Za-z][^>]*>\s*$")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
BLOCKQUOTE_RE = re.compile(r"^\s{0,3}>")
BULLET_RE = re.compile(r"^\s{0,3}[-+*]\s+")
NUMBERED_RE = re.compile(r"^\s{0,3}\d+[.)]\s+")
PANDOC_CITATION_RE = re.compile(r"(?<![\w.-])@[-A-Za-z0-9_:.#/$%]+")


class CandidateGenerationError(ValueError):
    """Raised when candidate generation refuses unsafe input."""


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _read_document_xml(docx_path: Path) -> ElementTree.Element:
    with zipfile.ZipFile(docx_path) as archive:
        try:
            payload = archive.read(DOCUMENT_XML)
        except KeyError as exc:
            raise ValueError(f"DOCX is missing {DOCUMENT_XML}: {docx_path}") from exc
    return ElementTree.fromstring(payload)


def _paragraphs(root: ElementTree.Element) -> list[ElementTree.Element]:
    return list(root.findall(f".//{{{WORD_NS}}}p"))


def _collect_text(
    element: ElementTree.Element,
    *,
    include_deleted: bool = False,
    in_deleted: bool = False,
) -> str:
    local = _local_name(element.tag)
    if local == "del":
        in_deleted = True

    parts: list[str] = []
    if local == "t" and not in_deleted and element.text:
        parts.append(element.text)
    elif local == "delText" and include_deleted and element.text:
        parts.append(element.text)

    for child in list(element):
        parts.append(
            _collect_text(
                child,
                include_deleted=include_deleted,
                in_deleted=in_deleted,
            )
        )
    return "".join(parts)


def extract_revised_text_from_docx(docx_path: str | Path) -> str:
    """Extract simple accepted/revised paragraph text from a DOCX.

    Native deletion text is ignored. Insertion text is included because it is
    the visible revised text in Word's tracked-change view.
    """

    root = _read_document_xml(Path(docx_path))
    paragraphs = [
        _normalize_text(_collect_text(paragraph, include_deleted=False))
        for paragraph in _paragraphs(root)
    ]
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def diff_text_to_review_markup(original_text: str, revised_text: str) -> str:
    """Emit simple review-markup tokens from a normalized word diff."""

    original_words = _normalize_text(original_text).split()
    revised_words = _normalize_text(revised_text).split()
    matcher = SequenceMatcher(None, original_words, revised_words, autojunk=False)

    pieces: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old = " ".join(original_words[i1:i2])
        new = " ".join(revised_words[j1:j2])
        if tag == "equal":
            pieces.extend(revised_words[j1:j2])
        elif tag == "insert" and new:
            pieces.append(f"{{++ {new} ++}}")
        elif tag == "delete" and old:
            pieces.append(f"{{-- {old} --}}")
        elif tag == "replace":
            if old and new:
                pieces.append(f"{{~~ {old} ~> {new} ~~}}")
            elif old:
                pieces.append(f"{{-- {old} --}}")
            elif new:
                pieces.append(f"{{++ {new} ++}}")
    return " ".join(pieces).strip()


def revised_docx_to_review_markup(original_text: str, revised_docx: str | Path) -> str:
    revised_text = extract_revised_text_from_docx(revised_docx)
    return diff_text_to_review_markup(original_text, revised_text)


def _simple_paragraphs(text: str) -> list[str]:
    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized_newlines:
        return []
    return [
        _normalize_text(paragraph)
        for paragraph in re.split(r"\n[ \t]*\n", normalized_newlines)
        if _normalize_text(paragraph)
    ]


def _unsupported_markdown_line_reason(line: str) -> str | None:
    stripped = line.strip()
    if not stripped:
        return None
    if FENCE_RE.match(line):
        return "unsupported Markdown fenced code block"
    if line.startswith("    ") or line.startswith("\t"):
        return "unsupported Markdown indented code block"
    if FRONT_MATTER_OR_THEMATIC_BREAK_RE.match(line):
        return "unsupported Markdown front matter or thematic break"
    if IMAGE_RE.match(line):
        return "unsupported Markdown image or figure line"
    if TABLE_SEPARATOR_RE.match(line) or line.count("|") >= 2:
        return "unsupported Markdown table"
    if "<!--" in line:
        return "unsupported Markdown HTML comment"
    if HTML_BLOCK_RE.match(line):
        return "unsupported Markdown raw HTML block"
    if HEADING_RE.match(line):
        return "unsupported Markdown heading"
    if BLOCKQUOTE_RE.match(line):
        return "unsupported Markdown blockquote"
    if BULLET_RE.match(line):
        return "unsupported Markdown bullet list"
    if NUMBERED_RE.match(line):
        return "unsupported Markdown numbered list"
    if "[@" in line or "[-@" in line or PANDOC_CITATION_RE.search(line):
        return "unsupported Markdown Pandoc citation"
    if REVIEW_TOKEN_RE.search(line):
        return "unsupported existing review-markup token"
    return None


def _unsupported_markdown_reason(text: str) -> str | None:
    for line_number, line in enumerate(text.splitlines(), start=1):
        reason = _unsupported_markdown_line_reason(line)
        if reason:
            return f"line {line_number}: {reason}"
    return None


def _preflight_status(total_blocks: int, refused_blocks: int) -> str:
    if total_blocks == 0:
        return "NO_ELIGIBLE_BLOCKS"
    if refused_blocks:
        return "REFUSED"
    return "SAFE_TO_ATTEMPT"


def _markdown_blocks(text: str) -> list[dict[str, object]]:
    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks: list[dict[str, object]] = []
    block_lines: list[tuple[int, str]] = []
    start_line: int | None = None

    def flush() -> None:
        nonlocal block_lines, start_line
        if not block_lines or start_line is None:
            return
        blocks.append(
            {
                "index": len(blocks) + 1,
                "start_line": start_line,
                "end_line": block_lines[-1][0],
                "lines": block_lines,
            }
        )
        block_lines = []
        start_line = None

    for line_number, line in enumerate(normalized_newlines.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if start_line is None:
            start_line = line_number
        block_lines.append((line_number, line))
    flush()
    return blocks


def preflight_markdown_source(original_path: str | Path) -> dict[str, object]:
    """Report candidate-import eligibility for an original Markdown source."""

    original = Path(original_path).expanduser().resolve()
    text = original.read_text(encoding="utf-8")
    blocks = _markdown_blocks(text)

    refusals: list[dict[str, object]] = []
    for block in blocks:
        for line_number, line in block["lines"]:  # type: ignore[index]
            reason = _unsupported_markdown_line_reason(line)
            if reason:
                refusals.append(
                    {
                        "block": block["index"],
                        "start_line": block["start_line"],
                        "end_line": block["end_line"],
                        "line": line_number,
                        "reason": reason,
                    }
                )
                break

    total_blocks = len(blocks)
    refused_blocks = len(refusals)
    eligible_blocks = total_blocks - refused_blocks
    status = _preflight_status(total_blocks, refused_blocks)
    safe_to_attempt = status == "SAFE_TO_ATTEMPT"
    return {
        "status": status,
        "path": str(original),
        "total_blocks": total_blocks,
        "eligible_blocks": eligible_blocks,
        "refused_blocks": refused_blocks,
        "safe_to_attempt": safe_to_attempt,
        "refusals": refusals,
    }


def format_preflight_report(report: dict[str, object]) -> str:
    """Render a prose-free preflight report for operators."""

    status = str(report["status"])
    safe_to_attempt = bool(report["safe_to_attempt"])
    lines = [
        "DOCX revised-candidate preflight",
        f"Original path: {report['path']}",
        f"Overall status: {status}",
        f"Blocks considered: {report['total_blocks']}",
        f"Eligible simple-prose paragraphs: {report['eligible_blocks']}",
        f"Refused blocks: {report['refused_blocks']}",
        f"Safe to attempt revised-candidate: {'yes' if safe_to_attempt else 'no'}",
    ]

    refusals = report["refusals"]
    if refusals:
        lines.extend(["", "Refusals:"])
        for refusal in refusals:  # type: ignore[assignment]
            lines.append(
                "- block {block}, lines {start_line}-{end_line}, line {line}: "
                "{reason}".format(**refusal)
            )
    else:
        lines.extend(["", "Refusals: none"])

    return "\n".join(lines) + "\n"


def format_preflight_json(report: dict[str, object]) -> str:
    """Render a deterministic, prose-free preflight JSON report."""

    return json.dumps(report, indent=2) + "\n"


def generate_revised_candidate(
    original_path: str | Path,
    revised_docx: str | Path,
    output_path: str | Path,
    *,
    overwrite: bool = False,
) -> str:
    """Write a separate review-markup candidate for simple prose paragraphs."""

    original = Path(original_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    if original == output:
        raise CandidateGenerationError("output path resolves to the same path as original")
    if output.exists() and not overwrite:
        raise CandidateGenerationError(f"output already exists: {output}")

    original_text = original.read_text(encoding="utf-8")
    unsupported_reason = _unsupported_markdown_reason(original_text)
    if unsupported_reason:
        raise CandidateGenerationError(unsupported_reason)

    original_paragraphs = _simple_paragraphs(original_text)
    revised_text = extract_revised_text_from_docx(revised_docx)
    revised_paragraphs = _simple_paragraphs(revised_text)

    if len(original_paragraphs) != len(revised_paragraphs):
        raise CandidateGenerationError(
            "paragraph count mismatch: "
            f"original has {len(original_paragraphs)}, "
            f"revised DOCX has {len(revised_paragraphs)}"
        )

    candidate = "\n\n".join(
        diff_text_to_review_markup(original, revised)
        for original, revised in zip(original_paragraphs, revised_paragraphs)
    )
    if candidate:
        candidate += "\n"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(candidate, encoding="utf-8")
    return candidate


def _review_token(prefix: str, text: str, suffix: str) -> str:
    cleaned = _normalize_text(text)
    if not cleaned:
        return ""
    return f"{{{prefix} {cleaned} {suffix}}}"


def _element_to_track_change_markup(element: ElementTree.Element) -> str:
    local = _local_name(element.tag)
    if local == "ins":
        return _review_token("++", _collect_text(element, include_deleted=False), "++")
    if local == "del":
        return _review_token("--", _collect_text(element, include_deleted=True), "--")
    if local == "t" and element.text:
        return element.text
    if local == "delText":
        return ""

    return "".join(_element_to_track_change_markup(child) for child in list(element))


def track_changes_docx_to_review_markup(docx_path: str | Path) -> str:
    """Read simple ``w:ins``/``w:del`` text changes from DOCX OOXML."""

    root = _read_document_xml(Path(docx_path))
    paragraphs = [
        _normalize_text(_element_to_track_change_markup(paragraph))
        for paragraph in _paragraphs(root)
    ]
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def _load_original_text(args: argparse.Namespace) -> str:
    if args.original_text is not None:
        return args.original_text
    return Path(args.original_path).read_text(encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    revised = subparsers.add_parser(
        "revised",
        help="Diff original text against revised DOCX text.",
    )
    original_group = revised.add_mutually_exclusive_group(required=True)
    original_group.add_argument("--original-text", help="Original plain text.")
    original_group.add_argument(
        "--original-path",
        help="Path to original plain text or Markdown to compare as text.",
    )
    revised.add_argument("--revised-docx", required=True, help="Path to revised DOCX.")

    candidate = subparsers.add_parser(
        "revised-candidate",
        help="Write a separate candidate Markdown file for simple revised DOCX prose.",
    )
    candidate.add_argument(
        "--original-path",
        required=True,
        help="Path to original simple Markdown or plain prose.",
    )
    candidate.add_argument("--revised-docx", required=True, help="Path to revised DOCX.")
    candidate.add_argument("--output", required=True, help="Candidate Markdown output path.")
    candidate.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing candidate output file.",
    )

    preflight = subparsers.add_parser(
        "preflight",
        help="Report whether an original Markdown source is eligible for revised-candidate.",
    )
    preflight.add_argument(
        "--original-path",
        required=True,
        help="Path to original Markdown or plain prose to preflight.",
    )
    preflight.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Preflight report format.",
    )

    tracked = subparsers.add_parser(
        "track-changes",
        help="Read simple native Word w:ins/w:del elements from DOCX OOXML.",
    )
    tracked.add_argument("--docx", required=True, help="Path to DOCX.")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "revised":
        print(revised_docx_to_review_markup(_load_original_text(args), args.revised_docx))
        return 0
    if args.command == "revised-candidate":
        try:
            generate_revised_candidate(
                args.original_path,
                args.revised_docx,
                args.output,
                overwrite=args.overwrite,
            )
        except CandidateGenerationError as exc:
            print(f"revised-candidate refused: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "preflight":
        report = preflight_markdown_source(args.original_path)
        if args.format == "json":
            print(format_preflight_json(report), end="")
        else:
            print(format_preflight_report(report), end="")
        return 0
    if args.command == "track-changes":
        print(track_changes_docx_to_review_markup(args.docx))
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
