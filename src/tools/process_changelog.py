"""把 changelog.txt 处理成 paratranz 能识别的 json 格式"""
import json
from pathlib import Path


VERSION: str | None = None
CHANGELOG_TXT: list | None = None


def changelog2paratranz():
    global VERSION, CHANGELOG_TXT
    with open(Path(__file__).parent.parent.parent / "degrees-of-lewdity-master" / "DoL Changelog.txt", "r", encoding="utf-8") as fp:
        lines = fp.readlines()

    current_version = lines[0].strip()  # 0.4.3.0
    current_version_main = ".".join(current_version.split(".")[:-1])  # 0.4.3
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if line[0].isnumeric() and line[-1].isnumeric():
            if ".".join(line.split(".")[:-1]) != current_version_main:
                lines = lines[:idx]
                break

    result = [
        {
            "key": line.strip(),
            "original": line.strip(),
            "translation": ""
        } for line in lines if line.strip()
    ]
    with open(Path(__file__).parent.parent.parent / "data" / "json" / f"{current_version}.json", "w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=2)
    VERSION = current_version
    CHANGELOG_TXT = lines


def paratranz2changelog():
    global VERSION, CHANGELOG_TXT
    if not (Path(__file__).parent / f"{VERSION}.json.json").exists():
        return
    with open(Path(__file__).parent / f"{VERSION}.json.json", "r", encoding="utf-8") as fp:
        data = json.load(fp)

    data = [
        (item["original"], item["translation"])
        for item in data
    ]
    for en, cn in data:
        for idx_changelog, line in enumerate(CHANGELOG_TXT):
            line = line.strip()
            print(line)
            if line == en:
                print(line)
                CHANGELOG_TXT[idx_changelog] = f"{cn}\n"
                continue
    with open(Path(__file__).parent / f"{VERSION}.txt", "w", encoding="utf-8") as fp:
        fp.writelines(CHANGELOG_TXT)


if __name__ == "__main__":
    changelog2paratranz()
    paratranz2changelog()