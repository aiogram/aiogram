import datetime
import pathlib

import black
import jinja2

from generator.parser import Parser

templates_dir: pathlib.Path = pathlib.Path(__file__).parent / "templates"


class Generator:
    def __init__(self, parser: Parser):
        self.parser = parser
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=[templates_dir]))

    @property
    def context(self):
        return {
            "groups": self.parser.groups,
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    def _render_template(self, template: str) -> str:
        template = self.env.get_template(template)
        content = template.render(self.context)
        return content

    def _reformat_code(self, code: str) -> str:
        return black.format_str(code, mode=black.FileMode())

    def render_types(self):
        content = self._render_template("types.py.jinja2")
        return self._reformat_code(content)
