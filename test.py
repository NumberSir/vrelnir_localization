import asyncio
from pathlib import Path
from src.parse_text import ParseTextTwee, ParseTextJS

FILE_BASE = r"D:\Users\Administrator\Documents\GitHub\vrelnir_localization\degrees-of-lewdity-master\game"
FILE_NAME = r"base-system/bodywriting.twee"
FILE_PATH = Path(rf"{FILE_BASE}/{FILE_NAME}")
with open(FILE_PATH, "r", encoding="utf-8") as fp:
    CONTENT = fp.read()
with open(FILE_PATH, "r", encoding="utf-8") as fp:
    LINES = fp.readlines()
PT = ParseTextTwee(lines=LINES, filepath=FILE_PATH) if FILE_PATH.name.endswith("twee") else ParseTextJS(lines=LINES, filepath=FILE_PATH)


async def test_fetch_lines():
    # sourcery skip: no-conditionals-in-tests
    # sourcery skip: no-loop-in-tests
    """抓了哪些行"""
    bl = PT.parse()
    pre_bool_list = PT.pre_parse_set_to(True)
    bl = [
        True if pre_bool_list[idx] or line else False
        for idx, line in enumerate(bl)
    ]
    print(f"bool: {len(bl)} - lines: {len(LINES)} - pre: {len(pre_bool_list)}")
    for idx, line in enumerate(LINES):
        if bl[idx]:
            print(f"{idx + 1}: {line}", end="")


async def test_fetch_pos():
    # sourcery skip: no-conditionals-in-tests
    # sourcery skip: no-loop-in-tests
    """抓的位置对不对"""
    able_lines = PT.parse()
    pre_bool_list = PT.pre_parse_set_to()
    able_lines = [
        True if pre_bool_list[idx] or line else False
        for idx, line in enumerate(able_lines)
    ]
    passage_name = None
    pos_relative = None
    pos_global = 0
    for idx, line in enumerate(LINES):
        if line.startswith("::"):
            pos_relative = 0
            tmp_ = line.lstrip(":: ")
            if "[" not in line:
                passage_name = tmp_.strip()
            else:
                for idx_, char in enumerate(tmp_):
                    if char != "[":
                        continue
                    passage_name = tmp_[:idx_ - 1].strip()
                    break
                else:
                    raise

        if able_lines[idx]:
            pos_start = 0
            if line != line.lstrip():  # 前面的 \t \s 也要算上
                for char in line:
                    if char == line.strip()[0]:
                        break
                    pos_start += 1
            print(f"passage: {passage_name}")
            print(f"line: {line}".replace("\t", "\\t").replace("\n", "\\n"))
            print(f"pos: {pos_relative + pos_start if pos_relative is not None else pos_global + pos_start}")
            print(f"global: {pos_global + pos_start}: {len(CONTENT)} | {CONTENT[pos_global + pos_start]}\n")
        if pos_relative is not None and not line.startswith("::"):
            pos_relative += len(line)
        pos_global += len(line)


if __name__ == '__main__':
    asyncio.run(test_fetch_lines())
