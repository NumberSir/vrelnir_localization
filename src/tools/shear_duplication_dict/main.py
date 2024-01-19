import json
from asyncio import run, gather
from aiofiles import open as aopen
from pathlib import Path
import os

from src.consts import DIR_PARATRANZ, DIR_RAW_DICTS


VERSION = "0.4.5.3"


class ShearDuplication:
    def __init__(self):
        self._dir_raw_dict_needed_to_be_sheared = DIR_PARATRANZ / "common" / "raw"  # 对应游戏的 game 目录，但是要排除掉失效词条和更新日志文件夹
        self._dir_raw_dict_base = DIR_RAW_DICTS / "common" / VERSION / "json" / "game"


    def get_maybe_duplicated_filelist(self) -> list[tuple[Path, Path]]:
        """获取可能有重复词条的文件相对路径"""
        maybe_target_relative_filepath = []
        for root, dir_list, file_list in os.walk(self._dir_raw_dict_needed_to_be_sheared):
            if "失效词条" in root or "更新日志" in root:
                continue

            for file in file_list:
                absolute_filepath = Path(root) / file
                relative_filepath = absolute_filepath.relative_to(self._dir_raw_dict_needed_to_be_sheared)

                relative_filepath_without_csv = Path(relative_filepath.__str__().replace(".csv", ""))
                base_filepath = self._dir_raw_dict_base / relative_filepath_without_csv
                if base_filepath.exists():
                    maybe_target_relative_filepath.append((relative_filepath, relative_filepath_without_csv))
        return maybe_target_relative_filepath

    async def get_duplicated_content(self, filepath_list: list[tuple[Path, Path]]):
        """获取重复内容"""
        tasks = {
            self._contrast(
                self._dir_raw_dict_needed_to_be_sheared / filepath,
                self._dir_raw_dict_base / filepath_without_csv,
            )
            for filepath, filepath_without_csv in filepath_list
        }
        await gather(*tasks)

    async def _contrast(self, filepath_needed_to_be_sheared: Path, filepath_base: Path):
        async with aopen(filepath_needed_to_be_sheared, "r", encoding="utf-8") as fp:
            content_available = await fp.read()

        async with aopen(filepath_base, "r", encoding="utf-8") as fp:
            content_unavailable = await fp.read()

        data_needed_to_be_sheared = json.loads(content_available)
        data_base = json.loads(content_unavailable)

        original_base = [_["original"] for _ in data_base]
        for data in data_needed_to_be_sheared:
            if data["original"] not in original_base:
                print(data["original"])


async def main():
    shear = ShearDuplication()
    filepath_list = shear.get_maybe_duplicated_filelist()
    await shear.get_duplicated_content(filepath_list)


if __name__ == '__main__':
    run(main())
