import git
import os

from azulero import _version

# General configuration
# =====================


extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.githubpages",  # Add .nojekyll file
    "sphinxcontrib.images",
    "sphinxcontrib.plantuml",
    "sphinxcontrib.video",
    "sphinx_changelog",
    "sphinx_new_tab_link",
]
source_suffix = {".rst": "restructuredtext"}
templates_path = ["_templates"]
master_doc = "index"
exclude_patterns = []


# Context
# =======


def list_releases(other_versions: dict[str, str] = {}):
    """
    List tags which start with 'v' and append versions passed as arguments.

    If the distant repository is not available, the local repository is used.
    """

    repo = git.Repo(".", search_parent_directories=True)
    try:
        tags = repo.git.ls_remote("--tags", "origin")
    except git.GitCommandError as e:
        print(f"Error: {e}")
        print(f"Finding versions in local repository.")
        tags = repo.git.show_ref("--tags")
    releases = [
        line.split("refs/tags/v")[-1]
        for line in tags.split("\n")
        if "refs/tags/v" in line and "^{}" not in line
    ]

    old_version_url = "https://github.com/kabasset/azulero/blob/{version}/README.md"
    new_version_url = "https://kabasset.github.io/azulero/{version}/index.html"

    releases.sort(key=lambda v: [int(d) for d in v.split(".")], reverse=True)
    url = lambda v: (
        old_version_url if v.startswith("v1.") else new_version_url
    ).format(version=v)
    releases = {str(v): url(f"v{v}") for v in releases}
    others = {v: url(other_versions[v]) for v in other_versions}
    return {**releases, **others}


html_context = {
    "repository": "https://github.com/kabasset/azulero",
    "versions": list_releases({"Development version": "develop"}),
    "social": "https://mastodon.social/@kabasset/tagged/Azulero",
}

project = _version.__title__
version = _version.__version__
license = _version.__license__
copyright = _version.__copyright__ + "."
author = _version.__author__[0]

rst_prolog = f"""
.. |project| replace:: {project}
.. |version| replace:: {version}
.. |copyright| replace:: {copyright}
.. |author| replace:: {author}
.. |license| replace:: {license}

.. _repository: {html_context['repository']}
.. _SPDX: https://spdx.org/licenses/{license}.html
.. _gallery: {html_context['social']}
.. _Azulite: https://kabasset.github.io/azulite/index.html
.. _eummy: https://github.com/schirmermischa/eummy
.. _euniverse: https://github.com/schirmermischa/euniverse
"""


# Style
# =====


# Theme
# -----

html_theme = "sphinxawesome_theme"

html_theme_path = ["_themes"]
html_static_path = ["_static"]
templates_path = ["_templates"]
html_css_files = [
    "code.css",
    "figures.css",
    "lists.css",
]

html_title = _version.__title__ + " " + _version.__version__
html_favicon = "_static/favicon.png"

html_use_index = False
html_permalinks = False
html_copy_source = False
html_show_sourcelink = False
html_show_copyright = True
html_last_updated_fmt = ""

html_sidebars = {
    "**": [
        "sidebar_main_nav_links.html",
        "sidebar_toc.html",
    ]
}


# Code blocks
# -----------

# pygments_style is not taken into account when pygments_style_dark is specified; sphinxawesome bug?
# Anyway, since we mostly rely on command lines, with very few highlighting,
# and there are many "false positives" (e.g. whole part of floats is highlighted),
# we prefer relying on manual highlighting of the words.

# pygments_style = "algol"
# pygments_style_dark = "monokai"


# Links
# -----


awesome_external_links = True


# PlantUML
# ========


if "PLANTUML_JAR" in os.environ:
    plantuml = f"java -jar {os.environ.get('PLANTUML_JAR')}"
else:
    plantuml = "plantuml"
plantuml += " -darkmode"
plantuml_output_format = "svg"


# Header
# ======

html_theme_options = {
    "show_prev_next": True,
    "awesome_external_links": False,
    "show_breadcrumbs": False,
    "logo_light": html_favicon,
    "logo_dark": html_favicon,
    "main_nav_links": {
        "Versions": "https://kabasset.github.io/azulero/versions/index.html",
        "New issue": "https://github.com/kabasset/azulero/issues/new",
        # TODO add gallery
    },
    "extra_header_link_icons": {
        "repository on GitHub": {
            "link": html_context["repository"],
            "icon": (
                '<svg width="16px" height="16px" viewBox="16 16 96 96" fill="none" xmlns="http://www.w3.org/2000/svg">'
                '<path d="M56.7937 84.9688C44.4187 83.4688 35.7 74.5625 35.7 63.0313C35.7 58.3438 37.3875 53.2813 40.2 49.9063C38.9812 46.8125 39.1687 40.25 40.575 37.5313C44.325 37.0625 49.3875 39.0313 52.3875 41.75C55.95 40.625 59.7 40.0625 64.2937 40.0625C68.8875 40.0625 72.6375 40.625 76.0125 41.6563C78.9187 39.0313 84.075 37.0625 87.825 37.5313C89.1375 40.0625 89.325 46.625 88.1062 49.8125C91.1062 53.375 92.7 58.1563 92.7 63.0313C92.7 74.5625 83.9812 83.2813 71.4187 84.875C74.6062 86.9375 76.7625 91.4375 76.7625 96.5938L76.7625 106.344C76.7625 109.156 79.1062 110.75 81.9187 109.625C98.8875 103.156 112.2 86.1875 112.2 65.1875C112.2 38.6563 90.6375 17 64.1062 17C37.575 17 16.2 38.6562 16.2 65.1875C16.2 86 29.4187 103.25 47.2312 109.719C49.7625 110.656 52.2 108.969 52.2 106.438L52.2 98.9375C50.8875 99.5 49.2 99.875 47.7 99.875C41.5125 99.875 37.8562 96.5 35.2312 90.2188C34.2 87.6875 33.075 86.1875 30.9187 85.9063C29.7937 85.8125 29.4187 85.3438 29.4187 84.7813C29.4187 83.6563 31.2937 82.8125 33.1687 82.8125C35.8875 82.8125 38.2312 84.5 40.6687 87.9688C42.5437 90.6875 44.5125 91.9063 46.8562 91.9063C49.2 91.9063 50.7 91.0625 52.8562 88.9063C54.45 87.3125 55.6687 85.9063 56.7937 84.9688Z" fill="currentColor"/>'
                "</svg>"
            ),
        },
        "gallery on Mastodon": {
            "link": html_context["social"],
            "icon": (
                '<svg width="16px" height="16px" viewBox="0 0 74 79" fill="currentColor" xmlns="http://www.w3.org/2000/svg">'
                '<path d="M73.7014 17.9592C72.5616 9.62034 65.1774 3.04876 56.424 1.77536C54.9472 1.56019 49.3517 0.7771 36.3901 0.7771H36.2933C23.3281 0.7771 20.5465 1.56019 19.0697 1.77536C10.56 3.01348 2.78877 8.91838 0.903306 17.356C-0.00357857 21.5113 -0.100361 26.1181 0.068112 30.3439C0.308275 36.404 0.354874 42.4535 0.91406 48.489C1.30064 52.498 1.97502 56.4751 2.93215 60.3905C4.72441 67.6217 11.9795 73.6395 19.0876 76.0945C26.6979 78.6548 34.8821 79.0799 42.724 77.3221C43.5866 77.1245 44.4398 76.8953 45.2833 76.6342C47.1867 76.0381 49.4199 75.3714 51.0616 74.2003C51.0841 74.1839 51.1026 74.1627 51.1156 74.1382C51.1286 74.1138 51.1359 74.0868 51.1368 74.0592V68.2108C51.1364 68.185 51.1302 68.1596 51.1185 68.1365C51.1069 68.1134 51.0902 68.0932 51.0695 68.0773C51.0489 68.0614 51.0249 68.0503 50.9994 68.0447C50.9738 68.0391 50.9473 68.0392 50.9218 68.045C45.8976 69.226 40.7491 69.818 35.5836 69.8087C26.694 69.8087 24.3031 65.6569 23.6184 63.9285C23.0681 62.4347 22.7186 60.8764 22.5789 59.2934C22.5775 59.2669 22.5825 59.2403 22.5934 59.216C22.6043 59.1916 22.621 59.1702 22.6419 59.1533C22.6629 59.1365 22.6876 59.1248 22.714 59.1191C22.7404 59.1134 22.7678 59.1139 22.794 59.1206C27.7345 60.2936 32.799 60.8856 37.8813 60.8843C39.1036 60.8843 40.3223 60.8843 41.5447 60.8526C46.6562 60.7115 52.0437 60.454 57.0728 59.4874C57.1983 59.4628 57.3237 59.4416 57.4313 59.4098C65.3638 57.9107 72.9128 53.2051 73.6799 41.2895C73.7086 40.8204 73.7803 36.3758 73.7803 35.889C73.7839 34.2347 74.3216 24.1533 73.7014 17.9592ZM61.4925 47.6918H53.1514V27.5855C53.1514 23.3526 51.3591 21.1938 47.7136 21.1938C43.7061 21.1938 41.6988 23.7476 41.6988 28.7919V39.7974H33.4078V28.7919C33.4078 23.7476 31.3969 21.1938 27.3894 21.1938C23.7654 21.1938 21.9552 23.3526 21.9516 27.5855V47.6918H13.6176V26.9752C13.6176 22.7423 14.7157 19.3795 16.9118 16.8868C19.1772 14.4 22.1488 13.1231 25.8373 13.1231C30.1064 13.1231 33.3325 14.7386 35.4832 17.9662L37.5587 21.3949L39.6377 17.9662C41.7884 14.7386 45.0145 13.1231 49.2765 13.1231C52.9614 13.1231 55.9329 14.4 58.2055 16.8868C60.4017 19.3772 61.4997 22.74 61.4997 26.9752L61.4925 47.6918Z" fill="inherit"/>'
                "</svg>"
            ),
        },
    },
}

# Autodoc
# =======

maximum_signature_line_length = 1
autodoc_preserve_defaults = True
autodoc_member_order = "bysource"
