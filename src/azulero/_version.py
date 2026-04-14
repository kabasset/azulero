from importlib.metadata import metadata

pkg_metadata = metadata("azulero")

_split_every_other_comma = lambda text: [
    l + ", " + r for l, r in zip(*[iter(text.split(", "))] * 2)
]

__name_soft__ = pkg_metadata.get("name", "unknown")
__version__ = pkg_metadata.get("version", "0.0.0")
__title__ = pkg_metadata.get("name", "unknown")
__description__ = pkg_metadata.get("summary", "")
__url__ = pkg_metadata.get("project-url", "").split(", ")[-1]
__author__ = _split_every_other_comma(pkg_metadata.get("author", ""))
__author_email__ = pkg_metadata.get("author-email", "unknown")
__license__ = pkg_metadata.get("license-expression", "unknown")
__copyright__ = "2025-2026, Antoine Basset (CNES) and contributors"
