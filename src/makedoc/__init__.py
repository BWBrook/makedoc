"""Build journal-ready PDF and DOCX manuscripts from Markdown sources."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("makedoc")
except PackageNotFoundError:  # running from a source tree without installation
    __version__ = "0+unknown"
