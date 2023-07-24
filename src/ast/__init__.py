from .acorn import *
import re
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
from re import Pattern
from typing import Union, Any
from enum import Enum
from loguru import logger


class Patterns(Enum):
    SPACE: str = " "
    RETURN: str = "\n"
    NUMBERS: str = "0123456789"

    STORY_START: str = ":"  # :: STORY

    VAR_NAME_HEAD: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    VAR_NAME_BODY: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"

    WIDGET_START: str = "<"
    TAG_START: str = "<"
    TAG_SLASH: str = "/"

    WIDGET_END: str = ">"
    TAG_END: str = ">"


@dataclass
class Token:
    type: str
    value: Any

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return fr"({self.type}) || {self.value}"


class Tokenizer:
    """词法分析器"""
    def __init__(self, raw_code: Union[str, bytes]):
        self._raw_code = raw_code

        self._tokens: list = []

    def tokenize(self):
        """str->tokens"""
        index: int = 0
        while index < self._raw_code.__len__():
            current_char = self._raw_code[index]

            # 空格
            if current_char == Patterns.SPACE.value:
                index += 1
            # 换行
            elif current_char == Patterns.RETURN.value:
                index += 1
            # 数字
            elif current_char in Patterns.NUMBERS.value:
                value = ""
                while current_char in Patterns.NUMBERS.value:
                    value += current_char
                    index += 1
                    current_char = self._raw_code[index]
                self._tokens.append(Token(type="number", value=value))
            # 故事(:: Story)
            elif current_char == Patterns.STORY_START.value:
                if (index == 0 or self._raw_code[index-1] == Patterns.RETURN.value) and self._raw_code[index+1] == Patterns.STORY_START.value:
                    value = ""
                    if self._raw_code[index+2] == Patterns.SPACE.value:
                        index += 3
                        current_char = self._raw_code[index]
                    while current_char != Patterns.RETURN.value:
                        value += current_char
                        index += 1
                        current_char = self._raw_code[index]
                    self._tokens.append(Token(type="story", value=value))
            elif current_char == Patterns.TAG_START.value:
                # 1. <tag>
                if self._raw_code[index+1] == Patterns.VAR_NAME_HEAD.value:
                    value = ""
                    index += 1
                    current_char = self._raw_code[index]
                    while current_char != Patterns.TAG_END.value:
                        value += current_char
                        index += 1
                        current_char =self._raw_code[index]
                    self._tokens.append(Token(type="tag", value=value))
                # 2. </tag>
                elif self._raw_code[index+1] == Patterns.TAG_SLASH.value:
                    value = ""
                    index += 2
                    current_char = self._raw_code[index]
                    while current_char not in {Patterns.TAG_END.value, Patterns.SPACE.value}:
                        value += current_char
                        index += 1
                        current_char =self._raw_code[index]
                    self._tokens.append(Token(type="tag_close", value=value))
                # 3. <<widget>>
                elif self._raw_code[index+1] == Patterns.WIDGET_START.value:
                    value = ""
                    type_ = "widget"
                    index += 2
                    current_char = self._raw_code[index]
                    # 4. <</widget>>
                    if current_char == Patterns.TAG_SLASH.value:
                        type_ = "widget_close"
                        index += 1
                        current_char = self._raw_code[index]
                    while current_char not in {Patterns.TAG_END.value, Patterns.SPACE.value}:
                        value += current_char
                        index += 1
                        current_char =self._raw_code[index]
                    self._tokens.append(Token(type=type_, value=value))
                # 3. 小于号
                # 4. <-!--
                else:
                    index += 1
                    continue
            else:
                index += 1
                continue
        return self._tokens


class Parser:
    """语法分析器"""


class Traverserer:
    """遍历器"""


def parse(raw: str):
    return Tokenizer(raw).tokenize()


if __name__ == '__main__':
    with open(Path(r"D:\GitHub\vrelnir_localization\degrees-of-lewdity-master\game\00-framework-tools\02-version\waiting-room.twee"), "r", encoding="utf-8") as fp:
        code = fp.read()
    result = parse(code)
    pprint(result)
