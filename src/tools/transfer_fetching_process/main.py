from pathlib import Path
from asyncio import gather as agather, run as arun

from src.consts import DIR_PARATRANZ


class TransferProcess:
    def __init__(self):
        self._dir_old_dict_root = DIR_PARATRANZ / "common" / "raw"  # 对应游戏的 game 目录，但是要排除掉失效词条和更新日志文件夹

    async def get_old_dict(self):
        """获取旧版键值对"""

    async def get_old_pos(self):
        """获取旧版起止位置"""

    async def get_new_dict(self):
        """获取新版键值对"""

    async def get_new_pos(self):
        """获取新版起止位置"""

    async def contrast_difference(self):
        """对比差异"""

    async def joint_dict(self):
        """拼接键值对"""


async def main():
    pass


if __name__ == '__main__':
    arun(main())
