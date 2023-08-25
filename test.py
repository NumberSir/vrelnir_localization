from pathlib import Path
from src.parse_text import ParseTextTwee, ParseTextJS

FILE_NAME = "04-Variables/variables-static.twee"


if __name__ == '__main__':
    file_base = r"E:\Documents\GitHub\vrelnir_localization\degrees-of-lewdity-master\game"
    path = Path(rf"{file_base}/{FILE_NAME}")
    with open(path, "r", encoding="utf-8") as fp:
        lines = fp.readlines()
    pt = ParseTextTwee(lines=lines, filepath=path) if path.name.endswith("twee") else ParseTextJS(lines=lines, filepath=path)
    bl = pt.parse()
    print(f"bool: {len(bl)} - lines: {len(lines)}")
    for idx, line in enumerate(lines):
        if bl[idx]:
            print(f"{idx+1}: {line}", end="")
