from pathlib import Path


"""汉化仓库"""
PARATRANZ_TOKEN = ""  # 要手动填，在设置里找
PARATRANZ_BASE_URL = "https://paratranz.cn/api"
PARATRANZ_HEADERS = {"Authorization": PARATRANZ_TOKEN}
PARATRANZ_PROJECT_ID = 4780  # DOL 项目 ID

"""源代码仓库"""
REPOSITORY_URL_COMMON = "https://gitgud.io/Vrelnir/degrees-of-lewdity"
REPOSITORY_ZIP_URL_COMMON = "https://gitgud.io/Vrelnir/degrees-of-lewdity/-/archive/master/degrees-of-lewdity-master.zip"
REPOSITORY_URL_DEV = "https://gitgud.io/Vrelnir/degrees-of-lewdity"
REPOSITORY_ZIP_URL_DEV = "https://gitgud.io/Vrelnir/degrees-of-lewdity/-/archive/dev/degrees-of-lewdity-dev.zip"

"""本地目录"""
DIR_ROOT = Path(__file__).parent
DIR_DATA_ROOT = DIR_ROOT / "data"

DIR_GAME_ROOT_COMMON = DIR_ROOT / "degrees-of-lewdity-master"
DIR_GAME_TEXTS_COMMON = DIR_GAME_ROOT_COMMON / "game"
DIR_GAME_ROOT_DEV = DIR_ROOT / "degrees-of-lewdity-dev"
DIR_GAME_TEXTS_DEV = DIR_GAME_ROOT_DEV / "game"

DIR_RAW_DICTS = DIR_ROOT / "raw_dicts"
DIR_FINE_DICTS = DIR_ROOT / "fine_dicts"

DIR_PARATRANZ = DIR_ROOT / "paratranz"

"""文件"""
FILE_REPOSITORY_ZIP = DIR_ROOT / "dol.zip"
FILE_PARATRANZ_ZIP = DIR_ROOT / "汉化包.zip"

SUFFIX_TEXTS = ".twee"


__all__ = [
    "PARATRANZ_BASE_URL",
    "PARATRANZ_HEADERS",
    "PARATRANZ_TOKEN",
    "PARATRANZ_PROJECT_ID",

    "REPOSITORY_URL_COMMON",
    "REPOSITORY_ZIP_URL_COMMON",
    "REPOSITORY_URL_DEV",
    "REPOSITORY_ZIP_URL_DEV",

    "DIR_ROOT",
    "DIR_DATA_ROOT",
    "DIR_GAME_ROOT_COMMON",
    "DIR_GAME_TEXTS_COMMON",
    "DIR_GAME_ROOT_DEV",
    "DIR_GAME_TEXTS_DEV",
    "DIR_RAW_DICTS",
    "DIR_FINE_DICTS",
    "DIR_PARATRANZ",

    "FILE_REPOSITORY_ZIP",
    "FILE_PARATRANZ_ZIP",

    "SUFFIX_TEXTS"
]
