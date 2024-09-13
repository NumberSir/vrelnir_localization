"""
运行前提：
1. 写好了 README
2. 写好了 CREDITS
3. 按照 degrees-of-lewdity-master/devTools/apkbuilder/README-windows.txt 配好了 nodejs 和 jdk17

运行步骤：
1. 触发 ModLoader 自动构建
2. 触发汉化包自动构建

3. 下载构建好的 ModLoader 包和图片包
4. 下载构建好的汉化包

5. 解压 ModLoader 包出两个 HTML 文件
6. 把 README, Credits, LICENSE 和 HTML 打成压缩包
7. 替换官方 APK 中的 HTML
8. 删除官方 APK 中的 img 文件夹
9. 计算 MD5
10. 提取出 README 中的本次更新部分
11. 构建 Release
"""
import asyncio
import hashlib
import os
import re
import shutil
import subprocess
import time
import zipfile
from pathlib import Path
from zipfile import ZipFile

import httpx

from dotenv import load_dotenv
from github import Github, Auth

from src.tools.build_release.download import *
from src.tools.build_release.log import *

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
DIR_REPO = Path("D:\\Users\\numbersir\\Documents\\GitHub\\Degrees-of-Lewdity-Chinese-Localization")

FILE_LICENSE = DIR_GAME / "LICENSE"
FILE_CREDITS = DIR_CREDITS / "CREDITS.md"
FILE_README = DIR_REPO / "README.md"

FILE_GRADLE = DIR_APK_BUILD_TOOLS / "gradle" / "gradle.zip"
FILE_CMDLINE = DIR_APK_BUILD_TOOLS / "cmdline-tools" / "latest.zip"

HTML_FILENAME = "Degrees of Lewdity.html"


class ReleaseBuild:
    def __init__(self, github: Github, client: httpx.AsyncClient):
        self._github = github
        self._client = client

    """ INIT """
    @staticmethod
    def clear():
        shutil.rmtree(DIR_TEMP, ignore_errors=True)
        shutil.rmtree(DIR_BUILD_ASSETS, ignore_errors=True)
        os.makedirs(DIR_TEMP, exist_ok=True)
        os.makedirs(DIR_BUILD_ASSETS, exist_ok=True)
        logger.info("> initialize successfully")

    """ ACTION """
    def _trigger(self):
        ...

    def trigger_mod_loader(self):
        ...

    def trigger_i18n(self):
        ...

    """ DOWNLOAD """
    async def _download(self, repo_name: str):
        repo = self.github.get_repo(repo_name)
        release = repo.get_latest_release()
        assets = release.get_assets()
        for asset in assets:
            response = await self.client.head(asset.browser_download_url, timeout=60, follow_redirects=True)
            filesize = int(response.headers["Content-Length"])
            chunks = await chunk_split(filesize, 64)

            if (DIR_TEMP / asset.name).exists():
                continue

            tasks = {
                chunk_download(asset.browser_download_url, self.client, start, end, DIR_TEMP / asset.name)
                for idx, (start, end) in enumerate(chunks)
            }
            await asyncio.gather(*tasks)

    async def download_mod_loader(self):
        await self._download("Lyoko-Jeremie/DoLModLoaderBuild")
        logger.info("> ModLoader & Imagepack downloaded successfully")

    async def download_i18n(self):
        await self._download("NumberSir/DoL-I18n-Build")
        logger.info("> ModI18N downloaded successfully")

    """ DECOMPRESS """
    def decompress_mod_loader(self):
        with zipfile.ZipFile(DIR_TEMP / self.mod_loader_filename, "r") as zfp:
            for file in zfp.filelist:
                if not file.filename.endswith(".html"):
                    continue
                zfp.extract(file, DIR_TEMP)

    """ BUILD ASSETS """
    def move_i18n(self):
        shutil.copyfile(
            DIR_TEMP / self.i18n_filename,
            DIR_BUILD_ASSETS / self.i18n_filename,
        )
        logger.info("> ModI18N built successfully")

    def rename_image_pack(self):
        (DIR_TEMP / self.image_pack_filename).rename(
            DIR_TEMP / f'{self.image_pack_filename.split("-")[0].split(".")[0]}-{self.game_version}.mod.zip')

    def move_image_pack(self):
        shutil.copyfile(
            DIR_TEMP / self.image_pack_filename,
            DIR_BUILD_ASSETS / self.image_pack_filename,
        )
        logger.info("> Imagepack built successfully")

    def _build_compress(self, html_filepath: Path, polyfill_suffix: str = ""):
        with ZipFile(DIR_BUILD_ASSETS / f"DoL-ModLoader-{self.game_version}-v{self.mod_loader_version}{polyfill_suffix}.zip", "w") as zfp:
            zfp.write(filename=FILE_README, arcname=FILE_README.name)
            zfp.write(filename=FILE_LICENSE, arcname=FILE_LICENSE.name)
            zfp.write(filename=FILE_CREDITS, arcname=FILE_CREDITS.name)
            zfp.write(filename=html_filepath, arcname=HTML_FILENAME)
        logger.info(f"> Zipfile{polyfill_suffix} built successfully")

    def build_compress_normal(self):
        return self._build_compress(DIR_TEMP / self.html_filename)

    def build_compress_polyfill(self):
        return self._build_compress(DIR_TEMP / self.html_polyfill_filename, "-polyfill")

    @staticmethod
    def _pre_build_apk():
        with ZipFile(FILE_GRADLE, "r") as zfp:
            zfp.extractall(DIR_APK_BUILDER / "androidsdk" / "gradle")

        with ZipFile(FILE_CMDLINE, "r") as zfp:
            zfp.extractall(DIR_APK_BUILDER / "androidsdk" / "cmdline-tools" / "latest")

        with open(DIR_APK_BUILDER / "setup_deps.bat", "r") as fp:
            content = fp.read()
        with open(DIR_APK_BUILDER / "setup_deps.bat", "w") as fp:
            fp.write(content.replace("pause", ""))

        with open(DIR_APK_BUILDER / "build_app_debug.bat", "r") as fp:
            content = fp.read()
        with open(DIR_APK_BUILDER / "build_app_debug.bat", "w") as fp:
            fp.write(content.replace("pause", ""))

    def _build_apk(self, html_filepath: Path, polyfill_suffix: str = ""):
        self._pre_build_apk()
        shutil.copyfile(
            html_filepath,
            DIR_GAME / HTML_FILENAME,
        )
        subprocess.Popen(DIR_APK_BUILDER / "setup_deps.bat", cwd=DIR_APK_BUILDER).wait()
        subprocess.Popen(DIR_APK_BUILDER / "build_app_debug.bat", cwd=DIR_APK_BUILDER).wait()
        shutil.copyfile(
            DIR_TEMP / self.html_filename,
            DIR_BUILD_ASSETS / f"DoL-ModLoader-{self.game_version}-v{self.mod_loader_version}{polyfill_suffix}.APK",
        )
        logger.info(f"> Apk{polyfill_suffix} built successfully")

    def build_apk_normal(self):
        return self._build_apk(DIR_TEMP / self.html_filename)

    def build_apk_polyfill(self):
        return self._build_apk(DIR_TEMP / self.html_polyfill_filename, "-polyfill")

    @staticmethod
    def rename_pre():
        for file in os.listdir(DIR_BUILD_ASSETS):
            if file.endswith(".mod.zip"):
                shutil.move(DIR_BUILD_ASSETS / file, DIR_BUILD_ASSETS / f"{file[:-8]}-pre{file[-8:]}")
            else:
                shutil.move(DIR_BUILD_ASSETS / file, DIR_BUILD_ASSETS / f"{file[:-4]}-pre{file[-4:]}")

    """ BUILD RELEASE NOTE"""
    @staticmethod
    def fetch_changelog() -> str:
        with open(FILE_README, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

        result = ""
        issues = []
        flag = False
        for line in lines:
            line = line.strip(">").strip().strip("-").strip()
            if not line:
                continue

            if not line.startswith("20") and not flag:
                continue

            if flag:
                if line.startswith("20"):
                    break
                result = f"{result}\n{line}"
            flag = True

        issues.extend(re.findall(r"\[(issue[\-dc]*\d+)*?]", result))
        for line in lines:
            if not line.startswith("[issue"):
                continue

            issue = line.split(":")[0].strip("[").strip("]")
            if issue not in issues:
                continue

            result = f"{result}\n{line.strip()}"
        return result

    @staticmethod
    def calculate_md5() -> str:
        result = "md5:"
        for file in os.listdir(DIR_BUILD_ASSETS):
            with open(DIR_BUILD_ASSETS / file, "rb") as fp:
                content = fp.read()
            result = f"{result}\n`{file}`: `{hashlib.md5(content).hexdigest()}`"
        return result

    @property
    def section_changelog(self) -> str:
        return self.fetch_changelog()

    @property
    def section_md5(self) -> str:
        return self.calculate_md5()

    def generate_release_note(self) -> None:
        with open(DIR_BUILD / "note.md", "w", encoding="utf-8") as fp:
            fp.write(
                f"{self.section_changelog}"
                "\n\n"
                f"{self.section_md5}"
                "\n\n"
                "## 致谢名单\n"
                "[CREDITS.md](CREDITS.md)"
            )
        logger.info("> release note generated successfully")

    def release(self):
        ...

    """ PROPERTY """
    @property
    def github(self) -> Github:
        return self._github

    @property
    def client(self) -> httpx.AsyncClient:
        return self._client

    """ FILENAME """
    @staticmethod
    def _get_tmp_filename(prefix: str = "", suffix: str = "") -> str:
        return [
            file
            for file in os.listdir(DIR_TEMP)
            if file.startswith(prefix)
            if file.endswith(suffix)
        ][0]

    @staticmethod
    def _get_dist_filename() -> str:
        return [file for file in os.listdir(DIR_GAME / "dist")][0]

    def get_mod_loader_filename(self) -> str:
        return self._get_tmp_filename(prefix="DoL-ModLoader")

    def get_image_pack_filename(self) -> str:
        return self._get_tmp_filename(prefix="GameOriginalImagePack")

    def get_i18n_filename(self) -> str:
        return self._get_tmp_filename(prefix="ModI18N")

    def get_html_filename(self) -> str:
        return self._get_tmp_filename(prefix="Degrees of Lewdity", suffix="mod.html")

    def get_html_polyfill_filename(self) -> str:
        return self._get_tmp_filename(prefix="Degrees of Lewdity", suffix="polyfill.html")

    @property
    def mod_loader_filename(self) -> str:
        return self.get_mod_loader_filename()

    @property
    def image_pack_filename(self) -> str:
        return self.get_image_pack_filename()

    @property
    def i18n_filename(self) -> str:
        return self.get_i18n_filename()

    @property
    def html_filename(self) -> str:
        return self.get_html_filename()

    @property
    def html_polyfill_filename(self) -> str:
        return self.get_html_polyfill_filename()

    @property
    def apk_filename(self) -> str:
        return self._get_dist_filename()

    """ VERSION """
    @staticmethod
    def get_game_version() -> str:
        with open(DIR_GAME / "version", "r", encoding="utf-8") as fp:
            return fp.read().strip()

    def get_i18n_version(self) -> str:
        return self.i18n_filename.split("-")[1]

    def get_mod_loader_version(self) -> str:
        return self.mod_loader_filename.split("-")[2]

    @property
    def game_version(self) -> str:
        return self.get_game_version()

    @property
    def i18n_version(self) -> str:
        return self.get_i18n_version()

    @property
    def mod_loader_version(self) -> str:
        return self.get_mod_loader_version()


async def main():
    start = time.time()
    async with httpx.AsyncClient(verify=False) as client:
        with Github(auth=Auth.Token(ACCESS_TOKEN)) as github:
            process = ReleaseBuild(github, client)
            """ 开始 """
            process.clear()

            """ 运行 """  # TODO

            """ 下载 """
            await process.download_mod_loader()
            await process.download_i18n()

            """ 解压 """
            process.decompress_mod_loader()

            """ 打包 """
            process.rename_image_pack()
            process.move_i18n()
            process.move_image_pack()
            process.build_compress_normal()
            process.build_compress_polyfill()
            process.build_apk_normal()
            process.build_apk_polyfill()
            process.rename_pre()  # 预览版

            """ 构建 """
            process.generate_release_note()
    logger.info(f"> cost {time.time() - start:.2f} seconds")

if __name__ == '__main__':
    asyncio.run(main())
