from pathlib import Path
from enum import Enum
from dotenv import load_dotenv

import os
import platform
import sys

load_dotenv()
"""当前系统"""
PLATFORM_SYSTEM = platform.system()
PLATFORM_ARCHITECTURE = platform.architecture()[0]
SYSTEM_ARGV = sys.argv
GITHUB_ACTION_DEV = len(SYSTEM_ARGV) > 1 and SYSTEM_ARGV[1] == "-D"
GITHUB_ACTION_ISBETA = len(SYSTEM_ARGV) > 2 and SYSTEM_ARGV[2] == "beta"

"""汉化仓库"""
PARATRANZ_TOKEN = os.getenv("PARATRANZ_TOKEN") or ""  # 必填，在个人设置里
PARATRANZ_BASE_URL = "https://paratranz.cn/api"
PARATRANZ_HEADERS = {"Authorization": PARATRANZ_TOKEN}
PARATRANZ_PROJECT_DOL_ID = 4780  # DOL 项目 ID
CHINESE_VERSION = os.getenv("CHINESE_VERSION") or ""  # 必填，参考 README
SOURCE_TYPE = os.getenv("SOURCE_TYPE") or "common"  # 必填，common 或 dev

"""Modloader"""
REPOSITORY_MODLOADER_ARTIFACTS = "https://api.github.com/repos/Lyoko-Jeremie/DoLModLoaderBuild/actions/artifacts"
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN") or ""

"""源代码仓库"""
REPOSITORY_URL_COMMON = "https://gitgud.io/Vrelnir/degrees-of-lewdity"
REPOSITORY_ZIP_URL_COMMON = "https://gitgud.io/Vrelnir/degrees-of-lewdity/-/archive/master/degrees-of-lewdity-master.zip"
REPOSITORY_COMMITS_URL_COMMON = "https://gitgud.io/api/v4/projects/8430/repository/commits"
REPOSITORY_URL_DEV = "https://gitgud.io/Vrelnir/degrees-of-lewdity"
REPOSITORY_ZIP_URL_DEV = "https://gitgud.io/Vrelnir/degrees-of-lewdity/-/archive/dev/degrees-of-lewdity-dev.zip"

"""本地目录"""
DIR_ROOT = Path(__file__).parent.parent
DIR_DATA_ROOT = DIR_ROOT / "data"
DIR_JSON_ROOT = DIR_DATA_ROOT / "json"
DIR_TEMP_ROOT = DIR_DATA_ROOT / "temp"
DIR_MODS_ROOT = DIR_DATA_ROOT / "mods"

DIR_GAME_ROOT_COMMON_NAME = "degrees-of-lewdity-master"
DIR_GAME_ROOT_COMMON = DIR_ROOT / DIR_GAME_ROOT_COMMON_NAME
DIR_GAME_TEXTS_COMMON = DIR_GAME_ROOT_COMMON / "game"
DIR_GAME_CSS_COMMON = DIR_GAME_ROOT_COMMON / "modules" / "css"
DIR_GAME_ANDROID_ROOT_COMMON = DIR_GAME_ROOT_COMMON / "devTools" / "androidsdk" / "image" / "cordova"

DIR_GAME_ROOT_DEV_NAME = "degrees-of-lewdity-dev"
DIR_GAME_ROOT_DEV = DIR_ROOT / DIR_GAME_ROOT_DEV_NAME
DIR_GAME_TEXTS_DEV = DIR_GAME_ROOT_DEV / "game"
DIR_GAME_CSS_DEV = DIR_GAME_ROOT_DEV / "modules" / "css"
DIR_GAME_ANDROID_ROOT_DEV = DIR_GAME_ROOT_DEV / "devTools" / "androidsdk" / "image" / "cordova"

DIR_RAW_DICTS = DIR_DATA_ROOT / "raw_dicts"

DIR_PARATRANZ = DIR_DATA_ROOT / "paratranz"

"""文件"""
FILE_REPOSITORY_ZIP = DIR_TEMP_ROOT / "dol.zip"
FILE_PARATRANZ_ZIP = DIR_TEMP_ROOT / "paratranz_export.zip"
FILE_COMMITS = DIR_JSON_ROOT / "commits.json"
FILE_MODS = DIR_JSON_ROOT / "mod.json"
FILE_VERSION_EDIT_COMMON = DIR_GAME_TEXTS_COMMON / "01-config" / "sugarcubeConfig.js"

SUFFIX_TWEE = ".twee"
SUFFIX_JS = ".js"


class DirNamesTwee(Enum):
	"""特殊的目录名"""

	FRAMEWORK = "00-framework-tools"
	CONFIG = "01-config"
	JAVASCRIPT = "03-JavaScript"
	VARIABLES = "04-Variables"
	BASE_CLOTHING = "base-clothing"
	BASE_COMBAT = "base-combat"
	BASE_DEBUG = "base-debug"
	BASE_HAIR = "base-hair"
	BASE_SYSTEM = "base-system"
	FLAVOUR_TEXT_GENERATORS = "flavour-text-generators"

	OVERWORLD = "overworld-"

	LOCATION = "loc-"
	SPECIAL = "special-"
	NORMAL = OVERWORLD or LOCATION or SPECIAL


class FileNamesTwee(Enum):
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
	PREGNANCY_VAR_FULL = "pregnancyVar.twee"
	VARIABLES_STATIC_FULL = "variables-static.twee"

	""" base-clothing """
	CAPTIONTEXT_FULL = "captiontext.twee"
	CLOTHING = "clothing-"  # 没有FULL代表文件名中包含这个文本
	CLOTHING_SETS_FULL = "clothing-sets.twee"
	CLOTHING_IMAGES_FULL = "images.twee"
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
	COMBAT_IMAGES_FULL = "images.twee"

	""" base-hair """
	HAIR_STYLES_FULL = "hair-styles.twee"

	""" base-system """
	CHARACTERISTICS_FULL = "characteristics.twee"
	SOCIAL_FULL = "social.twee"
	TRAITS_FULL = "traits.twee"
	BODYWRITING_FULL = "bodywriting.twee"
	BODYWRITING_OBJECTS_FULL = "bodywriting-objects.twee"
	CAPTION_FULL = "caption.twee"
	DEVIANCY_FULL = "deviancy.twee"
	SYSTEM_EXHIBITIONISM_FULL = "exhibitionism.twee"
	FAME_FULL = "fame.twee"
	FEATS_FULL = "feats.twee"
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
	PERSISTENT_NPCS_FULL = "persistent-npcs.twee"
	JOURNAL_FULL = "journal.twee"

	""" flavour-text-generators """
	BODY_COMMENTS_FULL = "body-comments.twee"
	EXHIBITIONISM_FULL = "exhibitionism.twee"
	EZ_THESAURUS_FULL = "ez-thesaurus.twee"


class DirNamesJS(Enum):
	"""要抓的 JS 目录"""

	CONFIG = "01-config"
	SETUP = "01-setup"
	HELPERS = "02-Helpers"
	JAVASCRIPT = "03-JavaScript"
	VARIABLES = "04-Variables"
	SPECIAL_MASTURBATION = "special-masturbation"
	PREGNANCY = "04-Pregnancy"
	TIME = "time"
	TEMPLATES = "03-Templates"
	EXTERNAL = "external"
	BASE_SYSTEM = "base-system"
	BASE_CLOTHING = "base-clothing"
	MAIN = "01-main"
	RENDERER = "05-renderer"
	LOC_FORESTSHOP = "loc-forestshop"


class FileNamesJS(Enum):
	"""要抓的 JS 文件"""
	"""01-config"""
	SUGARCUBE_CONFIG_FULL = "sugarcubeConfig.js"

	"""01-setup"""
	WEATHER_DESCRIPTION_FULL = "weather-descriptions.js"

	"""02-Helpers"""
	MACROS_FULL = "macros.js"

	""" 03-JavaScript """
	BASE_FULL = "base.js"
	BEDROOM_PILLS_FULL = "bedroom-pills.js"
	DEBUG_MENU_FULL = "debug-menu.js"
	EYES_RELATED = "eyes-related.js"
	FURNITURE_FULL = "furniture.js"
	INGAME_FULL = "ingame.js"
	SEXSHOP_MENU_FULL = "sexShopMenu.js"
	SEXTOY_INVENTORY_FULL = "sexToysInventory.js"
	UI_FULL = "ui.js"
	NPC_COMPRESSOR_FULL = "npc-compressor.js"
	COLOUR_NAMER_FULL = "colour-namer.js"
	CLOTHING_SHOP_V2_FULL = "clothing-shop-v2.js"
	TIME_FULL = "time.js"
	TIME_MACROS_FULL = "time-macros.js"
	SAVE_FULL = "save.js"

	""" 04-variables """
	COLOURS_FULL = "colours.js"
	FEATS_FULL = "feats.js"
	SHOP_FULL = "shop.js"
	PLANT_SETUP_FULL = "plant-setup.js"

	""" special-masturbation """
	ACTIONS_FULL = "actions.js"
	EFFECTS_FULL = "effects.js"
	MACROS_MASTURBATION_FULL = "macros-masturbation.js"

	""" 04-Pregnancy """
	CHILDREN_STORY_FUNCTIONS_FULL = "children-story-functions.js"
	PREGNANCY_FULL = "pregnancy.js"
	STORY_FUNCTIONS_FULL = "story-functions.js"
	PREGNANCY_TYPES_FULL = "pregnancy-types.js"

	""" 03-Templates """
	T_MISC_FULL = "t-misc.js"
	T_ACTIONS_FULL = "t-actions.js"
	T_BODYPARTS_FULL = "t-bodyparts.js"

	""" external """
	COLOR_NAMER_FULL = "color-namer.js"

	""" base-system """
	EFFECT_FULL = "effect.js"
	TEXT_FULL = "text.js"
	WIDGETS_FULL = "widgets.js"
	STAT_CHANGES_FULL = "stat-changes.js"
	QUESTMARKERS_FULL = "questmarkers.js"

	""" base-clothing """
	UDPATE_CLOTHES_FULL = "update-clothes.js"
	CLOTHING = "clothing-"

	""" 01-main """
	TOOLTIPS = "02-tooltips.js"

	""" 05-renderer """
	CANVASMODEL_EDITOR_FULL = "30-canvasmodel-editor.js"

	""" loc-forestshop """
	SHOP_HUNT_FUNCTIONS_FULL = "shop-hunt-functions.js"


__all__ = [
	"SYSTEM_ARGV",
	"GITHUB_ACTION_DEV",
	"GITHUB_ACTION_ISBETA",
	"PLATFORM_SYSTEM",
	"PLATFORM_ARCHITECTURE",
	"PARATRANZ_BASE_URL",
	"PARATRANZ_HEADERS",
	"PARATRANZ_TOKEN",
	"PARATRANZ_PROJECT_DOL_ID",
	"CHINESE_VERSION",
	"SOURCE_TYPE",
	"REPOSITORY_URL_COMMON",
	"REPOSITORY_ZIP_URL_COMMON",
	"REPOSITORY_COMMITS_URL_COMMON",
	"REPOSITORY_URL_DEV",
	"REPOSITORY_ZIP_URL_DEV",
	"DIR_ROOT",
	"DIR_DATA_ROOT",
	"DIR_JSON_ROOT",
	"DIR_TEMP_ROOT",
	"DIR_MODS_ROOT",
	"DIR_GAME_ROOT_COMMON_NAME",
	"DIR_GAME_ROOT_COMMON",
	"DIR_GAME_TEXTS_COMMON",
	"DIR_GAME_CSS_COMMON",
	"DIR_GAME_ANDROID_ROOT_COMMON",
	"DIR_GAME_ROOT_DEV_NAME",
	"DIR_GAME_ROOT_DEV",
	"DIR_GAME_TEXTS_DEV",
	"DIR_GAME_CSS_DEV",
	"DIR_GAME_ANDROID_ROOT_DEV",
	"DIR_RAW_DICTS",
	"DIR_PARATRANZ",
	"FILE_REPOSITORY_ZIP",
	"FILE_PARATRANZ_ZIP",
	"FILE_COMMITS",
	"FILE_MODS",
	"FILE_VERSION_EDIT_COMMON",
	"SUFFIX_TWEE",
	"SUFFIX_JS",
	"DirNamesTwee",
	"FileNamesTwee",
	"DirNamesJS",
	"FileNamesJS",

	"REPOSITORY_MODLOADER_ARTIFACTS",
	"GITHUB_ACCESS_TOKEN"
]
