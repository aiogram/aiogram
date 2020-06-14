import datetime

import aiogram

project = "aiogram"
author = "aiogram Team"
copyright = f"{datetime.date.today().year}, {author}"
release = aiogram.__version__
api_version = aiogram.__api_version__

templates_path = ["_templates"]
html_theme = "sphinx_rtd_theme"
html_icon = "_static/logo.png"
html_static_path = ["_static"]
todo_include_todos = True
# pygments_style = "sphinx"
htmlhelp_basename = project
html_theme_options = {
    'collapse_navigation': False,
}

extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.autodoc",
    "sphinx.ext.ifconfig",
    "sphinx-prompt",
    "sphinx_substitution_extensions",
]

rst_prolog = f"""
.. |api_version| replace:: {aiogram.__api_version__}
"""

language = None
locale_dirs = ["locales"]

exclude_patterns = []
source_suffix = ".rst"
master_doc = "index"

latex_documents = [
    (master_doc, f"{project}.tex", f"{project} Documentation", author, "manual"),
]
man_pages = [(master_doc, project, f"{project} Documentation", [author], 1)]
texinfo_documents = [
    (
        master_doc,
        project,
        f"{project} Documentation",
        author,
        project,
        "Modern and fully asynchronous framework for Telegram Bot API",
        "Miscellaneous",
    ),
]

autodoc_default_options = {
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
}
