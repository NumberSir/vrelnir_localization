import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
ACCESS_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN')

ROOT = Path(__file__).parent
DIR_TEMP = ROOT / "tmp"
DIR_BUILD = ROOT / "build"
DIR_BUILD_ASSETS = DIR_BUILD / "assets"
DIR_CREDITS = ROOT / "credits"
DIR_APK_BUILD_TOOLS = ROOT / "apk-build-tools"

DIR_GAME = ROOT.parent.parent.parent / "degrees-of-lewdity-master"
DIR_APK_BUILDER = DIR_GAME / "devTools" / "apkbuilder"
DIR_DIST = DIR_GAME / "dist"
DIR_REPO = Path("F:\\Users\\numbersir\\Documents\\GitHub\\Degrees-of-Lewdity-Chinese-Localization")

FILE_LICENSE = DIR_GAME / "LICENSE"
FILE_CREDITS = DIR_CREDITS / "CREDITS.md"
FILE_README = DIR_REPO / "README.md"

FILE_GRADLE = DIR_APK_BUILD_TOOLS / "gradle" / "gradle.zip"
FILE_CMDLINE = DIR_APK_BUILD_TOOLS / "cmdline-tools" / "latest.zip"

HTML_FILENAME = "Degrees of Lewdity.html"
APK_DEFAULT_FILENAME_PREFIX = "Degrees-of-Lewdity"

CORDOVA_ANDROID_KEYSTORE_PASSWORD = os.getenv("CORDOVA_ANDROID_KEYSTORE_PASSWORD")
CORDOVA_ANDROID_KEYSTORE_FILENAME = os.getenv("CORDOVA_ANDROID_KEYSTORE_FILENAME") or "dol-chs.keystore"
CORDOVA_ANDROID_KEYSTORE_ALIAS = os.getenv("CORDOVA_ANDROID_KEYSTORE_ALIAS") or "dol-chs"


__all__ = [
    "ACCESS_TOKEN",

    "ROOT",
    "DIR_TEMP",
    "DIR_BUILD",
    "DIR_BUILD_ASSETS",
    "DIR_CREDITS",
    "DIR_APK_BUILD_TOOLS",

    "DIR_GAME",
    "DIR_APK_BUILDER",
    "DIR_DIST",
    "DIR_REPO",

    "FILE_LICENSE",
    "FILE_CREDITS",
    "FILE_README",

    "FILE_GRADLE",
    "FILE_CMDLINE",

    "HTML_FILENAME",
    "APK_DEFAULT_FILENAME_PREFIX",

	"CORDOVA_ANDROID_KEYSTORE_PASSWORD",
	"CORDOVA_ANDROID_KEYSTORE_FILENAME",
	"CORDOVA_ANDROID_KEYSTORE_ALIAS",
]