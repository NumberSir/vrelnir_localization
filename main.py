import asyncio
import csv
import json
import os
import re
from pathlib import Path
from typing import List, Literal, Dict, Any
from zipfile import ZipFile

import httpx
from aiofiles import open as aopen, os as aos

from consts import *
from log import logger


class Localization:
    """本地化主类"""

    def __init__(self):
        self._rules: dict = None
        self._ignores: List[str] = None

        self._matched_rules: Dict[Path, Any] = None

    async def async_init(self) -> "Localization":
        await self.init_dirs()
        async with aopen(DIR_DATA_ROOT / "rules.json", "r", encoding="utf-8") as fp:
            self._rules = json.loads(await fp.read())
        async with aopen(DIR_DATA_ROOT / "ignores.json", "r", encoding="utf-8") as fp:
            self._ignores = json.loads(await fp.read())

        self._matched_rules = {}
        return self

    async def init_dirs(self, version: str):
        """创建目标文件夹"""
        await aos.makedirs(DIR_RAW_DICTS / version / "json", exist_ok=True)
        await aos.makedirs(DIR_RAW_DICTS / version / "csv", exist_ok=True)

    async def fetch_latest_repository(self):
        """获取最新仓库内容"""
        logger.info("===== 开始获取最新仓库内容 ...")
        async with httpx.AsyncClient() as client:
            response = await client.get("https://gitgud.io/Vrelnir/degrees-of-lewdity/-/raw/master/version")
            logger.info(f"当前仓库最新版本: {response.text}")
            await self.init_dirs(response.text)
            filesize = int((await client.head(REPOSITORY_ZIP_URL, timeout=60)).headers["Content-Length"])
            chunks = await self._divide_chunks(filesize)

            tasks = [
                self._chunk_download(client, start, end, idx, len(chunks))
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
        await self.create_all_text_files_dir(all_texts_files)
        await self.match_rules(all_texts_files)
        await self.process_texts()

    async def _fetch_all_text_files(self):
        """获取所有文本文件"""
        logger.info("===== 开始获取所有文本文件位置 ...")
        all_text_files = []
        for root, dir_list, file_list in os.walk(DIR_GAME_TEXTS):
            for file in file_list:
                if not file.endswith(SUFFIX_TEXTS):
                    continue
                if any(keyword in file for keyword in self._ignores):
                    logger.info(f"\t\t- 跳过 {Path(root).absolute() / file}")
                    continue
                all_text_files.append(Path(root).absolute() / file)
                logger.info(f"\t- {Path(root).absolute() / file}")
        logger.info("##### 所有文本文件位置已获取 !")
        return all_text_files

    async def create_all_text_files_dir(self, all_texts_files: List[Path]):
        """创建目录防报错"""
        for file in all_texts_files:
            target_dir = (file.parent.__str__()).split("degrees-of-lewdity-master\\")[1]
            target_dir_json = DIR_RAW_DICTS / "json" / target_dir
            target_dir_csv = DIR_RAW_DICTS / "csv" / target_dir
            if not target_dir_json.exists() or not target_dir_csv.exists():
                await aos.makedirs(target_dir_json, exist_ok=True)
                await aos.makedirs(target_dir_csv, exist_ok=True)

    async def match_rules(self, all_text_files: List[Path]):
        """获取要翻译的文本"""
        logger.info("===== 开始匹配文件对应的规则 ...")
        for file in all_text_files:
            file_name = file.name
            for k, rule in self._rules.items():
                if k in file_name:
                    self._matched_rules[file] = rule
                    logger.info(f"\t-  规则: {rule}\t|| 文件: {file}")
                    break
            else:
                self._matched_rules[file] = None
                logger.info(f"\t-  规则: {None}\t|| 文件: {file}")
        logger.info("===== 文件对应的规则已匹配! ")

    async def process_texts(self):
        """处理翻译文本为键值对"""
        logger.info("===== 开始处理翻译文本为键值对 ...")
        tasks = [
            self._process_for_gather(idx, file, rule)
            for idx, (file, rule) in enumerate(self._matched_rules.items())
        ]
        await asyncio.gather(*tasks)
        logger.info("===== 翻译文本已处理为键值对 ! ")

    async def _process_for_gather(self, idx: int, file: Path, rule: str):
        target_file = file.__str__().split("game\\")[1].replace(SUFFIX_TEXTS, "")

        async with aopen(file, "r", encoding="utf-8") as fp:
            lines = await fp.readlines()
        pr = await ProcessRules().async_init(type_=rule, lines=lines)
        able_lines = await pr.process()
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
        async with aopen(DIR_RAW_DICTS / "json" / "game" / f"{target_file}.json", "w",
                         encoding="utf-8") as fp:
            await fp.write(json.dumps(results_lines_json, ensure_ascii=False, indent=2))
        with open(DIR_RAW_DICTS / "csv" / "game" / f"{target_file}.csv", "w", encoding="utf-8",
                  newline="") as fp:
            csv.writer(fp).writerows(results_lines_csv)
        logger.info(f"\t- {target_file} 处理完毕 ({idx + 1} / {len(self._matched_rules)})")

    @staticmethod
    async def _divide_chunks(filesize: int, chunk: int = 32) -> List[List[int]]:
        """给大文件切片"""
        step = filesize // chunk
        arr = range(0, filesize, step)
        result = [
            [arr[i], arr[i + 1] - 1]
            for i in range(len(arr) - 1)
        ]
        result[-1][-1] = filesize - 1
        return result

    @staticmethod
    async def _chunk_download(client: httpx.AsyncClient, start: int, end: int, idx: int, full: int):
        """切片下载"""
        if not FILE_REPOSITORY_ZIP.exists():
            async with aopen(FILE_REPOSITORY_ZIP, "wb") as fp:
                pass
        headers = {"Range": f"bytes={start}-{end}"}
        response = await client.get(REPOSITORY_ZIP_URL, headers=headers)
        async with aopen(FILE_REPOSITORY_ZIP, "rb+") as fp:
            await fp.seek(start)
            await fp.write(response.content)
            logger.info(f"\t- 切片 {idx + 1} / {full} 已下载")


RuleType: Literal["cloth", "action", "option", "trait", "plant", None]


class ProcessRules:
    """根据不同的规则处理文本"""

    def __init__(self):
        self._lines = None
        self._type = None

    async def async_init(self, type_: "RuleType", lines: List[str]) -> "ProcessRules":
        self._type = type_
        self._lines = [line.strip() for line in lines]
        return self

    async def process(self):
        """处理文本"""
        if self._type == "cloth":
            return await self.process_cloth()
        elif self._type == "action":
            return await self.process_action()
        elif self._type == "option":
            return await self.process_option()
        elif self._type == "trait":
            return await self.process_trait()
        elif self._type == "plant":
            return await self.process_plant()
        else:
            return await self.process_normal()

    async def process_cloth(self) -> List[bool]:
        """衣物名称及描述 clothing-xxx.twee"""
        return [
            "name_cap" in line
            or "description" in line
            for line in self._lines
        ]

    async def process_action(self) -> List[bool]:
        """战斗行动/PC衣物状态/角色菜单 actions/actions-xxx.twee/captiontext.twee/characteristics.twee"""
        results = []
        for line in self._lines:
            if line == "<label>" or line == "</label>" or (">>" in line and "<<" not in line):
                results.append(False)
            elif "<<link" in line:
                results.append(
                    not bool(re.findall(
                        r'<<link\s\[\[(Next\|)|(Next\s\|)|(Next->)|(Leave\|)|(Refuse\|)|(Return\|)|(Return\s\|)', line))
                )
            elif line.startswith("<<set"):
                results.append(
                    bool(re.findall(r'set\s(_wearing)|(_finally)|(\$_pair)|(\$_a)\sto', line))
                    or
                    bool(re.findall(r'(\[\")|(\{\")|(_trimester)|(\$vaginaWetness)', line))
                )
            elif (
                    line.startswith('<<if _tentacle.shaft is')
                    and "_The _tentacle.fullDesc" not in line
            ):
                results.append(False)
            elif line.startswith("<<"):
                if line.endswith(">>") and (("_output" in line and "\"" in line) or "actionstentacleadvcheckbox" in line or "_tentacle.shaft" in line or "if !$player.inventory.sextoys" in line):
                    results.append(True)
                else:
                    results.append(False)
            elif line.startswith('<!--') and line.endswith('-->'):
                results.append(False)
            elif "$_pregnancyRisk" in line:
                results.append(True)
            elif line.startswith('::') or not line or line.endswith('*/') or "█" in line:
                results.append(False)
            elif "description" in line or "name :" in line or "preText:" in line or "$_number" in line or "$_verbIsPlural ?" in line or "<span class=\"" in line:
                results.append(True)
            elif "/*" in line or "div" in line or "<br>" in line:
                results.append(False)
            else:
                results.append(True)
        return results

    async def process_option(self) -> List[bool]:
        """选项菜单 options.twee"""
        results = []
        for line in self._lines:
            if "<<link" in line or "<<option" in line:
                results.append(True)
            # elif len(line) < 20:
            #     results.append(False)
            elif "description" in line or "<span class=\"" in line:
                results.append(True)
            elif line.startswith('<<') and line.endswith('>>'):
                results.append(False)
            elif "/*" in line or "*/" in line or not line or "<br>" in line:
                results.append(False)
            else:
                results.append(True)
        return results

    async def process_trait(self) -> List[bool]:
        """特质 traits.twee"""
        return [
            any((
                _ in line
                for _ in {
                "name:",
                "text:",
                "title:",
                "<summary",
                "<<option"
            }
            )) for line in self._lines
        ]

    async def process_plant(self) -> List[bool]:
        """植物"""
        return [
            "plural:" in line
            for line in self._lines
        ]

    async def process_normal(self) -> List[bool]:
        results = []
        for line in self._lines:
            if line.startswith('if') or line.startswith('<<if') or line.startswith('<</if') or line.startswith(
                    '<!--') or line == '<<print either(' or "<img" in line or ".render" in line:
                results.append(False)
            elif "{ name :" in line or "description:" in line or "preText:" in line or "_output" in line or "<<button" in line or "<span class=\"" in line:
                results.append(True)
            elif line.startswith('/*'):
                results.append(False)
            elif "<<link" in line:
                results.append(
                    not bool(re.findall(
                        r'<<link\s\[\[(Next\|)|(Next\s\|)|(Next->)|(Leave\|)|(Refuse\|)|(Return\|)|(Return\s\|)', line))
                )
            elif line.startswith('<'):
                if line.startswith('<<') and line.endswith('>>') and "<<note" not in line:
                    results.append(False)
                elif line.startswith('<<') and (line.endswith('*/') or line.endswith('-->') or line.endswith('[')):
                    results.append(False)
                elif line.startswith('<div') and not line.startswith('<div>') and not line.startswith(
                        '<div class="red">'):
                    results.append(False)
                elif "<br>" in line or line.startswith('</'):
                    results.append(False)
                else:
                    results.append(True)
            elif line.startswith('::') or not line or line.endswith('*/') or "█" in line:
                results.append(False)
            else:
                results.append(True)
        return results


async def main():
    ln = await Localization().async_init()
    await ln.fetch_latest_repository()
    await ln.unzip_latest_repository()
    await ln.init_dirs()
    await ln.create_dicts()


if __name__ == '__main__':
    asyncio.run(main())
