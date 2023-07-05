import csv
import re

from pathlib import Path
from typing import List, Dict,Any
from zipfile import ZipFile
from urllib.parse import quote

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

class ProjectDOL:
    """本地化主类"""

    def __init__(self, type_: str = "common"):
        with open(DIR_JSON_ROOT / "blacklists.json", "r", encoding="utf-8") as fp:
            self._blacklists: Dict[str, List] = json.load(fp)
        with open(DIR_JSON_ROOT / "whitelists.json", "r", encoding="utf-8") as fp:
            self._whitelists: Dict[str, List] = json.load(fp)
        self._type: str = type_
        self._version: str = None
        if FILE_COMMITS.exists():
            with open(FILE_COMMITS, "r", encoding="utf-8") as fp:
                self._commit: Dict[str, Any] = json.load(fp)
        else:
            self._commit = None
        self._is_latest = False
        self._paratranz_file_lists: List[Path] = None
        self._raw_dicts_file_lists: List[Path] = None
        self._game_texts_file_lists: List[Path] = None

    @staticmethod
    def _init_dirs(version: str):
        """创建目标文件夹"""
        os.makedirs(DIR_TEMP_ROOT, exist_ok=True)
        os.makedirs(DIR_RAW_DICTS / version / "csv", exist_ok=True)

    async def fetch_latest_version(self, is_quiet: bool = True):
        async with httpx.AsyncClient() as client:
            url = f"{REPOSITORY_URL_COMMON}/-/raw/master/version" if self._type == "common" else f"{REPOSITORY_URL_DEV}/-/raw/dev/version"
            response = await client.get(url)
            if not is_quiet:
                logger.info(f"当前仓库最新版本: {response.text}")
            self._version = response.text
        self._init_dirs(self._version)

    """生成字典"""
    async def download_from_gitgud(self):
        """从 gitgud 下载源仓库文件"""
        if not self._version:
            await self.fetch_latest_version()
        if self._is_latest:
            dol_path_zip = DIR_ROOT / "dol.zip"
            if dol_path_zip.exists():
                shutil.move(dol_path_zip, DIR_TEMP_ROOT)
                await self.unzip_latest_repository()
                return
        await self.fetch_latest_repository()
        await self.unzip_latest_repository()

    async def fetch_latest_repository(self):
        """获取最新仓库内容"""
        logger.info("===== 开始获取最新仓库内容 ...")
        async with httpx.AsyncClient() as client:
            zip_url = REPOSITORY_ZIP_URL_COMMON if self._type == "common" else REPOSITORY_ZIP_URL_DEV
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

        logger.info("##### 所有文本文件位置已获取 !\n")

    async def _create_all_text_files_dir(self):
        """创建目录防报错"""
        if not self._version:
            await self.fetch_latest_version()
        dir_name = DIR_GAME_ROOT_COMMON_NAME if self._type == "common" else DIR_GAME_ROOT_DEV_NAME
        for file in self._game_texts_file_lists:
            target_dir = file.parent.parts[file.parts.index(dir_name)+1:]
            target_dir_csv = (DIR_RAW_DICTS / self._version / "csv").joinpath(*target_dir)
            if not target_dir_csv.exists():
                os.makedirs(target_dir_csv, exist_ok=True)

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
        target_file = Path().joinpath(*file.parts[file.parts.index("game")+1:]).with_suffix("")

        with open(file, "r", encoding="utf-8") as fp:
            lines = fp.readlines()
        if file.name.endswith(SUFFIX_TWEE):
            pt = ParseTextTwee(lines, file)
        elif file.name.endswith(SUFFIX_JS):
            pt = ParseTextJS(lines, file)
            target_file = f"{target_file}.js"
        else:
            return
        able_lines = pt.parse()

        if not any(able_lines):
            logger.warning(f"\t- ***** 文件 {file} 无有效翻译行 !")
            return
        try:
            results_lines_csv = [
                (f"{idx_ + 1}_{'_'.join(self._version[2:].split('.'))}|", _.strip())
                for idx_, _ in enumerate(lines)
                if able_lines[idx_]
            ]
        except IndexError:
            logger.error(f"{file}")
            results_lines_csv = None
        if results_lines_csv:
            with open(DIR_RAW_DICTS / self._version / "csv" / "game" / f"{target_file}.csv", "w", encoding="utf-8-sig", newline="") as fp:
                csv.writer(fp).writerows(results_lines_csv)
        # logger.info(f"\t- ({idx + 1} / {len(self._game_texts_file_lists)}) {target_file} 处理完毕")

    """更新字典"""
    async def update_dicts(self):
        """更新字典"""
        if not self._version:
            await self.fetch_latest_version()
        logger.info("===== 开始更新字典 ...")
        # await self._create_unavailable_files_dir()
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
        if not new_file.exists():
            unavailable_file = DIR_RAW_DICTS / self._version / "csv" / "game" / "失效词条" / Path().joinpath(*old_file.parts[old_file.parts.index("utf8")+1:])
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
            if len(row) <= 2:  # 没翻译的，丢掉！
                continue

            if row[-2] == row[-1]:  # 不用翻译的，丢掉！
                continue

            old_en = row[-2]
            if old_en not in new_ens:
                # logger.info(f"\t- old: {old_en}")
                unavailables.append(old_data[idx_])
        unavailable_file = DIR_RAW_DICTS / self._version / "csv" / "game" / "失效词条" / os.path.join(*old_file.parts[1:]) if unavailables else None

        with open(new_file, "w", encoding="utf-8-sig", newline="") as fp:
            csv.writer(fp).writerows(new_data)

        if unavailable_file:
            os.makedirs(unavailable_file.parent, exist_ok=True)
            with open(unavailable_file, "w", encoding="utf-8-sig", newline="") as fp:
                csv.writer(fp).writerows(unavailables)

        # logger.info(f"\t- ({idx + 1} / {full}) {new_file.__str__().split('game')[1]} 更新完毕")

    """应用字典"""
    async def apply_dicts(self, blacklist_dirs: List[str] = None, blacklist_files: List[str] = None):
        """汉化覆写游戏文件"""
        if not self._version:
            await self.fetch_latest_version()
        DIR_GAME_TEXTS = DIR_GAME_TEXTS_COMMON if self._type == "common" else DIR_GAME_TEXTS_DEV
        logger.info("===== 开始覆写汉化 ...")
        file_mapping: dict = {}
        for root, dir_list, file_list in os.walk(DIR_RAW_DICTS / self._version / "csv"):
            if any(_ in root for _ in blacklist_dirs):
                continue
            if "失效词条" in root:
                continue
            for file in file_list:
                if all(_ not in file for _ in blacklist_files):
                    file_mapping[Path(root).absolute() / file] = (
                        DIR_GAME_TEXTS
                        / Path(root).relative_to(
                            DIR_RAW_DICTS / self._version / "csv" / "game"
                        )
                        / f"{file.split('.')[0]}.js"
                        if file.endswith(".js.csv")
                        else DIR_GAME_TEXTS
                        / Path(root).relative_to(
                            DIR_RAW_DICTS / self._version / "csv" / "game"
                        )
                        / f"{file.split('.')[0]}.twee"
                    )
        tasks = [
            self._apply_for_gather(csv_file, twee_file, idx, len(file_mapping))
            for idx, (csv_file, twee_file) in enumerate(file_mapping.items())
        ]
        await asyncio.gather(*tasks)
        logger.info("##### 汉化覆写完毕 !\n")

    async def _apply_for_gather(self, csv_file: Path, target_file: Path, idx: int, full: int):
        """gather 用"""
        vip_flag = target_file.name == "clothing-sets.twee"
        with open(target_file, "r", encoding="utf-8") as fp:
            raw_targets: List[str] = fp.readlines()
        raw_targets_temp = raw_targets.copy()

        with open(csv_file, "r", encoding="utf-8") as fp:
            for row in csv.reader(fp):
                if len(row) < 3 and not vip_flag:  # 没汉化
                    continue
                en, zh = row[-2:]
                en, zh = en.strip(), zh.strip()
                if not zh and not vip_flag:  # 没汉化/汉化为空
                    continue

                if self._is_full_comma(zh):
                    logger.warning(f"\t!!! 可能的全角逗号错误：{en} | {zh} | https://paratranz.cn/projects/4780/strings?text={quote(zh)}")
                if self._is_lack_angle(zh, en):
                    logger.warning(f"\t!!! 可能的尖括号数量错误：{en} | {zh} | https://paratranz.cn/projects/4780/strings?text={quote(zh)}")
                if self._is_different_event(zh, en):
                    logger.warning(f"\t!!! 可能的错译额外内容：{en} | {zh} | https://paratranz.cn/projects/4780/strings?text={quote(zh)}")
                if self._is_full_notation(zh, en):
                    logger.warning(f"\t!!! 可能的全角引号错误：{en} | {zh} | https://paratranz.cn/projects/4780/strings?text={quote(zh)}")

                for idx_, target_row in enumerate(raw_targets_temp):
                    if not target_row.strip():
                        continue

                    if "replace(/[^a-zA-Z 0-9.!()]" in target_row.strip():
                        raw_targets[idx_] = target_row.replace("replace(/[^a-zA-Z 0-9.!()]", "replace(/[^a-zA-Z\\u4e00-\\u9fa5 0-9.!()]")
                        continue
                    if en == target_row.strip():
                        raw_targets[idx_] = target_row.replace(en, zh)
                        if "<<print" in target_row and re.findall(r"<<print.*?\.writing>>", zh):
                            raw_targets[idx_] = raw_targets[idx_].replace("writing>>", "writ_cn>>")
                        elif "name_cap" not in target_row:
                            raw_targets_temp[idx_] = ""
                            continue

                        if "<<link " in target_row and re.findall(r"<<link.*?\.name_cap>>", zh):
                            raw_targets[idx_] = raw_targets[idx_].replace("name_cap>>", "cn_name_cap>>")
                        elif "<<clothingicon" in target_row and re.findall(r"<<clothingicon.*?\.name_cap", zh):
                            raw_targets[idx_] = raw_targets[idx_].replace("name_cap", "cn_name_cap")
                        raw_targets_temp[idx_] = ""
                        
                    elif "<" in target_row:
                        if "<<link [[" in target_row and re.findall(r"<<link \[\[(Next->|Next\s->|Next\||Next\s\||Leave\||Refuse\||Return\|Resume\||Confirm\||Continue\||Stop\|)", target_row):  # 高频词
                            raw_targets[idx_] = target_row\
                                .replace("[[Next", "[[继续")\
                                .replace("[[Leave", "[[离开")\
                                .replace("[[Refuse", "[[拒绝")\
                                .replace("[[Return", "[[返回")\
                                .replace("[[Resume", "[[返回")\
                                .replace("[[Confirm", "[[确认")\
                                .replace("[[Continue", "[[继续")\
                                .replace("[[Stop", "[[停止")
                        elif "<<print" in target_row and re.findall(r"<<print.*?\.writing>>", target_row):
                            raw_targets[idx_] = raw_targets[idx_].replace("writing>>", "writ_cn>>")
                        elif "name_cap" not in target_row:
                            continue

                        if "<<link " in target_row and re.findall(r"<<link.*?\.name_cap>>", target_row):
                            raw_targets[idx_] = raw_targets[idx_].replace("name_cap>>", "cn_name_cap>>")
                        elif "<<clothingicon" in target_row and re.findall(r"<<clothingicon.*?\.name_cap", target_row):
                            raw_targets[idx_] = raw_targets[idx_].replace("name_cap", "cn_name_cap")
                    elif target_row.strip() == "].select($_rng)>>":  # 怪东西
                        raw_targets[idx_] = ""
                # else:
                #     logger.warning(f"\t!!! 找不到替换的行: {zh} | {csv_file.relative_to(DIR_RAW_DICTS / self._version / 'csv' / 'game')}")
        with open(target_file, "w", encoding="utf-8") as fp:
            fp.writelines(raw_targets)
        # logger.info(f"\t- ({idx + 1} / {full}) {target_file.__str__().split('game')[1]} 覆写完毕")

    @staticmethod
    def _is_full_comma(line: str):
        """全角逗号"""
        return line.endswith('"，')

    @staticmethod
    def _is_lack_angle(line_zh: str, line_en: str):
        """<<> 缺一个 >"""
        if ("<" not in line_en and ">" not in line_en) or ParseTextTwee.is_only_marks(line_en):
            return False

        left_angle_single_zh = re.findall(r"[^<>=](<|>)[^<>=]", line_zh)
        right_angle_single_zh = re.findall(r"[^<>=](<|>)[^<>=]", line_zh)
        if "<<" not in line_en and ">>" not in line_en:
            if len(left_angle_single_zh) == len(right_angle_single_zh):
                return False
            left_angle_single_en = re.findall(r"[^<>=](<|>)[^<>=]", line_en)
            right_angle_single_en = re.findall(r"[^<>=](<|>)[^<>=]", line_en)
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
    def _is_different_event(line_zh: str, line_en: str):
        """<<link [[TEXT|EVENT]]>> 中 EVENT 打错了"""
        if "<<link [[" not in line_en or "|" not in line_en or not line_zh:
            return False
        event_en = re.findall(r"<<link\s\[\[.*?\|(.*?)\]\]", line_en)
        if not event_en:
            return False
        event_zh = re.findall(r"<<link\s\[\[.*?\|(.*?)\]\]", line_zh)
        return event_en != event_zh

    @staticmethod
    def _is_full_notation(line_zh: str, line_en: str):
        """单双引号打错了"""
        if '",' in line_en and '”,' in line_zh:
            return True
        return ': "' in line_en and ': “' in line_zh

    """ 删删删 """
    async def drop_all_dirs(self, force = False):
        """恢复到最初时的样子"""
        if not force:
            await self.get_lastest_commit()
        logger.warning("===== 开始删库跑路 ...")
        await self._drop_temp()
        await self._drop_gitgud()
        await self._drop_dict()
        await self._drop_paratranz()
        logger.warning("##### 删库跑路完毕 !\n")

    async def get_lastest_commit(self) -> None:
        ref_name = self.get_type("master", "dev")
        async with httpx.AsyncClient() as client:
            response = await client.get(REPOSITORY_URL_COMMITS, params = {"ref_name": ref_name})
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
        logger.info("===== 开始写入最新 commit ...")
        with open(FILE_COMMITS, "w") as fp:
            json.dump(latest_commit, fp, ensure_ascii=False, indent=2)
            logger.info("#### 最新 commit 已写入！")
           
    async def _drop_temp(self):
        """删掉临时文件"""
        if DIR_TEMP_ROOT.exists():
            if not self._is_latest:
                shutil.rmtree(DIR_TEMP_ROOT, ignore_errors=True)
                return
            if not FILE_REPOSITORY_ZIP.exists():
                return
            shutil.move(FILE_REPOSITORY_ZIP, DIR_ROOT) # type: ignore
            shutil.rmtree(DIR_TEMP_ROOT, ignore_errors=True)
        logger.warning("\t- 缓存目录已删除")

    def get_type(self, common, dev):
        return common if self._type == "common" else dev

    @property
    def game_dir(self) -> Path:
        """获得游戏目录"""
        return self.get_type(DIR_GAME_ROOT_COMMON, DIR_GAME_ROOT_DEV)

    async def _drop_gitgud(self):
        """删掉游戏库"""
        shutil.rmtree(self.game_dir, ignore_errors=True)
        logger.warning("\t- 游戏目录已删除")

    async def _drop_dict(self):
        """删掉生成的字典"""
        if not self._version:
            await self.fetch_latest_version()
        shutil.rmtree(DIR_RAW_DICTS / self._version, ignore_errors=True)
        logger.warning("\t- 字典目录已删除")

    async def _drop_paratranz(self):
        """删掉下载的汉化包"""
        shutil.rmtree(DIR_PARATRANZ, ignore_errors=True)
        logger.warning("\t- 汉化目录已删除")

    """ 编译游戏 """
    def compile(self):
        """编译游戏"""
        logger.info("===== 开始编译游戏 ...")
        if platform.system() == "Windows":
            self._compile_for_windows()
        elif platform.system() == "Linux":
            self._compile_for_linux()
        else:
            raise Exception("什么电脑系统啊？")
        logger.info("##### 游戏编译完毕 !")

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
                logger.info("同步到GIT文件夹")
                shutil.copyfile(
                    game_html,
                    dol_chinese_path / f"{dol_html}.html",
                )
                beeesssmod_dir = dol_chinese_path / "beeesssmod"
                if beeesssmod_dir.exists():
                    logger.info("同步到美化包文件夹")
                    shutil.copyfile(
                        game_html,
                        beeesssmod_dir / f"{dol_html}.html",
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


__all__ = [
    "ProjectDOL"
]
