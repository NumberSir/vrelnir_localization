"""
如:
<<set VAR ...>>
<<if VAR ...>>
<<run VAR ...>>
"""
import json
import os
from enum import Enum
from pathlib import Path
from src.consts import *

class Patterns(Enum):
    SPACE: str = " "
    RETURN: str = "\n"

    VAR_HEAD = "$_"
    ALPHA_NUMS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    NUMBERS: str = "0123456789"
    VAR_NAME_BODY: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"


def fetch():
    results = {}
    for root, dir_list, file_list in os.walk(DIR_GAME_TEXTS_COMMON):
        for file in file_list:
            if file.endswith(SUFFIX_TWEE):
                with open(Path(root).absolute() / file, "r", encoding="utf-8") as fp:
                    raw = fp.read()
                variables = tokenize(raw)
                if not variables:
                    continue
                results[str(Path(root) / file).split("game\\")[1]] = list(set(variables))
            else:
                continue

    with open("variables.json", "w", encoding="utf-8") as fp:
        json.dump(results, fp, ensure_ascii=False, indent=2)


def tokenize(raw: str) -> list[str]:
    idx = 0
    variables = []
    is_var_flag = False
    tmp = ""

    while idx < len(raw):
        current_char = raw[idx]

        if current_char == Patterns.SPACE.value or current_char == Patterns.RETURN.value:
            idx += 1
            if is_var_flag:
                is_var_flag = False
                if tmp in variables:
                    tmp = ""
                    continue
                variables.append(tmp)
                tmp = ""
        elif current_char in Patterns.VAR_HEAD.value and not is_var_flag:
            if raw[idx-1] in Patterns.ALPHA_NUMS.value:
                idx += 1
                continue
            is_var_flag = True
            tmp += current_char
            idx += 1
        elif is_var_flag:
            if current_char not in Patterns.VAR_NAME_BODY.value:
                is_var_flag = False
                idx += 1
                if tmp in variables:
                    tmp = ""
                    continue
                variables.append(tmp)
                tmp = ""
                continue
            tmp += current_char
            idx += 1
        else:
            idx += 1
            continue

    return variables

def main():
    fetch()


if __name__ == '__main__':
    main()