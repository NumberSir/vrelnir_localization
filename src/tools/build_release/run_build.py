"""
1. 触发 ModLoader 自动构建
2. 下载构建好的 ModLoader 包
3. 下载构建好的图片包

4. 触发汉化包自动构建
5. 下载构建好的汉化包

6. 解压 ModLoader 包出两个 HTML 文件
7. 构建 Credits
8. 把 README, Credits, LICENSE 和 HTML 打成压缩包
9. 替换官方 APK 中的 HTML
10. 删除官方 APK 中的 img 文件夹
11. 计算 MD5
12. 提取出 README 中的本次更新部分
13. 构建 Release
"""
import asyncio
import os
import shutil
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
DIR_GAME = ROOT.parent.parent.parent / "degrees-of-lewdity-master"
DIR_RELEASE = Path("D:\\Users\\numbersir\\Documents\\GitHub\\Degrees-of-Lewdity-Chinese-Localization")

FILE_LICENSE = DIR_GAME / "LICENSE"
FILE_CREDITS = DIR_CREDITS / "CREDITS.md"
FILE_README = DIR_RELEASE / "README.md"

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
        logger.info("initialize successfully")

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
        logger.info("ModLoader & Imagepack downloaded successfully")

    async def download_i18n(self):
        await self._download("NumberSir/DoL-I18n-Build")
        logger.info("ModI18N downloaded successfully")

    """ DECOMPRESS """
    def decompress_mod_loader(self):
        with zipfile.ZipFile(DIR_TEMP / self.mod_loader_filename, "r") as zfp:
            for file in zfp.filelist:
                if not file.filename.endswith(".html"):
                    continue
                zfp.extract(file, DIR_TEMP)

    """ BUILD """
    def move_i18n(self):
        shutil.copyfile(
            DIR_TEMP / self.i18n_filename,
            DIR_BUILD_ASSETS / self.i18n_filename,
        )
        logger.info("ModI18N built successfully")

    def rename_image_pack(self):
        (DIR_TEMP / self.image_pack_filename).rename(DIR_TEMP / f'{self.image_pack_filename.split("-")[0].split(".")[0]}-{self.game_version}.mod.zip')

    def move_image_pack(self):
        shutil.copyfile(
            DIR_TEMP / self.image_pack_filename,
            DIR_BUILD_ASSETS / self.image_pack_filename,
        )
        logger.info("Imagepack built successfully")

    def _build_compress(self, html_filepath: Path, polyfill_suffix: str = ""):
        with ZipFile(DIR_BUILD_ASSETS / f"DoL-ModLoader-{self.game_version}-v{self.mod_loader_version}{polyfill_suffix}.zip", "w") as zfp:
            zfp.write(filename=FILE_README, arcname=FILE_README.name)
            zfp.write(filename=FILE_LICENSE, arcname=FILE_LICENSE.name)
            zfp.write(filename=FILE_CREDITS, arcname=FILE_CREDITS.name)
            zfp.write(filename=html_filepath, arcname=HTML_FILENAME)
        logger.info(f"Zipfile{polyfill_suffix} built successfully")

    def build_compress_normal(self):
        return self._build_compress(DIR_TEMP / self.html_filename)

    def build_compress_polyfill(self):
        return self._build_compress(DIR_TEMP / self.html_polyfill_filename, "-polyfill")

    def build_apk(self):
        ...

    def fetch_changelog(self):
        ...

    def calculate_md5(self):
        ...

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
    def _get_filename(prefix: str = "", suffix: str = "") -> str:
        return [
            file
            for file in os.listdir(DIR_TEMP)
            if file.startswith(prefix)
            if file.endswith(suffix)
        ][0]

    def get_mod_loader_filename(self) -> str:
        return self._get_filename(prefix="DoL-ModLoader")

    def get_image_pack_filename(self) -> str:
        return self._get_filename(prefix="GameOriginalImagePack")

    def get_i18n_filename(self) -> str:
        return self._get_filename(prefix="ModI18N")

    def get_html_filename(self) -> str:
        return self._get_filename(prefix="Degrees of Lewdity", suffix="mod.html")

    def get_html_polyfill_filename(self) -> str:
        return self._get_filename(prefix="Degrees of Lewdity", suffix="polyfill.html")

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
    async with httpx.AsyncClient(verify=False) as client:
        with Github(auth=Auth.Token(ACCESS_TOKEN)) as github:
            build = ReleaseBuild(github, client)
            build.clear()

            await build.download_mod_loader()
            await build.download_i18n()

            build.decompress_mod_loader()

            build.rename_image_pack()
            build.move_i18n()
            build.move_image_pack()

            build.build_compress_normal()
            build.build_compress_polyfill()


if __name__ == '__main__':
    asyncio.run(main())
