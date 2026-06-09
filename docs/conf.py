import datetime
from pathlib import Path

import aiogram

project = "aiogram"
author = "aiogram Team"
copyright = f"{datetime.date.today().year}, {author}"
release = aiogram.__version__
api_version = aiogram.__api_version__

templates_path = ["_templates"]
html_theme = "furo"
html_logo = "_static/logo.png"
html_static_path = ["_static"]
todo_include_todos = True
pygments_style = "sphinx"
htmlhelp_basename = project
html_theme_options = {}
html_css_files = [
    "stylesheets/extra.css",
]
highlight_language = "python3"

extensions = [
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.autodoc",
    "sphinx.ext.ifconfig",
    "sphinx.ext.intersphinx",
    "sphinx_substitution_extensions",
    "sphinx_copybutton",
    # "sphinxcontrib.towncrier.ext",  # Temporary disabled due to bug in the extension https://github.com/sphinx-contrib/sphinxcontrib-towncrier/issues/92
]

rst_prolog = f"""
.. |api_version| replace:: {aiogram.__api_version__}

.. role:: pycode(code)
   :language: python3
"""

# language = None
locale_dirs = ["locale/"]
gettext_compact = False

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

# add_module_names = False

towncrier_draft_autoversion_mode = "draft"
towncrier_draft_include_empty = False
towncrier_draft_working_directory = Path(__file__).parent.parent


def skip_model_prefixed_members(app, what, name, obj, skip, options):
    # Skip any member whose name starts with "model_"
    if name.startswith("model_"):
        return True
    return skip


def setup(app):
    app.connect("autodoc-skip-member", skip_model_prefixed_members)
