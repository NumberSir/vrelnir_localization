from pathlib import Path


REPOSITORY_URL = "https://gitgud.io/Vrelnir/degrees-of-lewdity"
REPOSITORY_ZIP_URL = "https://gitgud.io/Vrelnir/degrees-of-lewdity/-/archive/master/degrees-of-lewdity-master.zip"

"""本地目录"""
DIR_ROOT = Path(__file__).parent
DIR_DATA_ROOT = DIR_ROOT / "data"
DIR_GAME_ROOT = DIR_ROOT / "degrees-of-lewdity-master"
DIR_GAME_TEXTS = DIR_GAME_ROOT / "game"
DIR_RAW_DICTS = DIR_ROOT / "raw_dicts"

FILE_REPOSITORY_ZIP = DIR_ROOT / "dol.zip"

SUFFIX_TEXTS = ".twee"


__all__ = [
    "REPOSITORY_URL",
    "REPOSITORY_ZIP_URL",

    "DIR_ROOT",
    "DIR_DATA_ROOT",
    "DIR_GAME_ROOT",
    "DIR_GAME_TEXTS",
    "DIR_RAW_DICTS",

    "FILE_REPOSITORY_ZIP",

    "SUFFIX_TEXTS"
]
