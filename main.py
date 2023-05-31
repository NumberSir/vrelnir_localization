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
from pathlib import Path
from typing import List
from zipfile import ZipFile

import httpx
from aiofiles import open as aopen, os as aos

from consts import *
from log import logger


async def divide_chunks(filesize: int, chunk: int = 32) -> List[List[int]]:
    """给大文件切片"""
    step = filesize // chunk
    arr = range(0, filesize, step)
    result = [
        [arr[i], arr[i + 1] - 1]
        for i in range(len(arr) - 1)
    ]
    result[-1][-1] = filesize - 1
    return result


async def chunk_download(url: str, client: httpx.AsyncClient, start: int, end: int, idx: int, full: int, save_path: Path):
    """切片下载"""
    if not save_path.exists():
        async with aopen(save_path, "wb") as fp:
            pass
    headers = {"Range": f"bytes={start}-{end}"}
    response = await client.get(url, headers=headers)
    async with aopen(save_path, "rb+") as fp:
        await fp.seek(start)
        await fp.write(response.content)
        logger.info(f"\t- 切片 {idx + 1} / {full} 已下载")


class ProjectDOL:
    """本地化主类"""

    def __init__(self):
        self._type: str = None
        self._rules: dict = None
        self._ignores: List[str] = None
        self._version: str = None

    async def async_init(self, type_: str = "common") -> "ProjectDOL":
        async with aopen(DIR_DATA_ROOT / "rules.json", "r", encoding="utf-8") as fp:
            self._rules = json.loads(await fp.read())
        async with aopen(DIR_DATA_ROOT / "ignores.json", "r", encoding="utf-8") as fp:
            self._ignores = json.loads(await fp.read())
        self._type = type_
        return self

    async def _init_dirs(self, version: str):
        """创建目标文件夹"""
        await aos.makedirs(DIR_RAW_DICTS / version / "json", exist_ok=True)
        await aos.makedirs(DIR_RAW_DICTS / version / "csv", exist_ok=True)
        await aos.makedirs(DIR_FINE_DICTS, exist_ok=True)

    """生成字典"""
    async def fetch_latest_repository(self):
        """获取最新仓库内容"""
        logger.info("===== 开始获取最新仓库内容 ...")
        async with httpx.AsyncClient() as client:
            url = f"{REPOSITORY_URL_COMMON}/-/raw/master/version" if self._type == "common" else f"{REPOSITORY_URL_DEV}/-/raw/dev/version"
            response = await client.get(url)
            logger.info(f"当前仓库最新版本: {response.text}")
            self._version = response.text
            await self._init_dirs(self._version)
            zip_url = REPOSITORY_ZIP_URL_COMMON if self._type == "common" else REPOSITORY_ZIP_URL_DEV
            filesize = int((await client.head(zip_url, timeout=60)).headers["Content-Length"])
            chunks = await divide_chunks(filesize)

            tasks = [
                chunk_download(zip_url, client, start, end, idx, len(chunks), FILE_REPOSITORY_ZIP)
                for idx, (start, end) in enumerate(chunks)
            ]
            await asyncio.gather(*tasks)
        logger.info("##### 最新仓库内容已获取! ")

    async def unzip_latest_repository(self):
        """解压到本地"""
        logger.info("===== 开始解压最新仓库内容 ...")
        with ZipFile(FILE_REPOSITORY_ZIP) as zfp:
            zfp.extractall(DIR_ROOT)
        logger.info("##### 最新仓库内容已解压! ")

    async def create_dicts(self):
        """创建字典"""
        all_texts_files: List[Path] = await self._fetch_all_text_files()
        await self._create_all_text_files_dir(all_texts_files)
        await self._process_texts(all_texts_files)

    async def _fetch_all_text_files(self):
        """获取所有文本文件"""
        logger.info("===== 开始获取所有文本文件位置 ...")
        all_text_files = []
        texts_dir = DIR_GAME_TEXTS_COMMON if self._type == "common" else DIR_GAME_TEXTS_DEV
        for root, dir_list, file_list in os.walk(texts_dir):
            for file in file_list:
                if not file.endswith(SUFFIX_TEXTS):
                    continue
                if any(keyword in file for keyword in self._ignores):
                    logger.debug(f"\t\t- 跳过 {Path(root).absolute() / file}")
                    continue
                all_text_files.append(Path(root).absolute() / file)
                logger.debug(f"\t- {Path(root).absolute() / file}")
        logger.info("##### 所有文本文件位置已获取 !")
        return all_text_files

    async def _create_all_text_files_dir(self, all_texts_files: List[Path]):
        """创建目录防报错"""
        for file in all_texts_files:
            target_dir = (file.parent.__str__()).split("degrees-of-lewdity-master\\")[1]
            target_dir_json = DIR_RAW_DICTS / self._version / "json" / target_dir
            target_dir_csv = DIR_RAW_DICTS / self._version / "csv" / target_dir
            if not target_dir_json.exists() or not target_dir_csv.exists():
                await aos.makedirs(target_dir_json, exist_ok=True)
                await aos.makedirs(target_dir_csv, exist_ok=True)

    async def _process_texts(self, all_text_files: List[Path]):
        """处理翻译文本为键值对"""
        logger.info("===== 开始处理翻译文本为键值对 ...")
        tasks = [
            self._process_for_gather(idx, file, all_text_files)
            for idx, file in enumerate(all_text_files)
        ]
        await asyncio.gather(*tasks)
        logger.info("===== 翻译文本已处理为键值对 ! ")

    async def _process_for_gather(self, idx: int, file: Path, all_text_files: List[Path]):
        target_file = file.__str__().split("game\\")[1].replace(SUFFIX_TEXTS, "")

        async with aopen(file, "r", encoding="utf-8") as fp:
            lines = await fp.readlines()

        rule = await self._match_rules(file)
        pt = await ParseText().async_init(lines, rule)
        able_lines = await pt.parse()

        if not able_lines:
            logger.warning(f"\t- ***** 文件 {file} 无有效翻译行 !")
        results_lines_json = [
            {
                "key": idx_ + 1,
                "original": _.strip(),
                "translation": ""
            } for idx_, _ in enumerate(lines) if able_lines[idx_]
        ]
        results_lines_csv = [
            (idx_ + 1, _.strip()) for idx_, _ in enumerate(lines) if able_lines[idx_]
        ]
        with open(DIR_RAW_DICTS / self._version / "json" / "game" / f"{target_file}.json", "w", encoding="utf-8") as fp:
            json.dump(results_lines_json, fp, ensure_ascii=False, indent=2)
        with open(DIR_RAW_DICTS / self._version / "csv" / "game" / f"{target_file}.csv", "w", encoding="utf-8", newline="") as fp:
            csv.writer(fp).writerows(results_lines_csv)
        logger.info(f"\t- {target_file} 处理完毕 ({idx + 1} / {len(all_text_files)})")

    async def _match_rules(self, file: Path):
        """匹配规则"""
        return next((v for k, v in self._rules.items() if k in file.name), None)

    """更新字典"""
    async def update_dicts(self):
        """TODO 更新字典"""

    """应用字典"""
    async def apply_dicts(self):
        """导入字典"""
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
        logger.info("##### 汉化覆写完毕 !")

    async def _apply_for_gather(self, file: Path, target_file: Path, idx: int, full: int):
        """gather 用"""
        with open(target_file, "r", encoding="utf-8") as fp:
            raw_targets: List[str] = fp.readlines()
        with open(file, "r", encoding="utf-8") as fp:
            reader = csv.reader(fp)
            for row in reader:
                if len(row) < 3:
                    continue
                if len(row) == 3:
                    row, en, zh = row
                else:
                    row, _, en, zh = row
                if "﻿" in row or " " in row:
                    row = row.replace("﻿", "").replace(" ", "")
                if "_" in row:
                    row = row.split("_")[0]
                if "," in row:
                    row = row.split(",")[0]
                row = int(row.strip().replace(" ", "").replace('"', ""))
                with contextlib.suppress(IndexError):
                    raw_targets[row - 1] = raw_targets[row - 1].replace(en, zh)
        with open(target_file, "w", encoding="utf-8") as fp:
            fp.writelines(raw_targets)
        logger.info(f"\t- {target_file} 已应用汉化 ({idx} / {full})")


class ParseText:
    """提取出要翻译的文本"""
    def __init__(self):
        self._high_rates: List[str] = None
        self._type: str = None
        self._lines: List[str] = None

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
            if not line or self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif "[[" in line and self.is_high_rate_link(line):
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

        vars = {_ for _ in re.findall(r"(\$[A-z])]", line) if _}
        for v in vars:
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
        await aos.makedirs(DIR_PARATRANZ, exist_ok=True)
        await cls.trigger_export()
        await cls.download_export()
        await cls.unzip_export()

    @classmethod
    async def trigger_export(cls):
        """触发导出"""
        logger.info("===== 开始导出汉化文件 ...")
        url = f"{PARATRANZ_BASE_URL}/projects/{PARATRANZ_PROJECT_ID}/artifacts"
        httpx.post(url, headers=PARATRANZ_HEADERS)
        logger.info("##### 汉化文件已导出 !")

    @classmethod
    async def download_export(cls):
        """下载文件"""
        logger.info("===== 开始下载汉化文件 ...")
        async with httpx.AsyncClient() as client:
            url = f"{PARATRANZ_BASE_URL}/projects/{PARATRANZ_PROJECT_ID}/artifacts/download"
            filesize = int((await client.head(url)).headers["Content-Length"])
            chunks = await divide_chunks(filesize, 16)

            tasks = [
                chunk_download(url, client, start, end, idx, len(chunks), FILE_PARATRANZ_ZIP)
                for idx, (start, end) in enumerate(chunks)
            ]
            await asyncio.gather(*tasks)
        logger.info("##### 汉化文件已下载 !")

    @classmethod
    async def unzip_export(cls):
        """解压"""
        logger.info("===== 开始解压汉化文件 ...")
        with ZipFile(FILE_PARATRANZ_ZIP) as zfp:
            zfp.extractall(DIR_PARATRANZ)
        logger.info("##### 汉化文件已解压 !")


async def main():
    dol = await ProjectDOL().async_init(type_="common")  # 改成 “dev” 则下载最新开发版分支的内容
    pt = Paratranz()

    """ 下载解压源仓库 """
    await dol.fetch_latest_repository()
    await dol.unzip_latest_repository()

    """ 提取文字 """
    await dol.create_dicts()

    """ 应用已有字典 """
    await pt.download_from_paratranz()  # 如果下载，需要在 consts 里填上管理员的 token, 在网站个人设置里找
    await dol.apply_dicts()

    """ TODO 更新当前字典 """


if __name__ == '__main__':
    asyncio.run(main())
