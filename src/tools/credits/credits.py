import asyncio
import datetime
import os

import httpx
from urllib.parse import quote
from lxml import etree

from src.consts import PARATRANZ_TOKEN, GITHUB_ACCESS_TOKEN


class Credit:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def build_paratranz_members(self, project_id: int = 4780) -> list[str]:
        """Paratranz 有贡献的"""
        members = await self._get_paratranz_members(project_id)
        return self._filter_scored_paratranz_members(members)

    async def _get_paratranz_members(self, project_id: int = 4780):
        url = f"https://paratranz.cn/api/projects/{project_id}/members"
        headers = {"Authorization": PARATRANZ_TOKEN}
        response = await self.client.get(url, headers=headers)
        return response.json()

    def _filter_scored_paratranz_members(self, members: list[dict]) -> list[str]:
        return [
            f'{member["user"]["username"]}({member["user"]["nickname"]})'
            if member["user"].get("nickname")
            else f'{member["user"]["username"]}'

            for member in members
            if member["totalPoints"]
        ]

    async def build_miraheze_members(self, limit: int = 500):
        """中文维基有贡献的"""
        members_html = await self._get_miraheze_members(limit)
        return self._filter_scored_miraheze_members(members_html)

    async def _get_miraheze_members(self, limit: int = 500):
        url = "https://degreesoflewditycn.miraheze.org/w/index.php"
        params = {
            "title": quote("特殊:用户列表"),
            "editsOnly": 1,
            "wpFormIdentifier": "mw-listusers-form",
            "limit": limit
        }
        response = await self.client.get(url, params=params)
        return response.text

    def _filter_scored_miraheze_members(self, html: str):
        html = etree.HTML(html)
        return html.xpath("//bdi/text()")

    async def build_issue_members(self, owner: str = "Eltirosto", repo: str = "Degrees-of-Lewdity-Chinese-Localization", per_page: int = 100, pages: int = 2):
        """有反馈过 issue 的"""
        members_data = await self._get_issue_members(owner, repo, per_page, pages)
        return list(set(self._filter_issue_members(members_data)))

    async def _get_issue_members(self, owner: str = "Eltirosto", repo: str = "Degrees-of-Lewdity-Chinese-Localization", per_page: int = 100, pages: int = 3):
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        headers = {"Authorization": f"Bearer {GITHUB_ACCESS_TOKEN}"}
        results = []
        for page in range(1, pages+1):
            params = {
                "state": "all",
                "per_page": per_page,
                "page": page
            }
            response = await self.client.get(url, params=params, headers=headers)
            results.extend(response.json())
        return results

    def _filter_issue_members(self, members_data: list[dict]):
        return [
            member["user"]["login"]
            for member in members_data
        ]

    @property
    def client(self):
        return self._client


async def main():
    async with httpx.AsyncClient() as client:
        credit = Credit(client)
        paratranz_members: list[str] = await credit.build_paratranz_members()
        miraheze_members: list[str] = await credit.build_miraheze_members()
        issue_members: list[str] = await credit.build_issue_members(pages=3)

    paratranz_members: str = '\n- '.join(paratranz_members)
    miraheze_members: str = '\n- '.join(miraheze_members)
    issue_members: str = '\n- '.join(issue_members)

    time = datetime.datetime.now().strftime("%Y%m%d")
    with open(f"CREDITS-{time}.md", "w", encoding="utf-8") as fp:
        fp.write(
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
            "</details>"
        )

if __name__ == '__main__':
    asyncio.run(main())
