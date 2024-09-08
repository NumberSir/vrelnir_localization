import asyncio
from pathlib import Path

from src import (
    logger,
    Paratranz,
    ProjectDOL,
    PARATRANZ_TOKEN,
    CHINESE_VERSION,
    SOURCE_TYPE
)
from src.tools.process_variables import VariablesProcess as VP

async def process_common(dol_common: ProjectDOL, pt: Paratranz, chs_version: str):
    """
    原版处理流程
    1. 下载源码
    2. 创建生肉词典
    3. 下载汉化词典
    4. 替换生肉词典
    5. 替换游戏原文
    """
    """ 删库跑路 """
    await dol_common.drop_all_dirs()

    """ 下载源码 """
    await dol_common.download_from_gitgud()

    """ 预处理所有的 <<set>> """
    var = VP()
    var.fetch_all_file_paths()
    var.fetch_all_set_content()

    """ 创建生肉词典 """
    await dol_common.create_dicts()

    """ 下载汉化词典 成品在 `raw_dicts` 文件夹里 """
    download_flag = await pt.download_from_paratranz()  # 如果下载，需要在 consts 里填上管理员的 token, 在网站个人设置里找
    if not download_flag:
        return

    """ 替换生肉词典 """
    await dol_common.update_dicts()


async def main():
    logger.info(f"filepath: {Path(__file__)}")
    dol_common = ProjectDOL(type_=SOURCE_TYPE)  # 改成 “dev” 则下载最新开发版分支的内容 common原版

    pt_common = Paratranz(type_=SOURCE_TYPE)
    if not PARATRANZ_TOKEN:
        logger.error("未填写 PARATRANZ_TOKEN, 汉化包下载可能失败，请前往 https://paratranz.cn/users/my 的设置栏中查看自己的 token, 并在 .env 中填写\n")
        return

    await process_common(dol_common, pt_common, chs_version=CHINESE_VERSION)


if __name__ == '__main__':
     asyncio.run(main())
