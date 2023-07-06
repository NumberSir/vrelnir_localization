from typing import Any, TypeVar
from .consts import *
from .log import *
import json
import httpx

MOD_DOL_DEFAULT = {
    "name": "",
    "zh_name": "",
    "type": "",
    "project_id": -1,
    "author": "",
    "url": "",
    "main_branches": "",
    "dev_branches": "",
    "path": "",
}


class ModDol:
    def __init__(self, json=None) -> None:
        self._data = (
            {
                "name": "",
                "zh_name": "",
                "type": "",
                "project_id": -1,
                "author": "",
                "url": "",
                "main_branches": "",
                "dev_branches": "",
                "path": "",
            }
            if not json
            else json
        )

    async def get_lastest_commit(self, branch=""):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.get_repository_branch_url(branch))
            if response.status_code != 200:
                logger.error("获取源仓库 commit 出错！")
                return None
            repo_json = response.json()
            if not repo_json:
                return None
            return repo_json

    @property
    def project_url_api_url(self):
        return (
            f"https://gitgud.io/api/v4/projects/{self.project_id}"
            if self.project_id > 0
            else None
        )

    @property
    def project_branches_api_url(self):
        url_api = self.project_url_api_url
        return f"{url_api}/repository/branches"

    def get_repository_branch_url(self, branch=""):
        brach = self.main_branches if not branch else branch
        return f"{self.project_branches_api_url}/{branch}"

    @property
    def data(self):
        return self._data

    @property
    def name(self) -> str:
        return self.getter_key("name")  # type: ignore

    @name.setter
    def name(self, value: str):
        self.setter_key("name", value)

    @property
    def zh_name(self) -> str:
        return self.getter_key("zh_name")  # type: ignore

    @zh_name.setter
    def zh_name(self, value: str):
        self.setter_key("zh_name", value)

    @property
    def type(self) -> str:
        return self.getter_key("type")  # type: ignore

    @type.setter
    def type(self, value: str):
        self.setter_key("type", value)

    @property
    def project_id(self) -> int:
        return self.getter_key("project_id")  # type: ignore

    @project_id.setter
    def project_id(self, value: int):
        self.setter_key("project_id", value)

    @property
    def author(self) -> str:
        return self.getter_key("author")  # type: ignore

    @author.setter
    def author(self, value: str):
        self.setter_key("author", value)

    @property
    def url(self) -> str:
        return self.getter_key("url")  # type: ignore

    @url.setter
    def url(self, value: str):
        self.setter_key("url", value)

    @property
    def main_branches(self) -> str:
        return self.getter_key("main_branches")  # type: ignore

    @main_branches.setter
    def main_branches(self, value: str):
        self.setter_key("main_branches", value)

    @property
    def dev_branches(self) -> str:
        return self.getter_key("dev_branches")  # type: ignore

    @dev_branches.setter
    def dev_branches(self, value: str):
        self.setter_key("dev_branches", value)

    @property
    def path(self) -> str:
        return self.getter_key("path")  # type: ignore

    @path.setter
    def path(self, value: str):
        self.setter_key("path", value)

    def getter_key(self, key: str):
        if not key:
            return None
        value = self.data[key]
        if value:
            return value
        default_value = MOD_DOL_DEFAULT[key]
        self.data[key] = default_value
        return default_value

    def setter_key(self, key: str, value: Any):
        self.data[key] = value


__all__ = ["ModDol"]
