import re

from aiocsv import AsyncReader, AsyncWriter
from aiofiles import open as aopen, os as aos
from pathlib import Path
from typing import List
from zipfile import ZipFile

import asyncio
import json
import httpx
import os
import shutil
import subprocess
import time
import webbrowser

from .consts import *
from .log import logger
from .parse_text import *
from .utils import *


class ProjectDOL:
    """本地化主类"""

    def __init__(self):
        self._type: str = ...
        self._rules: dict = ...
        self._ignores: List[str] = ...
        self._version: str = ...

        self._paratranz_file_lists: List[Path] = None
        self._raw_dicts_file_lists: List[Path] = None
        self._game_texts_file_lists: List[Path] = None

    async def async_init(self, type_: str = "common") -> "ProjectDOL":
        async with aopen(DIR_DATA_ROOT / "rules.json", "r", encoding="utf-8") as fp:
            self._rules = json.loads(await fp.read())
        async with aopen(DIR_DATA_ROOT / "ignores.json", "r", encoding="utf-8") as fp:
            self._ignores = json.loads(await fp.read())
        self._type = type_
        return self

    @staticmethod
    async def _init_dirs(version: str):
        """创建目标文件夹"""
        await aos.makedirs(DIR_TEMP_ROOT, exist_ok=True)
        await aos.makedirs(DIR_RAW_DICTS / version / "csv", exist_ok=True)
        # await aos.makedirs(DIR_FINE_DICTS, exist_ok=True)

    async def fetch_latest_version(self):
        async with httpx.AsyncClient() as client:
            url = f"{REPOSITORY_URL_COMMON}/-/raw/master/version" if self._type == "common" else f"{REPOSITORY_URL_DEV}/-/raw/dev/version"
            response = await client.get(url)
            logger.info(f"当前仓库最新版本: {response.text}")
            self._version = response.text

    """生成字典"""
    async def download_from_gitgud(self):
        """从 gitgud 下载源仓库文件"""
        await self.fetch_latest_repository()
        await self.unzip_latest_repository()

    async def fetch_latest_repository(self):
        """获取最新仓库内容"""
        logger.info("===== 开始获取最新仓库内容 ...")
        async with httpx.AsyncClient() as client:
            await self._init_dirs(self._version)
            zip_url = REPOSITORY_ZIP_URL_COMMON if self._type == "common" else REPOSITORY_ZIP_URL_DEV
            response = await client.head(zip_url, timeout=60, follow_redirects=True)
            filesize = int(response.headers["Content-Length"])
            chunks = await chunk_split(filesize, 64)

            tasks = [
                chunk_download(zip_url, client, start, end, idx, len(chunks), FILE_REPOSITORY_ZIP)
                for idx, (start, end) in enumerate(chunks)
            ]
            await asyncio.gather(*tasks)
        logger.info("##### 最新仓库内容已获取! \n")

    @staticmethod
    async def unzip_latest_repository():
        """解压到本地"""
        logger.info("===== 开始解压最新仓库内容 ...")
        with ZipFile(FILE_REPOSITORY_ZIP) as zfp:
            zfp.extractall(DIR_GAME_ROOT_COMMON.parent)
        logger.info("##### 最新仓库内容已解压! \n")

    async def create_dicts(self):
        """创建字典"""
        await self._fetch_all_text_files()
        await self._create_all_text_files_dir()
        await self._process_texts()

    async def _fetch_all_text_files(self):
        """获取所有文本文件"""
        logger.info("===== 开始获取所有文本文件位置 ...")
        self._game_texts_file_lists = []
        texts_dir = DIR_GAME_TEXTS_COMMON if self._type == "common" else DIR_GAME_TEXTS_DEV
        for root, dir_list, file_list in os.walk(texts_dir):
            for file in file_list:
                if not file.endswith(SUFFIX_TEXTS):
                    continue
                if all(keyword not in file for keyword in self._ignores):
                    self._game_texts_file_lists.append(Path(root).absolute() / file)
        logger.info("##### 所有文本文件位置已获取 !\n")

    async def _create_all_text_files_dir(self):
        """创建目录防报错"""
        dir_name = DIR_GAME_ROOT_COMMON_NAME if self._type == "common" else DIR_GAME_ROOT_DEV_NAME
        tasks = []
        for file in self._game_texts_file_lists:
            target_dir = file.parent.__str__().split(f"{dir_name}\\")[1]
            target_dir_csv = DIR_RAW_DICTS / self._version / "csv" / target_dir
            if not target_dir_csv.exists():
                tasks.append(aos.makedirs(target_dir_csv, exist_ok=True))
        await asyncio.gather(*tasks)

    async def _process_texts(self):
        """处理翻译文本为键值对"""
        logger.info("===== 开始处理翻译文本为键值对 ...")
        tasks = [
            self._process_for_gather(idx, file)
            for idx, file in enumerate(self._game_texts_file_lists)
        ]
        await asyncio.gather(*tasks)
        logger.info("##### 翻译文本已处理为键值对 ! \n")

    async def _process_for_gather(self, idx: int, file: Path):
        target_file = file.__str__().split("game\\")[1].replace(SUFFIX_TEXTS, "")

        async with aopen(file, "r", encoding="utf-8") as fp:
            lines = await fp.readlines()

        rule = await self._match_rules(file)
        pt = await ParseText().async_init(lines, rule)
        able_lines = await pt.parse()

        if not able_lines:
            logger.warning(f"\t- ***** 文件 {file} 无有效翻译行 !")
        results_lines_csv = [
            (f"{idx_ + 1}_{'_'.join(self._version[2:].split('.'))}|", _.strip()) for idx_, _ in enumerate(lines) if
            able_lines[idx_]
        ]
        async with aopen(DIR_RAW_DICTS / self._version / "csv" / "game" / f"{target_file}.csv", "w", encoding="utf-8", newline="") as fp:
            await AsyncWriter(fp).writerows(results_lines_csv)
        # logger.info(f"\t- ({idx + 1} / {len(self._game_texts_file_lists)}) {target_file} 处理完毕")

    async def _match_rules(self, file: Path):
        """匹配规则"""
        return next((v for k, v in self._rules.items() if k in file.name), None)


    """更新字典"""
    async def update_dicts(self):
        """更新字典"""
        logger.info("===== 开始更新字典 ...")
        await self._create_unavailable_files_dir()
        file_mapping: dict = {}
        for root, dir_list, file_list in os.walk(DIR_PARATRANZ / "utf8"):  # 导出的旧字典
            if "失效词条" in root:
                continue
            for file in file_list:
                file_mapping[Path(root).absolute() / file] = DIR_RAW_DICTS / self._version / "csv" / "game" / Path(root).relative_to(DIR_PARATRANZ / "utf8") / file

        tasks = [
            self._update_for_gather(old_file, new_file, idx, len(file_mapping))
            for idx, (old_file, new_file) in enumerate(file_mapping.items())
        ]
        await asyncio.gather(*tasks)
        logger.info("##### 字典更新完毕 !\n")

    async def _update_for_gather(self, old_file: Path, new_file: Path, idx: int, full: int):
        """gather 用"""

        async with aopen(old_file, "r", encoding="utf-8") as fp:
            old_data = [row async for row in AsyncReader(fp)]
            old_ens: dict = {
                row[-2] if len(row) > 2 else row[1]: idx_
                for idx_, row in enumerate(old_data)
            }  # 旧英文: 旧英文行键

        async with aopen(new_file, "r", encoding="utf-8") as fp:
            new_data = [row async for row in AsyncReader(fp)]
            new_ens: dict = {
                row[-1]: idx_
                for idx_, row in enumerate(new_data)
            }  # 旧英文: 旧英文行键

        # 1. 未变的键和汉化直接替换
        for idx_, row in enumerate(new_data):
            if row[-1] in old_ens:
                new_data[idx_][0] = old_data[old_ens[row[-1]]][0]
                if len(old_data[old_ens[row[-1]]]) >= 3:
                    new_data[idx_].append(old_data[old_ens[row[-1]]][-1].strip())

        # 2. 不存在的英文移入失效词条
        unavailables = []
        for idx_, row in enumerate(old_data):
            old_en = row[-2] if len(row) > 2 else row[-1]
            if old_en not in new_ens:
                unavailables.append(old_data[idx_])
        unavailable_file = DIR_RAW_DICTS / self._version / "csv/game/失效词条" / old_file.__str__().split("utf8\\")[1] if unavailables else None

        async with aopen(new_file, "w", encoding="utf-8-sig", newline="") as fp:
            await AsyncWriter(fp).writerows(new_data)

        if unavailable_file:
            if not unavailable_file.exists():
                await aos.makedirs(unavailable_file.parent, exist_ok=True)
                async with aopen(unavailable_file, "w", encoding="utf-8-sig", newline="") as fp:
                    await AsyncWriter(fp).writerows(unavailables)
            else:
                async with aopen(unavailable_file, "r", encoding="utf-8-sig") as fp:
                    old_unavailable_data = [row async for row in AsyncReader(fp)]
                async with aopen(unavailable_file, "w", encoding="utf-8-sig", newline="") as fp:
                    await AsyncWriter(fp).writerows(old_unavailable_data + unavailables)

        # logger.info(f"\t- ({idx + 1} / {full}) {new_file.__str__().split('game')[1]} 更新完毕")

    async def _create_unavailable_files_dir(self):
        """创建失效词条目录"""
        shutil.copytree(DIR_PARATRANZ / "utf8" / "失效词条", DIR_RAW_DICTS / self._version / "csv/game/失效词条")
        logger.info("\t- 失效词条目录已迁移")

    """应用字典"""
    async def apply_dicts(self, blacklist_dirs: List[str] = None, blacklist_files: List[str] = None):
        """汉化覆写游戏文件"""
        DIR_GAME_TEXTS = DIR_GAME_TEXTS_COMMON if self._type == "common" else DIR_GAME_TEXTS_DEV
        logger.info("===== 开始覆写汉化 ...")
        file_mapping: dict = {}
        for root, dir_list, file_list in os.walk(DIR_PARATRANZ / "utf8"):
            if "失效词条" in root:
                continue
            for file in file_list:
                file_mapping[Path(root).absolute() / file] = DIR_GAME_TEXTS / Path(root).relative_to(DIR_PARATRANZ / "utf8") / f"{file.split('.')[0]}.twee"

        tasks = [
            self._apply_for_gather(file, target_file, idx, len(file_mapping))
            for idx, (file, target_file) in enumerate(file_mapping.items())
        ]
        await asyncio.gather(*tasks)
        logger.info("##### 汉化覆写完毕 !\n")

    async def _apply_for_gather(self, file: Path, target_file: Path, idx: int, full: int):
        """gather 用"""
        async with aopen(target_file, "r", encoding="utf-8") as fp:
            raw_targets: List[str] = await fp.readlines()
        async with aopen(file, "r", encoding="utf-8") as fp:
            async for row in AsyncReader(fp):
                en, zh = row[-2:]
                if self._is_full_comma(zh):
                    logger.warning(f"\t!!! 可能的全角逗号错误：{file.relative_to(DIR_PARATRANZ/'utf8')} | {row[0]} | {zh}")
                if self._is_lack_angle(zh):
                    logger.warning(f"\t!!! 可能的尖括号数量错误：{file.relative_to(DIR_PARATRANZ/'utf8')} | {row[0]} | {zh}")
                for idx_, target_row in enumerate(raw_targets):
                    if en == target_row.strip() and zh.strip():
                        raw_targets[idx_] = target_row.replace(en, zh)
                        break
        async with aopen(target_file, "w", encoding="utf-8") as fp:
            await fp.writelines(raw_targets)
        # logger.info(f"\t- ({idx + 1} / {full}) {target_file.__str__().split('game')[1]} 覆写完毕")

    @staticmethod
    def _is_full_comma(line: str):
        """全角逗号"""
        return line.endswith('"，')

    @staticmethod
    def _is_lack_angle(line: str):
        """<<> 缺一个 >"""
        left_angle_single = re.findall(r"(<)", line)
        right_angle_single = re.findall(r"(>)", line)
        left_angle_double = re.findall(r"(<<)", line)
        right_arrow = re.findall(r"(=>)", line)
        return (
            len(left_angle_double) == len(right_angle_single)   # 形如 << >

            and len(right_angle_single) != 0                    # 形如 <<
            and (len(left_angle_single) - len(right_angle_single)) / 2 != len(left_angle_double)  # 形如 < > << >>
            and len(right_angle_single) != len(right_arrow)         # 形如 << >> =>
            and len(right_angle_single) % 2 != 0                    # 形如 << >> <<
            and len(left_angle_single) != len(right_angle_single)   # 形如 < >
        )

    """ 删删删 """
    async def drop_all_dirs(self):
        """恢复到最初时的样子"""
        logger.warning("===== 开始删库跑路 ...")
        await self._drop_temp()
        await self._drop_game()
        await self._drop_dict()
        await self._drop_paratranz()
        logger.warning("##### 删库跑路完毕 !\n")

    async def _drop_temp(self):
        """删掉临时文件"""
        shutil.rmtree(DIR_TEMP_ROOT, ignore_errors=True)
        logger.warning("\t- 缓存目录已删除")

    async def _drop_game(self):
        """删掉游戏库"""
        game_dir = DIR_GAME_ROOT_COMMON if self._type == "common" else DIR_GAME_ROOT_DEV
        shutil.rmtree(game_dir, ignore_errors=True)
        logger.warning("\t- 游戏目录已删除")

    async def _drop_dict(self):
        """删掉生成的字典"""
        shutil.rmtree(DIR_RAW_DICTS, ignore_errors=True)
        logger.warning("\t- 字典目录已删除")

    async def _drop_paratranz(self):
        """删掉下载的汉化包"""
        shutil.rmtree(DIR_PARATRANZ, ignore_errors=True)
        logger.warning("\t- 汉化目录已删除")

    """ 编译游戏 """
    def compile(self):
        """编译游戏"""
        logger.info("===== 开始编译游戏 ...")
        self._compile_for_windows()
        logger.info("##### 游戏编译完毕 !")

    def _compile_for_windows(self):
        """win"""
        game_dir = DIR_GAME_ROOT_COMMON if self._type == "common" else DIR_GAME_ROOT_DEV
        subprocess.Popen(game_dir / "compile.bat")
        time.sleep(5)
        logger.info("\t- Windows 游戏编译完成")

    def _compile_for_linux(self):
        """linux"""

    def _compile_for_mobile(self):
        """android"""

    """ 在浏览器中启动 """
    def run(self):
        game_dir = DIR_GAME_ROOT_COMMON if self._type == "common" else DIR_GAME_ROOT_DEV
        webbrowser.open(game_dir / "Degrees of Lewdity VERSION.html")


__all__ = [
    "ProjectDOL"
]
