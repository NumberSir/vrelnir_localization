import contextlib
import csv
import datetime
import re
from .ast import Acorn, JSSyntaxError
from pathlib import Path
from typing import Any
from zipfile import ZipFile, ZIP_DEFLATED
from urllib.parse import quote
from zipfile import ZipFile as zf, ZIP_DEFLATED
from aiofiles import open as aopen

import asyncio
import json
import httpx
import os
import platform
import shutil
import subprocess
import time
import webbrowser
import stat

from .consts import *
from .log import logger
from .parse_text import *
from .utils import *

LOGGER_COLOR = logger.opt(colors=True)


class ProjectDOL:
    """本地化主类"""

    def __init__(self, type_: str = "common"):
        with open(DIR_JSON_ROOT / "blacklists.json", "r", encoding="utf-8") as fp:
            self._blacklists: dict[str, list] = json.load(fp)
        with open(DIR_JSON_ROOT / "whitelists.json", "r", encoding="utf-8") as fp:
            self._whitelists: dict[str, list] = json.load(fp)
        self._type: str = type_
        self._version: str = None
        self._mention_name = "" if self._type == "common" else "dev"
        self._commit: dict[str, Any] = None
        self._acorn = Acorn()
        if FILE_COMMITS.exists():
            with open(FILE_COMMITS, "r", encoding="utf-8") as fp:
                self._commit: dict[str, Any] = json.load(fp)
                
        self._is_latest = False
        self._paratranz_file_lists: list[Path] = None
        self._raw_dicts_file_lists: list[Path] = None
        self._game_texts_file_lists: list[Path] = None

    def _init_dirs(self, version: str):
        """创建目标文件夹"""
        os.makedirs(DIR_TEMP_ROOT, exist_ok=True)
        os.makedirs(DIR_RAW_DICTS / self._type / version / "csv", exist_ok=True)

    """ 获取最新版本 """
    async def fetch_latest_version(self, is_quiet: bool = True):
        async with httpx.AsyncClient() as client:
            if self._type == "common":
                url = f"{REPOSITORY_URL_COMMON}/-/raw/master/version"
            elif self._type == "world":
                url = f"{REPOSITORY_URL_WORLD}/-/raw/master/version"
            else:
                url = f"{REPOSITORY_URL_DEV}/-/raw/dev/version"
            response = await client.get(url)
            if not is_quiet:
                logger.info(f"当前{self._mention_name}仓库最新版本: {response.text}")
            self._version = response.text
        self._init_dirs(self._version)

    """ 下载源码 """
    async def download_from_gitgud(self):
        """从 gitgud 下载源仓库文件"""
        if not self._version:
            await self.fetch_latest_version()
        if self._is_latest:  # 下载慢，是最新就不要重复下载了
            dol_path_zip = DIR_ROOT / f"dol{self._mention_name}.zip"
            if (DIR_ROOT / "dol.zip").exists() or (DIR_ROOT / f"dol{self._mention_name}.zip").exists():
                with contextlib.suppress(shutil.Error, FileNotFoundError):
                    shutil.move(DIR_ROOT / "dol.zip", DIR_TEMP_ROOT)
                with contextlib.suppress(shutil.Error, FileNotFoundError):
                    shutil.move(dol_path_zip, DIR_TEMP_ROOT)
                with contextlib.suppress(shutil.Error, FileNotFoundError):
                    shutil.move(DIR_ROOT / f"dol世扩.zip", DIR_TEMP_ROOT)
                await self.unzip_latest_repository()
                return
        await self.fetch_latest_repository()
        await self.unzip_latest_repository()

    async def fetch_latest_repository(self):
        """获取最新仓库内容"""
        logger.info(f"===== 开始获取最新{self._mention_name}仓库内容 ...")
        async with httpx.AsyncClient() as client:
            if self._type == "common":
                zip_url = REPOSITORY_ZIP_URL_COMMON
            elif self._type == "world":
                zip_url = REPOSITORY_ZIP_URL_WORLD
            else:
                zip_url = REPOSITORY_ZIP_URL_DEV
            flag = False
            for _ in range(3):
                try:
                    response = await client.head(zip_url, timeout=60, follow_redirects=True)
                    filesize = int(response.headers["Content-Length"])
                    chunks = await chunk_split(filesize, 64)
                except (httpx.ConnectError, KeyError) as e:
                    continue
                else:
                    flag = True
                    break

            if not flag:
                logger.error("***** 无法正常下载最新仓库源码！请检查你的网络连接是否正常！")
            tasks = [
                chunk_download(zip_url, client, start, end, idx, len(chunks), DIR_TEMP_ROOT / f"dol{self._mention_name}.zip")
                for idx, (start, end) in enumerate(chunks)
            ]
            await asyncio.gather(*tasks)
        logger.info(f"##### 最新{self._mention_name}仓库内容已获取! \n")

    async def unzip_latest_repository(self):
        """解压到本地"""
        logger.info(f"===== 开始解压{self._mention_name}最新仓库内容 ...")
        with ZipFile(DIR_TEMP_ROOT / f"dol{self._mention_name}.zip") as zfp:
            zfp.extractall(DIR_ROOT)
        logger.info(f"##### 最新{self._mention_name}仓库内容已解压! \n")

    async def patch_format_js(self):
        """汉化 format.js"""
        logger.info(f"===== 开始替换 format.js ...")
        shutil.copyfile(
            DIR_DATA_ROOT / "jsmodule" / "format.js",
            DIR_GAME_ROOT_COMMON / "devTools" / "tweego" / "storyFormats" / "sugarcube-2" / "format.js"
        )
        logger.info(f"##### format.js 已替换！\n")

    """ 创建生肉词典 """
    async def create_dicts(self):
        """创建字典"""
        await self._fetch_all_text_files()
        await self._create_all_text_files_dir()
        await self._process_texts()

    async def _fetch_all_text_files(self):
        """获取所有文本文件"""
        logger.info(f"===== 开始获取{self._mention_name}所有文本文件位置 ...")
        self._game_texts_file_lists = []
        if self._type == "common":
            texts_dir = DIR_GAME_TEXTS_COMMON
        elif self._type == "world":
            texts_dir = DIR_GAME_TEXTS_WORLD
        else:
            texts_dir = DIR_GAME_TEXTS_DEV
        for root, dir_list, file_list in os.walk(texts_dir):
            dir_name = Path(root).absolute().name
            for file in file_list:
                if not file.endswith(SUFFIX_TWEE):
                    if not file.endswith(SUFFIX_JS):
                        continue

                    if dir_name in self._whitelists and file in self._whitelists[dir_name]:
                        self._game_texts_file_lists.append(Path(root).absolute() / file)
                    continue

                if dir_name not in self._blacklists:
                    self._game_texts_file_lists.append(Path(root).absolute() / file)
                elif (
                    not self._blacklists[dir_name]
                    or file in self._blacklists[dir_name]
                ):
                    continue
                else:
                    self._game_texts_file_lists.append(Path(root).absolute() / file)

        logger.info(f"##### {self._mention_name}所有文本文件位置已获取 !\n")

    async def _create_all_text_files_dir(self):
        """创建目录防报错"""
        if not self._version:
            await self.fetch_latest_version()
        if self._type == "common":
            dir_name = DIR_GAME_ROOT_COMMON_NAME
        elif self._type == "world":
            dir_name = DIR_GAME_ROOT_WORLD_NAME
        else:
            dir_name = DIR_GAME_ROOT_DEV_NAME
        for file in self._game_texts_file_lists:
            target_dir = file.parent.parts[file.parts.index(dir_name)+1:]
            target_dir_csv = (DIR_RAW_DICTS / self._type / self._version / "csv").joinpath(*target_dir)
            if not target_dir_csv.exists():
                os.makedirs(target_dir_csv, exist_ok=True)
            target_dir_json = (DIR_RAW_DICTS / self._type / self._version / "json").joinpath(*target_dir)
            if not target_dir_json.exists():
                os.makedirs(target_dir_json, exist_ok=True)

    async def _process_texts(self):
        """处理翻译文本为键值对"""
        logger.info(f"===== 开始处理{self._mention_name}翻译文本为键值对 ...")
        tasks = [
            self._process_for_gather(idx, file)
            for idx, file in enumerate(self._game_texts_file_lists)
        ]
        await asyncio.gather(*tasks)
        logger.info(f"##### {self._mention_name}翻译文本已处理为键值对 ! \n")

    async def _process_for_gather(self, idx: int, file: Path):
        target_file = Path().joinpath(*file.parts[file.parts.index("game")+1:]).with_suffix("")

        with open(file, "r", encoding="utf-8") as fp:
            lines = fp.readlines()
        with open(file, "r", encoding="utf-8") as fp:
            content = fp.read()
        if file.name.endswith(SUFFIX_TWEE):
            pt = ParseTextTwee(lines, file)
            pre_bool_list = pt.pre_parse_set_run()
        elif file.name.endswith(SUFFIX_JS):
            pt = ParseTextJS(lines, file)
            target_file = f"{target_file}.js"
        else:
            return
        able_lines = pt.parse()
        if file.name.endswith(SUFFIX_TWEE) and pt.pre_bool_list:
            able_lines = [
                True if pre_bool_list[idx] or line else False
                for idx, line in enumerate(able_lines)
            ]

        if not any(able_lines):
            logger.warning(f"\t- ***** 文件 {file} 无有效翻译行 !")
            return
        try:
            results_lines_csv = [
                (f"{idx_ + 1}_{'_'.join(self._version[2:].split('.'))}|", _.strip())
                for idx_, _ in enumerate(lines)
                if able_lines[idx_]
            ]
            results_lines_json = await self._build_json_results_with_passage(lines, able_lines, content, file.__str__().split("\\game\\")[-1].split("/game/")[-1])
        except IndexError:
            logger.error(f"lines: {len(lines)} - parsed: {len(able_lines)}| {file}")
            results_lines_csv = None
            results_lines_json = None
        if results_lines_csv:
            with open(DIR_RAW_DICTS / self._type / self._version / "csv" / "game" / f"{target_file}.csv", "w", encoding="utf-8-sig", newline="") as fp:
                csv.writer(fp).writerows(results_lines_csv)
        if results_lines_json:
            with open(DIR_RAW_DICTS / self._type / self._version / "json" / "game" / f"{target_file}.json", "w", encoding="utf-8", newline="") as fp:
                json.dump(results_lines_json, fp, ensure_ascii=False, indent=2)
        # logger.info(f"\t- ({idx + 1} / {len(self._game_texts_file_lists)}) {target_file} 处理完毕")

    async def _build_json_results_with_passage(self, lines: list[str], able_lines: list[bool], content: str, file: str) -> list[dict]:
        """导出成带 passage 注释的行文本"""
        results_lines_json = []
        passage_name = None
        pos_relative = None
        pos_global = 0
        for idx, line in enumerate(lines):
            if line.startswith("::"):
                pos_relative = 0
                tmp_ = line.lstrip(":: ")
                if "[" not in line:
                    passage_name = tmp_.strip()
                else:
                    for idx_, char in enumerate(tmp_):
                        if char != "[":
                            continue
                        passage_name = tmp_[:idx_-1].strip()
                        break
                    else:
                        raise

            if able_lines[idx]:
                pos_start = 0
                if line != line.lstrip():  # 前面的 \t \s 也要算上
                    for char in line:
                        if char == line.strip()[0]:
                            break
                        pos_start += 1
                results_lines_json.append({
                    "passage": passage_name,  # 非 twee 文件为 null
                    "filepath": file,
                    "key": f"{idx + 1}_{'_'.join(self._version[2:].split('.'))}|",
                    "original": line.strip(),
                    "translation": "",
                    "pos": pos_relative + pos_start if pos_relative is not None else pos_global + pos_start  # 非 twee 文件为 null
                })
                if content[pos_global + pos_start] != line.lstrip()[0]:
                    logger.error(f"pos可能不对！{file} | {passage_name} | {line}".replace("\t", "\\t").replace("\n", "\\n"))
            if pos_relative is not None and not line.startswith("::"):
                pos_relative += len(line)
            pos_global += len(line)
        return results_lines_json

    """ 去重生肉词典 """
    async def shear_off_repetition(self):
        """目前仅限世扩"""
        logger.info(f"===== 开始去重{self._mention_name}文本 ...")
        # 不要对原版调用去重
        if self._type == "common":
            raise Exception("不要对原版调用去重")

        for root, dir_list, file_list in os.walk(DIR_RAW_DICTS / self._type / self._version / "csv" / "game"):
            if "失效词条" in root:
                continue

            for file in file_list:
                common_file_path = DIR_PARATRANZ / "common" / "utf8" / Path().joinpath(*(Path(root) / file).split("game//")[1])
                if not common_file_path.exists():
                    continue
                mod_file_path = Path(root) / file

                with open(mod_file_path, "r", encoding="utf-8") as fp:
                    mod_data = list(csv.reader(fp))

                with open(common_file_path, "r", encoding="utf-8") as fp:
                    common_data = list(csv.reader(fp))
                    common_ens: dict = {
                        row[-2] if len(row) > 2 else row[1]: idx_
                        for idx_, row in enumerate(common_data)
                    }  # 旧英文: 旧英文行键

                # mod 中的键也在原版中，直接删掉
                for idx, row in enumerate(mod_data.copy()):
                    if row[-1] in common_ens:
                        mod_data[idx] = None

                mod_data = [_ for _ in mod_data if _]
                if not mod_data:
                    os.remove(mod_file_path)
                    continue

                with open(mod_file_path, "w", encoding="utf-8-sig", newline="") as fp:
                    csv.writer(fp).writerows(mod_data)

            if not os.listdir(Path(root)):
                shutil.rmtree(Path(root))
        logger.info(f"##### {self._mention_name}所有文本已去重 !\n")

    """ 替换生肉词典 """
    async def update_dicts(self):
        """更新字典"""
        if not self._version:
            await self.fetch_latest_version()
        logger.info(f"===== 开始更新{self._mention_name}字典 ...")
        file_mapping: dict = {}
        for root, dir_list, file_list in os.walk(DIR_PARATRANZ / self._type / "utf8"):  # 导出的旧字典
            if "失效词条" in root:
                continue
            for file in file_list:
                file_mapping[Path(root).absolute() / file] = (
                    DIR_RAW_DICTS / self._type / self._version / "csv" / "game" / Path(root).relative_to(DIR_PARATRANZ / self._type / "utf8") / file,
                    DIR_RAW_DICTS / self._type / self._version / "json" / "game" / Path(root).relative_to(DIR_PARATRANZ / self._type / "utf8") / f'{file.removesuffix(".csv")}.json',
                )

        tasks = [
            self._update_for_gather(old_file, new_file, json_file)
            for old_file, (new_file, json_file) in file_mapping.items()
        ]
        await asyncio.gather(*tasks)
        await self._integrate_json()
        logger.info(f"##### {self._mention_name}字典更新完毕 !\n")

    async def _update_for_gather(self, old_file: Path, new_file: Path, json_file: Path):
        """
        gather 用
        :param old_file: 下载的汉化文件的绝对路径
        :param new_file: 本地新抓字典文件的绝对路径
        """
        if not new_file.exists():
            unavailable_file = DIR_RAW_DICTS / self._type / self._version / "csv" / "game" / "失效词条" / Path().joinpath(*old_file.parts[old_file.parts.index("utf8")+1:])
            os.makedirs(unavailable_file.parent, exist_ok=True)
            with open(old_file, "r", encoding="utf-8") as fp:
                unavailables = list(csv.reader(fp))
            with open(unavailable_file, "w", encoding="utf-8-sig", newline="") as fp:
                csv.writer(fp).writerows(unavailables)
            return

        with open(old_file, "r", encoding="utf-8") as fp:
            old_data = list(csv.reader(fp))
            old_ens: dict = {
                row[-2] if len(row) > 2 else row[1]: idx_
                for idx_, row in enumerate(old_data)
            }  # 旧英文: 旧英文行键

        with open(new_file, "r", encoding="utf-8") as fp:
            new_data = list(csv.reader(fp))
            new_ens: dict = {
                row[-1]: idx_
                for idx_, row in enumerate(new_data)
            }  # 字典英文: 旧英文行键

        with open(json_file, "r", encoding="utf-8") as fp:
            json_data: list[dict] = json.load(fp)

        # 1. 未变的键和汉化直接替换
        for idx_, row in enumerate(new_data):
            if row[-1] in old_ens:
                new_data[idx_][0] = old_data[old_ens[row[-1]]][0]
                if len(old_data[old_ens[row[-1]]]) >= 3:
                    ts = old_data[old_ens[row[-1]]][-1].strip()
                    new_data[idx_].append(ts)
                    try:
                        json_data[idx_]["translation"] = ts
                    except IndexError as e:
                        logger.error(f"json与csv长度不同: {json_file}")

        # 2. 不存在的英文移入失效词条
        unavailables = []
        for idx_, row in enumerate(old_data):
            if len(row) <= 2:  # 没翻译的，丢掉！
                continue
            if row[-2] == row[-1]:  # 不用翻译的，丢掉！
                continue

            old_en = row[-2]
            if old_en not in new_ens:
                # logger.info(f"\t- old: {old_en}")
                unavailables.append(old_data[idx_])
        unavailable_file = DIR_RAW_DICTS / self._type / self._version / "csv" / "game" / "失效词条" / Path().joinpath(*old_file.parts[old_file.parts.index("utf8")+1:]) if unavailables else None
        with open(old_file,  "w", encoding="utf-8-sig", newline="") as fp:
            csv.writer(fp).writerows(old_data)

        with open(new_file, "w", encoding="utf-8-sig", newline="") as fp:
            csv.writer(fp).writerows(new_data)

        with open(new_file, "r", encoding="utf-8-sig") as fp:
            problem_data = fp.readlines()

        with open(json_file, "w", encoding="utf-8") as fp:
            json.dump(json_data, fp, ensure_ascii=False, indent=2)

        for idx, line in enumerate(problem_data):
            if "﻿" in line:
                problem_data[idx] = line.replace("﻿", "")

        with open(new_file, "w", encoding="utf-8-sig") as fp:
            fp.writelines(problem_data)

        if unavailable_file:
            os.makedirs(unavailable_file.parent, exist_ok=True)
            with open(unavailable_file, "w", encoding="utf-8-sig", newline="") as fp:
                csv.writer(fp).writerows(unavailables)

    async def _integrate_json(self):
        """把 json 字典合并成一个大的"""
        integrated_dict = []
        for root, dir_list, file_list in os.walk(DIR_RAW_DICTS / self._type / self._version / "json" / "game"):
            for file in file_list:
                with open(Path(root) / file, "r", encoding="utf-8") as fp:
                    json_data: list[dict] = json.load(fp)

                json_data = [
                    item for item in json_data
                    if item["original"] != item["translation"] and item["translation"]
                ]
                integrated_dict.extend(json_data)
        i18n_dict = await self._wash_json(integrated_dict)
        with open(DIR_DATA_ROOT / "json" / "i18n.json", "w", encoding="utf-8") as fp:
            json.dump(i18n_dict, fp, ensure_ascii=False, indent=2)

    @staticmethod
    async def _wash_json(integrated_dict: list[dict]) -> dict:
        """处理为 i18n mod 可接受的格式"""
        i18n_dict = {
            "typeB": {
                "TypeBOutputText": [],
                "TypeBInputStoryScript": []
            }
        }
        for data in integrated_dict:
            result_data = {
                "f": data["original"], "t": data["translation"], "pos": data["pos"]
            }

            filename = Path(data["filepath"]).name
            result_data["fileName"] = filename
            if filename.endswith(".js"):
                result_data["js"] = True
            elif filename.endswith(".css"):
                result_data["css"] = True

            if data["passage"]:
                result_data["pN"] = data["passage"]
                i18n_dict["typeB"]["TypeBInputStoryScript"].append(result_data)
                continue
            i18n_dict["typeB"]["TypeBOutputText"].append(result_data)
        return i18n_dict

    """ 替换游戏原文 """
    async def apply_dicts(self, blacklist_dirs: list[str] = None, blacklist_files: list[str] = None, debug_flag: bool = False, type_manual: str = None):
        """汉化覆写游戏文件"""
        if not self._version:
            await self.fetch_latest_version()

        if self._type == "common":
            DIR_GAME_TEXTS = DIR_GAME_TEXTS_COMMON
        elif self._type == "world":
            DIR_GAME_TEXTS = DIR_GAME_TEXTS_WORLD
        else:
            DIR_GAME_TEXTS = DIR_GAME_TEXTS_DEV
        logger.info(f"===== 开始覆写{self._mention_name}汉化 ...")

        type_manual = type_manual or self._type
        # 脑子转不过来，先这样写吧
        if type_manual != self._type:
            os.makedirs(DIR_RAW_DICTS / "common" / self._version / "csv" / "game", exist_ok=True)
            for tree in os.listdir(DIR_PARATRANZ / "common" / "utf8"):
                with contextlib.suppress(shutil.Error, FileNotFoundError):
                    shutil.move(DIR_PARATRANZ / "common" / "utf8" / tree, DIR_RAW_DICTS / "common" / self._version / "csv" / "game")

        file_mapping: dict = {}
        for root, dir_list, file_list in os.walk(DIR_RAW_DICTS / type_manual / self._version / "csv"):
            if any(_ in Path(root).absolute().__str__() for _ in blacklist_dirs):
                continue
            if "失效词条" in root:
                continue
            for file in file_list:
                # logger.warning(f"替换文件：{file}")
                if any(_ in file for _ in blacklist_files):
                    continue
                if file.endswith(".js.csv"):
                    file_mapping[Path(root).absolute() / file] = DIR_GAME_TEXTS / Path(root).relative_to(DIR_RAW_DICTS / type_manual / self._version / "csv" / "game") / f"{file.split('.')[0]}.js".replace("utf8\\", "")
                else:
                    file_mapping[Path(root).absolute() / file] = DIR_GAME_TEXTS / Path(root).relative_to(DIR_RAW_DICTS / type_manual / self._version / "csv" / "game") / f"{file.split('.')[0]}.twee".replace("utf8\\", "")

        tasks = [
            self._apply_for_gather(csv_file, twee_file, debug_flag=debug_flag, type_manual=type_manual)
            for idx, (csv_file, twee_file) in enumerate(file_mapping.items())
        ]
        await asyncio.gather(*tasks)
        logger.info(f"##### {self._mention_name}汉化覆写完毕 !\n")

    async def _apply_for_gather(self, csv_file: Path, target_file: Path, debug_flag: bool = False, type_manual: str = None):
        """gather 用"""
        with open(target_file, "r", encoding="utf-8") as fp:
            raw_targets: list[str] = fp.readlines()
        raw_targets_temp = raw_targets.copy()
        needed_replace_outfit_name_cap_flag = False
        type_manual = type_manual or self._type

        with open(csv_file, "r", encoding="utf-8") as fp:
            for row in csv.reader(fp):
                if len(row) < 3:  # 没汉化
                    continue
                en, zh = row[-2:]
                en, zh = en.strip(), zh.strip()
                if not zh:  # 没汉化/汉化为空
                    continue

                zh = re.sub('^(“)', '"', zh)
                zh = re.sub('(”)$', '"', zh)
                if self._is_lack_angle(zh, en):
                    logger.warning(f"\t!!! 可能的尖括号数量错误：{en} | {zh} | https://paratranz.cn/projects/{PARATRANZ_PROJECT_WE_ID if type_manual == 'world' else PARATRANZ_PROJECT_DOL_ID}/strings?text={quote(en)}")
                    if debug_flag:
                        webbrowser.open(f"https://paratranz.cn/projects/{PARATRANZ_PROJECT_WE_ID if type_manual == 'world' else PARATRANZ_PROJECT_DOL_ID}/strings?text={quote(en)}")
                # if self._is_lack_square(zh, en):
                #     logger.warning(f"\t!!! 可能的方括号数量错误：{en} | {zh} | https://paratranz.cn/projects/{PARATRANZ_PROJECT_WE_ID if type_manual == 'world' else PARATRANZ_PROJECT_DOL_ID}/strings?text={quote(en)}")
                #     if debug_flag:
                #         webbrowser.open(f"https://paratranz.cn/projects/{PARATRANZ_PROJECT_WE_ID if type_manual == 'world' else PARATRANZ_PROJECT_DOL_ID}/strings?text={quote(en)}")
                if self._is_different_event(zh, en):
                    logger.warning(f"\t!!! 可能的事件名称错翻：{en} | {zh} | https://paratranz.cn/projects/{PARATRANZ_PROJECT_WE_ID if type_manual == 'world' else PARATRANZ_PROJECT_DOL_ID}/strings?text={quote(en)}")
                    if debug_flag:
                        webbrowser.open(f"https://paratranz.cn/projects/{PARATRANZ_PROJECT_WE_ID if type_manual == 'world' else PARATRANZ_PROJECT_DOL_ID}/strings?text={quote(en)}")

                for idx_, target_row in enumerate(raw_targets_temp):
                    if not target_row.strip():
                        continue

                    if en == target_row.strip():
                        raw_targets[idx_] = target_row.replace(en, zh).replace(" \n", "\n").lstrip(" ")
                        raw_targets_temp[idx_] = ""

        if target_file.name.endswith(".js"):
            try:
                self._acorn.parse("".join(raw_targets))
                LOGGER_COLOR.info(f"<g>JS 语法检测通过</g> {target_file}")
            except JSSyntaxError as err:
                try:
                    LOGGER_COLOR.error(f"{target_file} | {err.err_code(raw_targets)}")
                except ValueError as e:
                    LOGGER_COLOR.error(f"{target_file}")
        with open(target_file, "w", encoding="utf-8") as fp:
            fp.writelines(raw_targets)

        # logger.info(f"\t- ({idx + 1} / {full}) {target_file.__str__().split('game')[1]} 覆写完毕")

    @staticmethod
    def _is_lack_angle(line_zh: str, line_en: str):
        """<<> 缺一个 >"""
        if ("<" not in line_en and ">" not in line_en) or ParseTextTwee.is_only_marks(line_en):
            return False

        # 首尾不好判断
        if line_zh[0] == "<":
            line_zh = f"_{line_zh}"
        if line_en[0] == "<":
            line_en = f"_{line_en}"
        if line_zh[-1] == ">":
            line_zh = f"{line_zh}_"
        if line_en[-1] == ">":
            line_en = f"{line_en}_"

        left_angle_single_zh = re.findall(r"[^<=](<)[^<=3]", line_zh)
        right_angle_single_zh = re.findall(r"[^>=](>)[^>=:]", line_zh)
        if "<<" not in line_en and ">>" not in line_en:
            if len(left_angle_single_zh) == len(right_angle_single_zh):
                return False
            # print(f"las: {len(left_angle_single_zh)}({left_angle_single_zh}) - ras: {len(right_angle_single_zh)}({right_angle_single_zh}) | {line_zh}")
            left_angle_single_en = re.findall(r"[^<=](<)[^<=3]", line_en)
            right_angle_single_en = re.findall(r"[^>=](>)[^>=:]", line_en)
            return (
                len(left_angle_single_en) != len(left_angle_single_zh)
                or len(right_angle_single_en) != len(right_angle_single_zh)
            )  # 形如 < > <, 也只有这一种情况

        left_angle_double_zh = re.findall(r"(<<)", line_zh)
        right_angle_double_zh = re.findall(r"(>>)", line_zh)
        if len(left_angle_double_zh) == len(right_angle_double_zh):
            return False

        left_angle_double_en = re.findall(r"(<<)", line_en)
        right_angle_double_en = re.findall(r"(>>)", line_en)
        return (
            len(left_angle_double_en) != len(left_angle_double_zh)
            or len(right_angle_double_en) != len(right_angle_double_zh)
        )  # 形如 << >> <<

    @staticmethod
    def _is_lack_square(line_zh: str, line_en: str):
        """缺一个 [ 或 ]"""
        if "[" not in line_en and "]" not in line_en:
            return False

        # 首尾不好判断
        if line_zh[0] == "[":
            line_zh = f"_{line_zh}"
        if line_en[0] == "[":
            line_en = f"_{line_en}"
        if line_zh[-1] == "]":
            line_zh = f"{line_zh}_"
        if line_en[-1] == "]":
            line_en = f"{line_en}_"

        left_square_single_zh = re.findall(r"[^\[](\[)[^\[]", line_zh)
        right_square_single_zh = re.findall(r"[^]](])[^]]", line_zh)
        if "[[" not in line_en and "]]" not in line_en:
            if len(left_square_single_zh) == len(right_square_single_zh):
                return False
            left_square_single_en = re.findall(r"[^\[](\[)[^\[]", line_en)
            right_square_single_en = re.findall(r"[^]](])[^]]", line_en)
            return (
                len(left_square_single_en) != len(left_square_single_zh)
                or len(right_square_single_en) != len(right_square_single_zh)
            )  # 形如 [ ] [, 也只有这一种情况

        left_square_double_zh = re.findall(r"(\[\[)", line_zh)
        right_square_double_zh = re.findall(r"(]])", line_zh)
        if len(left_square_double_zh) == len(right_square_double_zh):
            return False
        left_square_double_en = re.findall(r"(\[\[)", line_en)
        right_square_double_en = re.findall(r"(]])", line_en)
        return (
                len(left_square_double_en) != len(left_square_double_zh)
                or len(right_square_double_en) != len(right_square_double_zh)
        )  # 形如 [[ ]] [[

    @staticmethod
    def _is_different_event(line_zh: str, line_en: str):
        """<<link [[TEXT|EVENT]]>> 中 EVENT 打错了"""
        if "<<link [[" not in line_en or not line_zh:
            return False
        event_en = re.findall(r"<<link\s\[\[.*?\|(.*?)\]\]", line_en)
        if not event_en:
            return False
        event_zh = re.findall(r"<<link\s\[\[.*?\|(.*?)\]\]", line_zh)
        return event_en != event_zh

    @staticmethod
    def _is_full_notation_new(line_zh: str, line_en: str):
        """半全角打错了"""
        if "cn_name" in line_zh or "writ_cn" in line_zh:
            return False
        left_angle_double_en = re.findall(r'(",)', line_en)
        left_angle_double_zh = re.findall(r'(",)', line_zh)
        return len(left_angle_double_en) != len(left_angle_double_zh)

    @staticmethod
    def _is_lack_yin(line_zh: str, line_en: str):
        """缺少引号"""
        right_angle_double_en = re.findall(r'(")', line_en)
        right_angle_double_zh = re.findall(r'(")', line_zh)
        return (
            (len(right_angle_double_en) - len(right_angle_double_zh))%2 != 0
        )

    @staticmethod
    def _is_full_comma(line: str):
        """全角逗号"""
        return line.endswith('"，')

    @staticmethod
    def _is_full_notation(line_zh: str, line_en: str):
        """单双引号打错了"""
        if '",' in line_en and '”,' in line_zh:
            return True
        return ': "' in line_en and ': “' in line_zh

    @staticmethod
    def _is_lost_notation(line_zh: str, line_en: str):
        """漏了引号逗号"""
        if any(line_en.endswith(_) for _ in {"',", '",', "`,"}) and line_zh[-2:] != line_en[-2:]:
            return True
        return False

    async def get_lastest_commit(self) -> None:
        ref_name = self.get_type("master", "master", "dev")
        async with httpx.AsyncClient() as client:
            response = await client.get(REPOSITORY_COMMITS_URL_COMMON, params={"ref_name": ref_name})
            if response.status_code != 200:
                logger.error("获取源仓库 commit 出错！")
                return None
            repo_json = response.json()
        if not repo_json:
            return None
        latest_commit = repo_json[0]
        logger.info(f'latest commit: {latest_commit["id"]}')
        self._is_latest = bool(self._commit and latest_commit["id"] == self._commit["id"])
        if self._is_latest:
            return None
        logger.info(f"===== 开始写入{self._mention_name}最新 commit ...")
        with open(FILE_COMMITS, "w") as fp:
            json.dump(latest_commit, fp, ensure_ascii=False, indent=2)
            logger.info(f"#### {self._mention_name}最新 commit 已写入！")

    def get_type(self, common, world, dev):
        if self._type == "common":
            return common
        elif self._type == "world":
            return world
        else:
            return dev

    @property
    def game_dir(self) -> Path:
        """获得游戏目录"""
        return self.get_type(DIR_GAME_ROOT_COMMON, DIR_GAME_ROOT_WORLD, DIR_GAME_ROOT_DEV)

    """其他要修改的东西"""
    def change_css(self):
        """字体间距"""
        css_dir = DIR_GAME_CSS_COMMON if self._type == "common" else DIR_GAME_CSS_DEV
        with open(css_dir / "base.css", "r", encoding="utf-8") as fp:
            lines = fp.readlines()
        for idx, line in enumerate(lines):
            match line.strip():
                case "max-height: 2.4em;":
                    lines[idx] = line.replace("2.4em;", "7em;")
                    continue
                case 'content: " months";':
                    lines[idx] = line.replace(" months", "月数")
                    continue
                case 'content: " weeks";':
                    lines[idx] = line.replace(" weeks", "周数")
                    break
                case _:
                    continue
        with open(css_dir / "base.css", "w", encoding="utf-8") as fp:
            fp.writelines(lines)

    def replace_banner(self):
        """汉化版条幅"""
        shutil.copyfile(
            DIR_DATA_ROOT / "img" / "banner.png",
            DIR_GAME_ROOT_COMMON / "img" / "misc" / "banner.png"
        )

    def change_version(self, version: str = ""):
        """修改版本号"""
        if self._type == "world":
            with open(FILE_VERSION_EDIT_WORLD, "r", encoding="utf-8") as fp:
                lines = fp.readlines()
            for idx, line in enumerate(lines):
                if "version: " in line.strip():
                    lines[idx] = f'version: "{version}",\n'
                    break
            with open(FILE_VERSION_EDIT_WORLD, "w", encoding="utf-8") as fp:
                fp.writelines(lines)
        else:
            with open(FILE_VERSION_EDIT_COMMON, "r", encoding="utf-8") as fp:
                lines = fp.readlines()
            for idx, line in enumerate(lines):
                if "version: " in line.strip():
                    lines[idx] = f'version: "{version}",\n'
                    break
            with open(FILE_VERSION_EDIT_COMMON, "w", encoding="utf-8") as fp:
                fp.writelines(lines)

    """ 删删删 """
    async def drop_all_dirs(self, force=False):
        """恢复到最初时的样子"""
        if not force:
            await self.get_lastest_commit()
        logger.warning("===== 开始删库跑路 ...")
        await self._drop_temp()
        await self._drop_gitgud()
        await self._drop_dict()
        await self._drop_paratranz()
        logger.warning("##### 删库跑路完毕 !\n")
           
    async def _drop_temp(self):
        """删掉临时文件"""
        if DIR_TEMP_ROOT.exists():
            if not self._is_latest:
                shutil.rmtree(DIR_TEMP_ROOT, ignore_errors=True)
                return
            if FILE_REPOSITORY_ZIP.exists():
                with contextlib.suppress(shutil.Error, FileNotFoundError):
                    shutil.move(FILE_REPOSITORY_ZIP, DIR_ROOT)

            if (DIR_TEMP_ROOT / f"dol{self._mention_name}.zip").exists():
                with contextlib.suppress(shutil.Error, FileNotFoundError):
                    shutil.move(DIR_TEMP_ROOT / f"dol{self._mention_name}.zip", DIR_ROOT)

            if (DIR_TEMP_ROOT / "dol世扩.zip").exists():
                with contextlib.suppress(shutil.Error, FileNotFoundError):
                    shutil.move(DIR_TEMP_ROOT / "dol世扩.zip", DIR_ROOT)

            shutil.rmtree(DIR_TEMP_ROOT, ignore_errors=True)
        logger.warning("\t- 缓存目录已删除")

    async def _drop_gitgud(self):
        """删掉游戏库"""
        shutil.rmtree(self.game_dir, ignore_errors=True)
        logger.warning(f"\t- {self._mention_name}游戏目录已删除")

    async def _drop_dict(self):
        """删掉生成的字典"""
        if not self._version:
            await self.fetch_latest_version()
        shutil.rmtree(DIR_RAW_DICTS / self._type / self._version, ignore_errors=True)
        shutil.rmtree(DIR_RAW_DICTS / "common" / self._version, ignore_errors=True)
        logger.warning(f"\t- {self._mention_name}字典目录已删除")

    async def _drop_paratranz(self):
        """删掉下载的汉化包"""
        shutil.rmtree(DIR_PARATRANZ / self._type, ignore_errors=True)
        logger.warning(f"\t- {self._mention_name}汉化目录已删除")

    """ 编译游戏 """
    def compile(self, chs_version: str = ""):
        """编译游戏"""
        logger.info("===== 开始编译游戏 ...")
        # self._before_compile(chs_version)
        if platform.system() == "Windows":
            self._compile_for_windows()
        elif platform.system() == "Linux":
            self._compile_for_linux()
        else:
            raise Exception("什么电脑系统啊？")
        logger.info("##### 游戏编译完毕 !")

    def _before_compile(self, chs_version: str = ""):
        """修改一些编译设置"""
        with open(self.game_dir / "compile.bat", "r", encoding="utf-8") as fp:
            content = fp.read()
        content = content.replace("Degrees of Lewdity VERSION.html", "Degrees of Lewdity.html")
        with open(self.game_dir / "compile.bat", "w", encoding="utf-8") as fp:
            fp.write(content)

        with open(self.game_dir / "devTools" / "androidsdk" / "image" / "cordova" / "comfig.xml", "r", encoding="utf-8") as fp:
            lines = fp.readlines()
        for idx, line in enumerate(lines):
            if 'id="' in line:
                lines[idx] = 'id="dol-chs"\n'
                continue
            if 'version="' in line:
                lines[idx] = f'version="{chs_version}"\n'
                continue
            if 'android-packageName="' in line:
                lines[idx] = 'android-packageName="com.vrelnir.DegreesOfLewdityCHS"\n'
                continue
            if '<description>Degrees of Lewdity</description>' in line:
                lines[idx] = '<description>Degrees of Lewdity 汉化版</description>\n'
        with open(self.game_dir / "devTools" / "androidsdk" / "image" / "cordova" / "comfig.xml", "w", encoding="utf-8") as fp:
            fp.writelines(lines)

    def _compile_for_windows(self):
        """win"""
        subprocess.Popen(self.game_dir / "compile.bat")
        time.sleep(5)
        logger.info(f"\t- Windows 游戏编译完成，位于 {self.game_dir / 'Degrees of Lewdity VERSION.html'}")

    def _compile_for_linux(self):
        """linux"""
        if GITHUB_ACTION_DEV:
            tweego_exe = "tweego_linux86" if PLATFORM_ARCHITECTURE == "32bit" else "tweego_linux64"
            tweego_exe_file = self.game_dir / "devTools" / "tweego" / tweego_exe
            tweego_exe_file.chmod(tweego_exe_file.stat().st_mode | stat.S_IEXEC)
            tweego_compile_sh = self.game_dir / "compile.sh"
            tweego_compile_sh.chmod(tweego_compile_sh.stat().st_mode | stat.S_IEXEC)
        subprocess.Popen("bash ./compile.sh", env=os.environ, shell=True, cwd=self.game_dir)
        time.sleep(5)
        logger.info(f"\t- Linux 游戏编译完成，位于 {self.game_dir / 'Degrees of Lewdity VERSION.html'}")

    def _compile_for_mobile(self):
        """android"""

    """ 打包游戏 """
    def package_zip(self, chs_version: str = "chs"):
        """ 打包游戏 """
        today = datetime.datetime.now().strftime("%Y%m%d")
        with open(DIR_GAME_ROOT_COMMON / "version", "r", encoding="utf-8") as fp:
            version = fp.read()
        with zf(DIR_GAME_ROOT_COMMON / f"dol-{chs_version}-{today}.zip", "w", compresslevel=9, compression=ZIP_DEFLATED) as zfp:
            for root, dir_list, file_list in os.walk(DIR_GAME_ROOT_COMMON):
                for file in file_list:
                    filepath = Path((Path(root) / file).__str__().split("degrees-of-lewdity-master/")[-1].split("degrees-of-lewdity-master\\")[-1])
                    if (file in {
                            "Degrees of Lewdity VERSION.html",
                            "style.css",
                        }
                        or "degrees-of-lewdity-master/img/" in root
                        or "degrees-of-lewdity-master\\img\\" in root
                        or filepath == Path("LICENSE")
                    ):
                        zfp.write(filename=DIR_GAME_ROOT_COMMON / filepath, arcname=filepath, compresslevel=9)

    async def copy_to_git(self):
        """复制到git"""
        git_repo = os.getenv("GIT_REPO")
        dol_chinese_path = DIR_ROOT / git_repo
        if not dol_chinese_path.exists():
            logger.warning(f"不存在{git_repo}文件夹")
            return

        logger.info("===== 开始复制到 git ...")
        game_dir_path = self.game_dir
        game_dir = os.listdir(game_dir_path)

        logger.info(f"game_dir: {game_dir}")
        for file in game_dir:
            if file.startswith("Degrees of Lewdity") and file.endswith("html"):
                dol_html = "beta" if GITHUB_ACTION_ISBETA else "index"
                game_html = game_dir_path / file
                logger.info("复制到GIT文件夹")
                shutil.copyfile(
                    game_html,
                    dol_chinese_path / f"{dol_html}.html",
                )
                beeesssmod_dir_path =dol_chinese_path / "beeesssmod"
                beeesssmod_dir = Path(beeesssmod_dir_path)
                if beeesssmod_dir.is_dir():
                    logger.info("同步到美化包文件夹")
                    shutil.copyfile(
                        game_html,
                        beeesssmod_dir_path / f"{dol_html}.html",
                    )

            elif file in {"style.css", "DolSettingsExport.json"}:
                logger.info(f"game_dir file: {file}")
                shutil.copyfile(
                    game_dir_path / file,
                    dol_chinese_path / file,
                )
        dol_chinese_img_path = dol_chinese_path / "img"


        shutil.copytree(
            self.game_dir / "img",
            dol_chinese_img_path,
            True,
            ignore=lambda src,files: [f for f in files if f.endswith(".js") or f.endswith(".bat")],
            dirs_exist_ok=True,
        )
        logger.info("##### 复制到 git 已完毕! ")
        await self.drop_all_dirs(True)

    """ 在浏览器中启动 """
    def run(self):
        webbrowser.open((self.game_dir / "Degrees of Lewdity VERSION.html").__str__())

    """ i18n 相关"""
    async def download_modloader_autobuild(self):
        async with httpx.AsyncClient() as client:
            await self._get_latest_modloader_autobuild(client)

    async def _get_latest_modloader_autobuild(self, client: httpx.AsyncClient):
        response = await client.get(REPOSITORY_MODLOADER_ARTIFACTS)
        url = response.json()["artifacts"][0]["archive_download_url"]

        logger.info(f"url: {url}")
        async with client.stream("GET", url, headers={
            "accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_ACCESS_TOKEN}"
        }, follow_redirects=True, timeout=60) as response:
            async with aopen(DIR_TEMP_ROOT / "modloader.zip", "wb+") as afp:
                async for char in response.iter_raw():
                    await afp.write(char)



        # response = await client.get(url, headers={
        #     "accept": "application/vnd.github+json",
        #     "Authorization": f"Bearer {GITHUB_ACCESS_TOKEN}"
        # }, follow_redirects=True, timeout=60)
        # logger.info(f"status: {response.status_code}")
        # with open(DIR_TEMP_ROOT / "modloader.zip", "wb") as fp:
        #     fp.write(response.content)


__all__ = [
    "ProjectDOL"
]
