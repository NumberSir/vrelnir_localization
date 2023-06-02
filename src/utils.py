from aiofiles import open as aopen
from pathlib import Path
from typing import List
import httpx

from .log import logger

async def chunk_split(filesize: int, chunk: int = 2) -> List[List[int]]:
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


__all__ = [
    "chunk_split",
    "chunk_download"
]
