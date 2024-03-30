import re

from pathlib import Path

"""REGEX"""
PTN_COMMENT = re.compile(r"""(/\*|<!--)[\s\S]*?(\*/|-->)""")
PTN_HEAD = re.compile(r"""::[\s\S]*?\n""")
PTN_MACRO = re.compile(r"""<</?([\w=\-]+)(?:\s+((?:(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)|(?://.*\n)|(?:`(?:\\.|[^`\\\n])*?`)|(?:"(?:\\.|[^"\\\n])*?")|(?:'(?:\\.|[^'\\\n])*?')|(?:\[(?:[<>]?[Ii][Mm][Gg])?\[[^\r\n]*?]]+)|[^>]|(?:>(?!>)))*?))?>>""")
PTN_TAG = re.compile(r"""(?<!<)<(?![<!])/?(\w+)\s*[\s\S]*?(?<!>)>(?!>)""")

"""STRING"""
GAME_TEXTS_NAME = "degrees-of-lewdity-master"

"""NUMBER"""
GENERAL_LIMIT = 1000

"""PATH"""
ROOT = Path(__file__).parent.parent.parent
DIR_GAME = ROOT / GAME_TEXTS_NAME
DIR_GAME_TEXTS = DIR_GAME / "game"
DIR_TEST = ROOT / "src" / "parse_texts"
DIR_PASSAGE = DIR_TEST / "passage"
DIR_TARGET = DIR_TEST / "target"


__all__ = [
    "PTN_COMMENT",
    "PTN_HEAD",
    "PTN_MACRO",
    "PTN_TAG",

    "GAME_TEXTS_NAME",

    "GENERAL_LIMIT",

    "ROOT",
    "DIR_GAME",
    "DIR_GAME_TEXTS",
    "DIR_PASSAGE",
    "DIR_TARGET",
    "DIR_TEST"
]
