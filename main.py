"""
基本种类:
:: EVENT [WIDGET]      | 一般在文件开头

<<WIDGET_1>>ANY<</WIDGET_1>>   | 有闭合的
<<WIDGET_0>>                | 无闭合的
<<WIDGET "TAG">>            | 特殊名称
<<WIDGET COND>>             | 条件，如 if / link 等

特殊:
<<if>>ANY<<elseif>>ANY<<else>>ANY<</if>>
<<switch>>ANY<<case>>ANY<</switch>>
<<link [[TEXT]]>>
<<link [[TEXT|EVENT]]>>

$VAR                | 变量
$VAR.FUNC(PARAM)    | 调用函数
$VAR.PROP           | 属性

STRING                  | 文本
<CHAR_1>ANY</CHAR_1>    | 有闭合的
<CHAR_0>                | 无闭合的

//COMMENT       | 注释
/*COMMENT*/     | 注释
<!--COMMENT-->  | 注释

要翻译的：
TEXT, STRING
"""

import asyncio
import contextlib
import csv
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List
import webbrowser
from zipfile import ZipFile

import httpx
from aiofiles import open as aopen, os as aos

from consts import *
from log import logger
import time


async def divide_chunks(filesize: int, chunk: int = 2) -> List[List[int]]:
    """给大文件切片"""
    step = filesize // chunk
    arr = range(0, filesize, step)
    result = [
        [arr[i], arr[i + 1] - 1]
        for i in range(len(arr) - 1)
    ]
    result[-1][-1] = filesize - 1
    # logger.info(f"chunks: {result}")
    return result


async def chunk_download(url: str, client: httpx.AsyncClient, start: int, end: int, idx: int, full: int, save_path: Path):
    """切片下载"""
    if not save_path.exists():
        async with aopen(save_path, "wb") as fp:
            ...
    headers = {"Range": f"bytes={start}-{end}"}
    response = await client.get(url, headers=headers, follow_redirects=True)
    async with aopen(save_path, "rb+") as fp:
        await fp.seek(start)
        await fp.write(response.content)
        logger.info(f"\t- 切片 {idx + 1} / {full} 已下载")


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
        await aos.makedirs(DIR_RAW_DICTS / version / "json", exist_ok=True)
        await aos.makedirs(DIR_RAW_DICTS / version / "csv", exist_ok=True)
        await aos.makedirs(DIR_FINE_DICTS, exist_ok=True)

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
            # logger.info(f"headers: {response.headers}")
            filesize = int(response.headers["Content-Length"])
            chunks = await divide_chunks(filesize, 64)

            tasks = [
                chunk_download(zip_url, client, start, end, idx, len(chunks), FILE_REPOSITORY_ZIP)
                for idx, (start, end) in enumerate(chunks)
            ]
            await asyncio.gather(*tasks)
            # response = await client.get(zip_url)
            # async with aopen(FILE_REPOSITORY_ZIP, "wb") as fp:
            #     await fp.write(response.content)
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
        for file in self._game_texts_file_lists:
            target_dir = (file.parent.__str__()).split("degrees-of-lewdity-master\\")[1]
            # target_dir_json = DIR_RAW_DICTS / self._version / "json" / target_dir
            target_dir_csv = DIR_RAW_DICTS / self._version / "csv" / target_dir
            if not target_dir_csv.exists():
                # await aos.makedirs(target_dir_json, exist_ok=True)
                await aos.makedirs(target_dir_csv, exist_ok=True)

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
        # results_lines_json = [
        #     {
        #         "key": f"{idx_ + 1}_{'_'.join(self._version.split('.'))}",
        #         "original": _.strip(),
        #         "translation": ""
        #     } for idx_, _ in enumerate(lines) if able_lines[idx_]
        # ]
        results_lines_csv = [
            (f"{idx_ + 1}_{'_'.join(self._version.split('.'))}", _.strip()) for idx_, _ in enumerate(lines) if
            able_lines[idx_]
        ]
        # with open(DIR_RAW_DICTS / self._version / "json" / "game" / f"{target_file}.json", "w", encoding="utf-8") as fp:
        #     json.dump(results_lines_json, fp, ensure_ascii=False, indent=2)
        with open(DIR_RAW_DICTS / self._version / "csv" / "game" / f"{target_file}.csv", "w", encoding="utf-8",
                  newline="") as fp:
            csv.writer(fp).writerows(results_lines_csv)
        # logger.info(f"\t- ({idx + 1} / {len(self._game_texts_file_lists)}) {target_file} 处理完毕")

    async def _match_rules(self, file: Path):
        """匹配规则"""
        return next((v for k, v in self._rules.items() if k in file.name), None)

    """更新字典"""
    async def update_dicts(self):
        """更新字典"""
        logger.info("===== 开始更新字典 ...")
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
        with open(old_file, "r", encoding="utf-8") as fp:
            old_data: List = list(csv.reader(fp))
        old_ens: dict = {
            row[-2] if len(row) > 2 else row[1]: idx_
            for idx_, row in enumerate(old_data)
        }  # 旧英文: 旧英文行键

        with open(new_file, "r", encoding="utf-8") as fp:
            new_data: List = list(csv.reader(fp))

        for idx_, row in enumerate(new_data):
            if row[-1] in old_ens:
                new_data[idx_][0] = self.process_bad_key(old_data[old_ens[row[-1]]][0])
                if len(old_data[old_ens[row[-1]]]) >= 3:
                    new_data[idx_].append(old_data[old_ens[row[-1]]][-1].strip())

        with open(new_file, "w", encoding="utf-8", newline="") as fp:
            csv.writer(fp).writerows(new_data)
        # logger.info(f"\t- ({idx + 1} / {full}) {new_file.__str__().split('game')[1]} 更新完毕")

    @staticmethod
    def process_bad_key(key: str):
        """有些行键因为不知道什么原因有些乱七八糟的字符"""
        if "﻿" in key:
            key = key.replace("﻿", "", -1).strip()
        if " " in key:
            key = key.replace(" ", "", -1).strip()
        if "," in key:
            key = key.split(",")[0].strip()
        if "|" in key:
            key = key.replace("|", "")
        return key.strip()

    """应用字典"""
    async def apply_dicts(self, blacklist_dirs: List[str] = None, blacklist_files: List[str] = None):
        """汉化覆写游戏文件"""
        DIR_GAME_TEXTS = DIR_GAME_TEXTS_COMMON if self._type == "common" else DIR_GAME_TEXTS_DEV
        logger.info("===== 开始覆写汉化 ...")
        file_mapping: dict = {}
        for root, dir_list, file_list in os.walk(DIR_PARATRANZ / "utf8"):
            # if blacklist_dirs and any(_ in root for _ in blacklist_dirs):
            #     continue
            if "失效词条" in root:
                continue
            for file in file_list:
                # if blacklist_files and f"{file.split('.')[0]}.twee" in blacklist_files:
                #     continue
                file_mapping[Path(root).absolute() / file] = DIR_GAME_TEXTS / Path(root).relative_to(DIR_PARATRANZ / "utf8") / f"{file.split('.')[0]}.twee"

        tasks = [
            self._apply_for_gather(file, target_file, idx, len(file_mapping))
            for idx, (file, target_file) in enumerate(file_mapping.items())
        ]
        await asyncio.gather(*tasks)
        logger.info("##### 汉化覆写完毕 !\n")

    @staticmethod
    async def _apply_for_gather(file: Path, target_file: Path, idx: int, full: int):
        """gather 用"""
        with open(target_file, "r", encoding="utf-8") as fp:
            raw_targets: List[str] = fp.readlines()
        with open(file, "r", encoding="utf-8") as fp:
            reader = csv.reader(fp)
            for row in reader:
                en, zh = row[-2:]
                for idx_, target_row in enumerate(raw_targets):
                    if en == target_row.strip() and zh.strip():
                        raw_targets[idx_] = target_row.replace(en, zh)
                        break
        with open(target_file, "w", encoding="utf-8") as fp:
            fp.writelines(raw_targets)
        # logger.info(f"\t- ({idx + 1} / {full}) {target_file.__str__().split('game')[1]} 覆写完毕")

    """ 删删删 """
    async def drop_all_dirs(self):
        """恢复到最初时的样子"""
        logger.warning("===== 开始删库跑路 ...")
        await self._drop_game()
        await self._drop_dict()
        await self._drop_paratranz()
        logger.warning("##### 删库跑路完毕 !\n")

    async def _drop_game(self):
        """删掉游戏库"""
        game_dir = DIR_GAME_ROOT_COMMON if self._type == "common" else DIR_GAME_ROOT_DEV
        shutil.rmtree(game_dir, ignore_errors=True)
        logger.warning("\t- 游戏目录已删除")

    async def _drop_dict(self):
        """删掉生成的字典"""
        shutil.rmtree(DIR_RAW_DICTS, ignore_errors=True)
        logger.info("\t- 字典目录已删除")

    async def _drop_paratranz(self):
        """删掉下载的汉化包"""
        shutil.rmtree(DIR_PARATRANZ, ignore_errors=True)
        logger.info("\t- 汉化目录已删除")

    """ 编译游戏 """
    def compile(self):
        """编译游戏"""
        logger.info("===== 开始编译游戏 ...")
        self._compile_for_windows()
        logger.info("##### 游戏编译完毕 !")

    def _compile_for_windows(self):
        """win"""
        subprocess.Popen(DIR_GAME_ROOT_COMMON / "compile.bat")
        time.sleep(5)
        logger.info("\t- Windows 游戏编译完成")

    def _compile_for_linux(self):
        """linux"""

    def _compile_for_mobile(self):
        """android"""

    """ 在浏览器中启动 """
    def run(self):
        webbrowser.open(DIR_GAME_ROOT_COMMON / "Degrees of Lewdity VERSION.html")


class ParseText:
    """提取出要翻译的文本"""

    def __init__(self):
        self._high_rates: List[str] = ...
        self._type: str = ...
        self._lines: List[str] = ...

    async def async_init(self, lines: List[str], type_: str = None, high_rates: List[str] = None) -> "ParseText":
        self._lines = lines
        self._type = type_
        self._high_rates = high_rates
        return self

    async def parse(self) -> List[bool]:
        """导出要翻译的行"""
        if self._type == "cloth":
            return await self.parse_cloth()
        elif self._type == "plant":
            return await self.parse_plant()
        elif self._type == "trait":
            return await self.parse_trait()
        return await self.parse_normal()

    async def parse_cloth(self) -> List[bool]:
        """衣服"""
        return [
            "name_cap" in line.strip() or "description" in line.strip()
            for line in self._lines
        ]

    async def parse_plant(self) -> List[bool]:
        """种地"""
        return [
            "plural:" in line.strip()
            for line in self._lines
        ]

    async def parse_trait(self) -> List[bool]:
        """特性"""
        return [
            any((_ in line.strip() for _ in {"name:", "text:", "title:", "<summary", "<<option"}))
            for line in self._lines
        ]

    async def parse_option(self) -> List[bool]:
        """设置"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
            elif any((_ in line for _ in {"<<link", "<<option", "description", "<span class", "<div class"})):
                results.append(True)
            elif self.is_single_widget(line) or self.is_comment(line):
                results.append(False)
            else:
                results.append(True)
        return results

    async def parse_normal(self) -> List[bool]:
        """常规"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line or self.is_comment(line) or self.is_event(line) or self.is_only_marks(line) or ("[[" in line and self.is_high_rate_link(line)):
                results.append(False)
            elif "[[" in line or self.is_assignment(line) or self.is_option(line):
                results.append(True)
            elif self.is_single_widget(line) or self.is_half_widget(line):
                results.append(False)
            else:
                results.append(True)
        return results

    @staticmethod
    def is_high_rate_link(line: str) -> bool:
        """高频选项"""
        return bool(re.findall(r"<<link\s\[\[(Next)|(Leave)|(Refuse)|(Return)", line))

    @staticmethod
    def is_only_marks(line: str) -> bool:
        """只有符号没字母数字"""
        return not any(re.findall(r"([A-z\d]*)", line))

    @staticmethod
    def is_event(line: str) -> bool:
        """事件"""
        return line.startswith("::")

    @staticmethod
    def is_comment(line: str) -> bool:
        """注释"""
        return any(line.startswith(_) for _ in {"//", "/*", "<!--", "*/", "*"})

    @staticmethod
    def is_assignment(line: str) -> bool:
        """专指 <<set>> 可能出现的特殊情况"""
        set_to = re.findall(r'<<set.*?to\s\"', line)
        return bool(set_to)

    @staticmethod
    def is_option(line: str) -> bool:
        """专指 <<option>> 可能出现的特殊情况"""
        set_to = re.findall(r'<<option\s\"', line)
        return bool(set_to)

    @staticmethod
    def is_single_widget(line: str) -> bool:
        """单独的 <<>>, <>, $VAR"""
        if ("<" not in line and "$" not in line) or '"' in line:
            return False

        widgets = {_ for _ in re.findall(r"(<<.*[^\[\n].*?>>)", line) if _}
        for w in widgets:
            line = line.replace(w, "", -1)

        if "<" not in line and "$" not in line:
            return (not line.strip()) or ParseText.is_comment(line.strip()) or False
        tags = {_ for _ in re.findall(r"(<[/\sA-z\"=]*>)", line) if _}
        for t in tags:
            line = line.replace(t, "", -1)

        if "$" not in line:
            return (not line.strip()) or ParseText.is_comment(line.strip()) or False

        vars_ = {_ for _ in re.findall(r"(\$[A-z])]", line) if _}
        for v in vars_:
            line = line.replace(v, "", -1)
        return (not line.strip()) or ParseText.is_comment(line.strip()) or False

    @staticmethod
    def is_half_widget(line: str) -> bool:
        """只有一半 <<, >>, <, >"""
        return any((
            "<<" in line and ">>" not in line,
            ">>" in line and "<<" not in line,
            "<" in line and ">" not in line,
            ">" in line and "<" not in line
        ))


class Paratranz:
    """下载汉化包相关"""

    @classmethod
    async def download_from_paratranz(cls):
        """从 paratranz 下载汉化包"""
        await aos.makedirs(DIR_PARATRANZ, exist_ok=True)
        with contextlib.suppress(httpx.TimeoutException):
            await cls.trigger_export()
        await cls.download_export()
        await cls.unzip_export()

    @classmethod
    async def trigger_export(cls):
        """触发导出"""
        logger.info("===== 开始导出汉化文件 ...")
        url = f"{PARATRANZ_BASE_URL}/projects/{PARATRANZ_PROJECT_ID}/artifacts"
        httpx.post(url, headers=PARATRANZ_HEADERS)
        logger.info("##### 汉化文件已导出 !\n")

    @classmethod
    async def download_export(cls):
        """下载文件"""
        logger.info("===== 开始下载汉化文件 ...")
        url = f"{PARATRANZ_BASE_URL}/projects/{PARATRANZ_PROJECT_ID}/artifacts/download"
        async with httpx.AsyncClient() as client:
            content = (await client.get(url, headers=PARATRANZ_HEADERS, follow_redirects=True)).content
            # logger.info(f"content: {content}")
        with open(FILE_PARATRANZ_ZIP, "wb") as fp:
            fp.write(content)
        #async with httpx.AsyncClient(timeout=60, headers=PARATRANZ_HEADERS) as client:
            #url = f"{PARATRANZ_BASE_URL}/projects/{PARATRANZ_PROJECT_ID}/artifacts/download"
            #filesize = int((await client.head(url, timeout=60, follow_redirects=True)).headers["Content-Length"])
            #chunks = await divide_chunks(filesize, 8)

            #tasks = [
                #chunk_download(url, client, start, end, idx, len(chunks), FILE_PARATRANZ_ZIP)
                #for idx, (start, end) in enumerate(chunks)
            #]
            #await asyncio.gather(*tasks)
        logger.info("##### 汉化文件已下载 !\n")

    @classmethod
    async def unzip_export(cls):
        """解压"""
        logger.info("===== 开始解压汉化文件 ...")
        with ZipFile(FILE_PARATRANZ_ZIP) as zfp:
            zfp.extractall(DIR_PARATRANZ)
        logger.info("##### 汉化文件已解压 !\n")


async def main():
    start = time.time()
    # =====
    dol = await ProjectDOL().async_init(type_="common")  # 改成 “dev” 则下载最新开发版分支的内容
    pt = Paratranz()

    """ 删库跑路 """
    await dol.drop_all_dirs()

    """ 获取最新版本 """
    await dol.fetch_latest_version()

    """ 提取键值 """
    await dol.download_from_gitgud()
    await dol.create_dicts()

    """ 更新导出的字典 """
    await pt.download_from_paratranz()  # 如果下载，需要在 consts 里填上管理员的 token, 在网站个人设置里找
    await dol.update_dicts()

    """ 覆写汉化 """
    await dol.apply_dicts()
    # error = []

    """ 编译成游戏 """
    dol.compile()
    dol.run()
    # =====
    end = time.time()
    return end-start


if __name__ == '__main__':
    last = asyncio.run(main())
    logger.info(f"===== 总耗时 {last}s =====")
 
