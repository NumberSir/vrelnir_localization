import asyncio
import datetime
import os
from pathlib import Path

from src.log import logger

import httpx
from urllib.parse import quote
from lxml import etree

from src.consts import PARATRANZ_TOKEN, GITHUB_ACCESS_TOKEN

DIR_RELEASE = Path("D:\\Users\\numbersir\\Documents\\GitHub\\Degrees-of-Lewdity-Chinese-Localization")


class Credit:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    """ PARATRANZ """
    async def build_paratranz_members(self, project_id: int = 4780) -> list[str]:
        """Paratranz 有贡献的"""
        members = await self._get_paratranz_members(project_id)
        return self._filter_scored_paratranz_members(members)

    async def _get_paratranz_members(self, project_id: int = 4780):
        url = f"https://paratranz.cn/api/projects/{project_id}/members"
        headers = {"Authorization": PARATRANZ_TOKEN}
        response = await self.client.get(url, headers=headers)
        logger.info("paratranz members Finished")
        return response.json()

    def _filter_scored_paratranz_members(self, members: list[dict]) -> list[str]:
        return sorted([
            f'{member["user"]["username"]}({member["user"]["nickname"]})'
            if member["user"].get("nickname")
            else f'{member["user"]["username"]}'
            for member in members
            if member["totalPoints"]
        ])

    """ WIKI """
    async def build_miraheze_members(self, limit: int = 600):
        """中文维基有贡献的"""
        members_html = await self._get_miraheze_members(limit)
        return self._filter_scored_miraheze_members(members_html)

    async def _get_miraheze_members(self, limit: int = 600):
        url = f"https://degreesoflewditycn.miraheze.org/wiki/{quote('特殊:用户列表')}"
        params = {
            "editsOnly": 1,
            "wpFormIdentifier": "mw-listusers-form",
            "limit": limit,
        }
        response = await self.client.get(url, params=params)
        logger.info("miraheze members Finished")
        return response.text

    def _filter_scored_miraheze_members(self, html: str):
        html = etree.HTML(html)
        return sorted(html.xpath("//bdi/text()"))

    """ GITHUB """
    async def build_issue_members(
        self,
        owner: str = "Eltirosto",
        repo: str = "Degrees-of-Lewdity-Chinese-Localization",
        per_page: int = 100,
        pages: int = 6,
    ):
        """有反馈过 issue 的"""
        members_data = await self._get_issue_members(owner, repo, per_page, pages)
        return sorted(list(set(self._filter_issue_members(members_data))))

    async def _get_issue_members(
        self,
        owner: str = "Eltirosto",
        repo: str = "Degrees-of-Lewdity-Chinese-Localization",
        per_page: int = 100,
        pages: int = 6,
    ) -> list[dict]:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        headers = {"Authorization": f"Bearer {GITHUB_ACCESS_TOKEN}"}
        results = []
        for page in range(1, pages + 1):
            params = {"state": "all", "per_page": per_page, "page": page}
            response = await self.client.get(url, params=params, headers=headers)
            results.extend(response.json())
        logger.info("issue members Finished")
        return results

    def _filter_issue_members(self, members_data: list[dict]):
        return [member["user"]["login"] for member in members_data]

    """ PROPERTY """
    @property
    def client(self):
        return self._client


async def main():
    async with httpx.AsyncClient(verify=False) as client:
        credit = Credit(client)
        paratranz_members: list[str] = await credit.build_paratranz_members()
        miraheze_members: list[str] = await credit.build_miraheze_members()
        issue_members: list[str] = await credit.build_issue_members(pages=3)

    paratranz_members: str = "\n- ".join(paratranz_members)
    miraheze_members: str = "\n- ".join(miraheze_members)
    issue_members: str = "\n- ".join(issue_members)

    time = datetime.datetime.now().strftime("%Y%m%d")
    os.makedirs(Path(__file__).parent / "credits", exist_ok=True)

    content = (
        "## 欲都孤儿 贡献者名单\n"
        f"> {time}\n"
        "### 为汉化做出过贡献的诸位（排名不分先后）：\n"
        "<details>\n"
        "<summary>点击展开</summary>\n\n"
        f"- {paratranz_members}\n\n"
        "</details>\n\n"
        "### 为建设中文维基提供过贡献的诸位（排名不分先后）：\n"
        "<details>\n"
        "<summary>点击展开</summary>\n\n"
        f"- {miraheze_members}\n\n"
        "</details>\n\n"
        "### 为改进汉化内容提供过贡献的诸位（排名不分先后）：\n"
        "<details>\n"
        "<summary>点击展开</summary>\n\n"
        f"- {issue_members}\n\n"
        "</details>\n\n"
        "---\n"
        "本游戏的汉化版制作、维护与更新属实不易，十分感谢以上不吝提供帮助、做出贡献的诸位。"
    )

    with open(Path(__file__).parent / "credits" / "CREDITS.md", "w", encoding="utf-8") as fp:
        fp.write(content)

    with open(DIR_RELEASE / "CREDITS.md", "w", encoding="utf-8") as fp:
        fp.write(content)


if __name__ == "__main__":
    asyncio.run(main())
