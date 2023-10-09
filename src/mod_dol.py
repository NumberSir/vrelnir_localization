import asyncio
from pathlib import Path
from .consts import *
from .log import *
import json
import httpx
from .utils import chunk_split, chunk_download


from dataclasses import dataclass

@dataclass
class ModData:
    name: str = ""
    zh_name: str = ""
    type: str = ""
    project_id: int = -1
    author: str = ""
    url: str = ""
    main_branches: str = ""
    dev_branches: str = ""
    path: str | Path = ""
    output_file: str = ""


class ModDol:
    def __init__(self, json_: dict = None) -> None:
        self._data = ModData(**json_) if json_ else ModData()
        self.branch_json = {}

    async def get_lastest_commit(self, branch: str = "") -> dict | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.get_repository_branch_url(branch))
            if response.status_code != 200:
                logger.error("获取源仓库 commit 出错！")
                return None
            return response.json() or None

    async def get_lastest_archive(self, branch: str = "", format_: str = "zip"):
        """下载 mod 包"""
        last_commit = await self.get_lastest_commit(branch)
        if not last_commit:
            return
        archive_url = f"{self.repository_api_url}/archive.{format_}?sha={last_commit['commit']['id']}"
        if param_path := self.data.path:
            archive_url += f"&path={param_path}"
        logger.info(f"====开始下载{self.data.zh_name}")
        logger.info(f"下载地址{archive_url}")
        async with httpx.AsyncClient() as client:
            for _ in range(3):
                try:
                    response = await client.head(archive_url, timeout=60, follow_redirects=True)
                    filesize = int(response.headers["Content-Length"])
                    chunks = await chunk_split(filesize, 64)
                except (httpx.ConnectError, KeyError) as e:
                    continue
                else:
                    flag = True
                    break

            if not flag:
                logger.error(f"***** 无法正常下载最新mod {self.data.zh_name}！请检查你的网络连接是否正常！")
            tasks = [
                chunk_download(archive_url, client, start, end, idx, len(chunks), DIR_TEMP_ROOT / self.data.output_file)
                for idx, (start, end) in enumerate(chunks)
            ]
            await asyncio.gather(*tasks)
        logger.info(f"##### 最新mod {self.data.zh_name} 内容已获取! \n")

    @property
    def project_url_api_url(self):
        return (
            f"https://gitgud.io/api/v4/projects/{self.data.project_id}"
            if self.data.project_id > 0
            else None
        )

    @property
    def repository_api_url(self):
        return f"{self.project_url_api_url}/repository"

    @property
    def project_branches_api_url(self):
        return f"{self.repository_api_url}/branches"

    def get_repository_branch_url(self, branch: str = ""):
        branch = branch or self.data.main_branches
        return f"{self.project_branches_api_url}/{branch}"

    @property
    def data(self) -> "ModData":
        return self._data


__all__ = ["ModDol"]
