import re
from pathlib import Path
from typing import Callable


class ParseText:
    def __init__(self, filepath: Path, debug_flag: bool = False):
        self._filepath = filepath
        self._filename = filepath.name
        self._dirparent = filepath.parent

        self._debug_flag = debug_flag

    def parse(self) -> list[bool]:
        """ 返回哪些要提取，哪些不要 """
        raise NotImplementedError

    """ 以下是几种频率高的判断函数 """
    @staticmethod
    def is_comment(line: str) -> bool:
        """全行注释"""
        return any(_ for _ in {
            line == "<!--",
            line == "-->",
            line == "/*",
            line == "*/",

            line.startswith("<!--") and "-->" not in line,
            line.endswith("-->") and "<!--" not in line,
            line.startswith("*"),
            line.startswith("/*") and "*/" not in line,
            line.endswith("*/") and "/*" not in line,
        })

    @staticmethod
    def is_only_marks(line: str) -> bool:
        """只有符号没字母数字"""
        return not any(re.findall(r"([A-Za-z\d]+)", line))

    @staticmethod
    def is_event(line: str) -> bool:
        """事件"""
        return "::" in line

    @staticmethod
    def is_tag_span(line: str) -> bool:
        """只要有 <span"""
        return "<span " in line

    @staticmethod
    def is_tag_label(line: str) -> bool:
        """只要有 <label>"""
        return "<label>" in line

    @staticmethod
    def is_tag_input(line: str) -> bool:
        """只要有 <input """
        return "<input " in line

    @staticmethod
    def is_widget_script(line: str) -> bool:
        """只要有 <<script """
        return "<<script " in line

    @staticmethod
    def is_widget_note(line: str) -> bool:
        """只要有 <<note """
        return "<<note " in line

    @staticmethod
    def is_widget_print(line: str) -> bool:
        """只要有 <<print """
        return "<<print " in line

    @staticmethod
    def is_widget_if(line: str) -> bool:
        """只要有 <<if """
        return "<<if " in line

    @staticmethod
    def is_widget_option(line: str) -> bool:
        """只要有 <<option """
        return "<<option " in line

    @staticmethod
    def is_widget_button(line: str) -> bool:
        """只要有 <<button """
        return "<<button " in line

    @staticmethod
    def is_widget_link(line: str) -> bool:
        """这位更是重量级 <<link """
        return any(re.findall(r"<<link\s*(\[\[|\"\w|`\w|\'\w|\"\(|`\(|\'\(|_\w|`)", line))

    @staticmethod
    def is_widget_set_to(line: str, keys: set[str]) -> bool:
        """这位更是重量级 <<set """
        pattern = re.compile("<<set (?:" + r"|".join(keys) + ")[\'\"\w\s\[\]\$\+\.\(\)\{\}:\-]*(?:to|\+|\+=|\().*?[\w\{\"\'`]+(?:\w| \w|<<|\"\w)")
        return any(re.findall(pattern, line))

    """以下是几种常用的简化提取"""
    def parse_type_only(self, pattern: str | set[str]) -> list[bool]:
        """指文件中只有一种或几种简单字符格式需要提取"""
        with open(self._filepath, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

        if isinstance(pattern, str):
            return [
                line.strip() and
                pattern in line.strip()
                for line in lines
            ]

        return [
            line.strip() and
            any((_ in line.strip() for _ in pattern))
            for line in lines
        ]


class ParseTextTwee(ParseText):
    ...


class ParseTextJS(ParseText):
    ...


class ParseTextCSS(ParseText):
    ...
