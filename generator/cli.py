import logging
import pathlib
import sys
import typing

from generator.generator import Generator
from generator.parser import Parser

script_path = pathlib.Path(__file__).parent
out_dir = script_path.parent / "aiogram" / "_telegram"


def main(argv: typing.List[str]) -> int:
    logging.basicConfig(level=logging.ERROR, stream=sys.stdout)
    parser = Parser()
    parser.parse()
    generator = Generator(parser)

    with (out_dir / "types.py").open("w") as f:
        f.write(generator.render_types())

    return 0
