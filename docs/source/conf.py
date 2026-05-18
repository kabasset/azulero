# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import git
import locale
import os

from azulero import _version

try:
    locale.setlocale(locale.LC_TIME, "en_US.utf8")
except locale.Error as e:
    print(f"Error: {e}")


def list_releases(other_versions: dict[str, str] = {}):

    repo = git.Repo("../..")
    try:
        tags = repo.git.ls_remote("--tags", "origin")
    except git.GitCommandError as e:
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


html_context = {"versions": list_releases({"Development version": "develop"})}

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

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.githubpages",
    "sphinx_prompt",
    "sphinx_copybutton",
    "sphinxcontrib.plantuml",
    "sphinxcontrib.mermaid",
    "sphinx_subfigure",
    "sphinxcontrib.video",
    "sphinxarg.ext",
    "sphinx_changelog",
]
source_suffix = {".rst": "restructuredtext"}
templates_path = ["_templates"]
master_doc = "index"
exclude_patterns = []
pygments_style = "sphinx"
copybutton_exclude = ".linenos, .gp"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

html_theme_path = ["_themes"]
html_logo = "_static/logo.png"
html_title = _version.__title__ + " v" + _version.__version__
# html_favicon = "favicon.png"
html_css_files = ["custom.css"]

html_use_index = False
html_permalinks = False
html_copy_source = False
html_show_sourcelink = False
html_show_copyright = True

html_theme_options = {
    # 'fixed_sidebar': True,  # Cannot search if window is too small
    "show_relbars": True,
}

templates_path = [
    "_templates",
]

html_sidebars = {
    "**": [
        "searchfield.html",
        "navigation.html",
        "relations.html",
        "localtoc.html",
        "versions.html",
    ]
}

# PlantUml

if "PLANTUML_JAR" in os.environ:
    plantuml = f"java -jar {os.environ.get('PLANTUML_JAR')}"
plantuml_output_format = "svg"
