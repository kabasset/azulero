import git
import os

from azulero import _version

# General configuration
# =====================


extensions = [
    "sphinx.ext.githubpages",
    "sphinx_prompt",
    "sphinxcontrib.plantuml",
    "sphinx_subfigure",
    "sphinxcontrib.video",
    "sphinx_changelog",
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

    repo = git.Repo("../..")
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
}

project = _version.__title__
version = _version.__version__
license = _version.__license__
copyright = _version.__copyright__
author = _version.__author__[0]

rst_prolog = f"""
.. _SPDX: https://spdx.org/licenses/{license}.html
.. |project| replace:: {project}
.. |version| replace:: {version}
.. |copyright| replace:: {copyright}
.. |author| replace:: {author}
.. |license| replace:: {license}

"""


# Style
# =====


# Theme
# -----

html_theme = "sphinxawesome_theme"

html_theme_path = ["_themes"]
html_static_path = ["_static"]
templates_path = ["_templates"]

html_logo = "_static/logo.png"  # FIXME same as favicon with this theme
html_title = _version.__title__ + " v" + _version.__version__
# html_favicon = "favicon.png"
# html_css_files = ["custom.css"]

html_use_index = False
html_permalinks = False
html_copy_source = False
html_show_sourcelink = False
html_show_copyright = True

html_sidebars = {
    "**": [
        "sidebar_main_nav_links.html",
        "sidebar_toc.html",
        "versions.html",
    ]
}


# Code blocks
# -----------


pygments_style = "github-dark"
pygments_style_dark = "github-dark"


# Links
# -----


awesome_external_links = True


# PlantUML
# ========


if "PLANTUML_JAR" in os.environ:
    plantuml = f"java -jar {os.environ.get('PLANTUML_JAR')}"
plantuml_output_format = "svg"
