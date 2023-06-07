from aiofiles import os as aos, open as aopen
from zipfile import ZipFile

import contextlib
import httpx

from .consts import *
from .log import logger


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
        headers = PARATRANZ_HEADERS
        headers["User-Agent"] = "NSScript/1.0 (+https://github.com/NumberSir/vrelnir_localization)"
        async with httpx.AsyncClient() as client:
            content = (await client.get(url, headers=headers, follow_redirects=True)).content
        async with aopen(FILE_PARATRANZ_ZIP, "wb") as fp:
            await fp.write(content)
        logger.info("##### 汉化文件已下载 !\n")

    @classmethod
    async def unzip_export(cls):
        """解压"""
        logger.info("===== 开始解压汉化文件 ...")
        with ZipFile(FILE_PARATRANZ_ZIP) as zfp:
            zfp.extractall(DIR_PARATRANZ)
        logger.info("##### 汉化文件已解压 !\n")


__all__ = [
    "Paratranz"
]


if __name__ == '__main__':
    import asyncio
    asyncio.run(Paratranz.download_export())
