"""把 changelog.txt 处理成 paratranz 能识别的 json 格式"""
import json
import os
from pathlib import Path

from src.consts import DIR_PARATRANZ


VERSION: str | None = None
CHANGELOG_TXT: list | None = None
os.makedirs("data", exist_ok=True)

def changelog2paratranz(version: str = None):
    global VERSION, CHANGELOG_TXT
     
    with open(Path(__file__).parent.parent.parent.parent / "degrees-of-lewdity-master" / "DoL Changelog.txt", "r", encoding="utf-8") as fp:
        lines = fp.readlines()

    current_version = version or lines[0].strip().strip(":")  # 0.4.3.0
    current_version_main = ".".join(current_version.split(".")[:-1])  # 0.4.3
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if line[0].isnumeric() and line.strip(":")[-1].isnumeric() and ".".join(line.split(".")[:-1]) != current_version_main:
            lines = lines[:idx]
            break

    result = [
        {
            "key": line.strip(),
            "original": line.strip(),
            "translation": ""
        } for line in lines if line.strip()
    ]
    with open(Path(__file__).parent / "data" / f"{current_version}.json", "w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=2)
    VERSION = current_version
    CHANGELOG_TXT = lines


def paratranz2changelog(version: str = None):
    global VERSION, CHANGELOG_TXT
    if version is None:
        version = VERSION

    downloaded_raw_dir = DIR_PARATRANZ / "common" / "raw" / "更新日志" / f"{version}.json.json"
    if not downloaded_raw_dir.exists():
        return
    with open(downloaded_raw_dir, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    data = [
        (item["original"], item["translation"])
        for item in data
    ]
    for en, cn in data:
        for idx_changelog, line in enumerate(CHANGELOG_TXT):
            line = line.strip()
            if line == en:
                CHANGELOG_TXT[idx_changelog] = f"{cn}\n"
                continue
    with open(Path(__file__).parent / "data" / f"{version}.txt", "w", encoding="utf-8") as fp:
        fp.writelines(CHANGELOG_TXT)


if __name__ == "__main__":
    changelog2paratranz()
    paratranz2changelog()
