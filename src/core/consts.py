from pathlib import Path
from enum import Enum


"""汉化仓库"""
PARATRANZ_TOKEN = "84f5b1350b9d607d00312111a5afdfc9"  # 必填，在个人设置里
PARATRANZ_BASE_URL = "https://paratranz.cn/api"
PARATRANZ_HEADERS = {"Authorization": PARATRANZ_TOKEN}
PARATRANZ_PROJECT_ID = 4780  # DOL 项目 ID

"""源代码仓库"""
REPOSITORY_URL_COMMON = "https://gitgud.io/Vrelnir/degrees-of-lewdity"
REPOSITORY_ZIP_URL_COMMON = "https://gitgud.io/Vrelnir/degrees-of-lewdity/-/archive/master/degrees-of-lewdity-master.zip"
REPOSITORY_URL_DEV = "https://gitgud.io/Vrelnir/degrees-of-lewdity"
REPOSITORY_ZIP_URL_DEV = "https://gitgud.io/Vrelnir/degrees-of-lewdity/-/archive/dev/degrees-of-lewdity-dev.zip"

"""本地目录"""
DIR_ROOT = Path(__file__).parent.parent.parent
DIR_DATA_ROOT = DIR_ROOT / "data"
DIR_TEMP_ROOT = DIR_ROOT / "temp"

DIR_GAME_ROOT_COMMON_NAME = "degrees-of-lewdity-master"
DIR_GAME_ROOT_COMMON = DIR_ROOT / DIR_GAME_ROOT_COMMON_NAME
# DIR_GAME_ROOT_COMMON = Path("D:\Joy\Butter").absolute() / "degrees-of-lewdity-master"
DIR_GAME_TEXTS_COMMON = DIR_GAME_ROOT_COMMON / "game"

DIR_GAME_ROOT_DEV_NAME = "degrees-of-lewdity-dev"
DIR_GAME_ROOT_DEV = DIR_ROOT / DIR_GAME_ROOT_DEV_NAME
DIR_GAME_TEXTS_DEV = DIR_GAME_ROOT_DEV / "game"

DIR_RAW_DICTS = DIR_ROOT / "raw_dicts"
DIR_FINE_DICTS = DIR_ROOT / "fine_dicts"

DIR_PARATRANZ = DIR_ROOT / "paratranz"

"""文件"""
FILE_REPOSITORY_ZIP = DIR_TEMP_ROOT / "dol.zip"
FILE_PARATRANZ_ZIP = DIR_TEMP_ROOT / "paratranz_export.zip"

SUFFIX_TWEE = ".twee"
SUFFIX_JS = ".js"


class DirNames(Enum):
    """特殊的目录名"""
    FRAMEWORK = "00-framework-tools"
    CONFIG = "01-config"
    JAVASCRIPT = "03-JavaScript"
    VARIABLES = "04-Variables"
    BASE_CLOTHING = "base-clothing"
    BASE_COMBAT = "base-combat"
    BASE_DEBUG = "base-debug"
    BASE_SYSTEM = "base-system"

    OVERWORLD = "overworld-"
    LOCATION = "loc-"
    SPECIAL = "special-"
    NORMAL = OVERWORLD or LOCATION or SPECIAL


class FileNames(Enum):
    """特殊的文件名"""
    """ 00-framework-tools """
    WAITING_ROOM_FULL = "waiting-room.twee"  # FULL 代表这就是文件名

    """ 01-config """
    START_FULL = "start.twee"
    VERSION_INFO_FULL = "versionInfo.twee"

    """ 04-Variables """
    CANVASMODEL_FULL = "canvasmodel-example.twee"
    PASSAGE_FOOTER_FULL = "variables-passageFooter.twee"
    VERSION_UPDATE_FULL = "variables-versionUpdate.twee"

    """ base-clothing """
    CAPTIONTEXT_FULL = "captiontext.twee"
    CLOTHING = "clothing-"  # 没有FULL代表文件名中包含这个文本
    CLOTHING_SETS_FULL = "clothing-sets.twee"
    IMAGES_FULL = "images.twee"
    INIT_FULL = "init.twee"
    WARDROBES_FULL = "wardrobes.twee"

    """ base-combat """
    ACTIONS_FULL = "actions.twee"
    ACTIONS = "actions"
    STALK_FULL = "stalk.twee"
    GENERATION = "generation.twee"
    TENTACLE_ADV_FULL = "tentacle-adv.twee"
    TENTACLES_FULL = "tentacles.twee"
    COMBAT_EFFECTS_FULL = "effects.twee"
    NPC_DAMAGE_FULL = "npc-damage.twee"
    NPC_GENERATION_FULL = "npc-generation.twee"
    SPEECH_SYDNEY_FULL = "speech-sydney.twee"
    SPEECH_FULL = "speech.twee"
    STRUGGLE_FULL = "struggle.twee"
    SWARMS_FULL = "swarms.twee"
    SWARM_EFFECTS_FULL = "swarm-effects.twee"
    COMBAT_WIDGETS_FULL = "widgets.twee"

    """ base-system """
    CHARACTERISTICS_FULL = "characteristics.twee"
    SOCIAL_FULL = "social.twee"
    TRAITS_FULL = "traits.twee"
    BODYWRITING_FULL = "bodywriting.twee"
    BODYWRITING_OBJECTS_FULL = "bodywriting-objects.twee"
    CAPTION_FULL = "caption.twee"
    DEVIANCY_FULL = "deviancy.twee"
    EXHIBITIONISM_FULL = "exhibitionism.twee"
    MOBILE_STATS_FULL = "mobileStats.twee"
    NAME_LIST_FULL = "name-list.twee"
    NAMED_NPCS_FULL = "named-npcs.twee"
    NICKNAMES_FULL = "nicknames.twee"
    PLANT_OBJECTS_FULL = "plant-objects.twee"
    PROMISCUITY_FULL = "promiscuity.twee"
    RADIO_FULL = "radio.twee"
    SETTINGS_FULL = "settings.twee"
    SKILL_DIFFICULTIES_FULL = "skill-difficulties.twee"
    SLEEP_FULL = "sleep.twee"
    STAT_CHANGES_FULL = "stat-changes.twee"
    TENDING_FULL = "tending.twee"
    TEXT_FULL = "text.twee"
    TIME_FULL = "time.twee"
    TIPS_FULL = "tips.twee"
    TRANSFORMATIONS_FULL = "transformations.twee"
    SYSTEM_WIDGETS_FULL = "widgets.twee"


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
    "DIR_TEMP_ROOT",
    "DIR_GAME_ROOT_COMMON_NAME",
    "DIR_GAME_ROOT_COMMON",
    "DIR_GAME_TEXTS_COMMON",
    "DIR_GAME_ROOT_DEV_NAME",
    "DIR_GAME_ROOT_DEV",
    "DIR_GAME_TEXTS_DEV",
    "DIR_RAW_DICTS",
    "DIR_FINE_DICTS",
    "DIR_PARATRANZ",

    "FILE_REPOSITORY_ZIP",
    "FILE_PARATRANZ_ZIP",

    "SUFFIX_TWEE",
    "SUFFIX_JS",

    "DirNames",
    "FileNames"
]
