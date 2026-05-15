# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import locale
import os

from azulero import _version

try:
    locale.setlocale(locale.LC_TIME, "en_US.utf8")
except locale.Error as e:
    print(f"Error: {e}")


project = _version.__title__
copyright = _version.__copyright__
author = _version.__author__[0]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.githubpages",
    "sphinx_prompt",
    "sphinx_copybutton",
    "sphinxcontrib.plantuml",
    "sphinxcontrib.mermaid",
    "sphinx_multiversion",
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


# Multiversion

smv_tag_whitelist = r"^v\d+\.\d+\.\d+$"  # FIXME >= 2.0.0
smv_branch_whitelist = r"^develop$"
smv_remote_whitelist = r"^origin$"
smv_released_pattern = r"^refs/tags/.*$"

templates_path = [
    "_templates",
]

html_sidebars = {
    "**": [
        "searchfield.html",
        "navigation.html",
        "relations.html",
        "versioning.html",
        "localtoc.html",
        "homelink.html",
    ]
}

# PlantUml

if "PLANTUML_JAR" in os.environ:
    plantuml = f"java -jar {os.environ.get('PLANTUML_JAR')}"
plantuml_output_format = "svg"
