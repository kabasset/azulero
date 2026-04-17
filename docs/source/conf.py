# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import locale

locale.setlocale(locale.LC_TIME, "en_US.utf8")

from azulero import _version

project = _version.__title__
copyright = _version.__copyright__
author = _version.__author__[0]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.githubpages",
    "sphinx_prompt",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
]
source_suffix = ".rst"
templates_path = ["_templates"]
master_doc = "index"
exclude_patterns = []
pygments_style = "sphinx"

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
