"""
基本种类:
:: EVENT [WIDGET]      | 一般在文件开头

<<WIDGET_1>>ANY<</WIDGET_1>>   | 有闭合的
<<WIDGET_0>>                | 无闭合的
<<WIDGET "TAG">>            | 特殊名称
<<WIDGET COND>>             | 条件，如 if / link 等

特殊:
<<if>>ANY<<elseif>>ANY<<else>>ANY<</if>>

<<switch>>ANY<<case>>ANY<</switch>>

<<link [[TEXT]]>></link<>>
<<link [[TEXT|EVENT]]>></link<>>

<<set $VAR to KEYWORD>>
<<set $VAR to "VAR">>
<<set $VAR to "STRING">>

$VAR                | 变量
$VAR.FUNC(PARAM)    | 调用函数
$VAR.PROP           | 属性

STRING                  | 文本
<CHAR_1>ANY</CHAR_1>    | 有闭合的
<CHAR_0>                | 无闭合的

<span class="VAR">TEXT</span>

//COMMENT       | 注释
/*COMMENT*/     | 注释(可跨行)
    /* COMMENT
     * COMMENT
     * COMMENT */
<!--COMMENT-->  | 注释(可跨行)
    <!-- COMMENT
    COMMENT -->

要翻译的：
TEXT, STRING
"""
import asyncio
import sys
import time

from src import (
    logger,
    Paratranz,
    ProjectDOL,
    PARATRANZ_TOKEN,
    PARATRANZ_PROJECT_WE_ID
)
from src.ast import Acorn, JSSyntaxError



# async def process_world_expansion(dol_we: ProjectDOL, pt_common: Paratranz, pt_we: Paratranz, version: str):
#     """
#     世界扩展处理流程
#     1. 下载源码
#     2. 创建生肉词典
#     3. 下载原版汉化词典
#     4. 去重生肉词典
#     5. 下载世扩汉化词典
#     6. 替换生肉词典
#     7. 替换游戏原文
#     """
#
#     """ 删库跑路 """
#     await dol_we.drop_all_dirs()
#
#     """ 获取最新版本 """
#     await dol_we.fetch_latest_version()
#
#     """ 下载源码 """
#     await dol_we.download_from_gitgud()
#
#     """ 创建生肉词典 """
#     await dol_we.create_dicts()
#
#     """ 下载原版汉化词典 """
#     download_flag = await pt_common.download_from_paratranz()
#     if not download_flag:
#         return
#
#     """ 去重生肉词典 """
#     await dol_we.shear_off_repetition()
#
#     """ 下载世扩汉化词典 """
#     download_flag = await pt_we.download_from_paratranz()  # 如果下载，需要在 consts 里填上管理员的 token, 在网站个人设置里找
#     if not download_flag:
#         return
#
#     """ 替换生肉词典 """
#     await dol_we.update_dicts()
#
#     """ 替换游戏原文 """
#     blacklist_dirs = []
#     blacklist_files = []
#     await dol_we.apply_dicts(blacklist_dirs, blacklist_files, debug_flag=False)
#     await dol_we.apply_dicts(blacklist_dirs, blacklist_files, debug_flag=False, type_manual="common")
#
#     """ 有些额外需要更改的 """
#     dol_we.change_css()
#     dol_we.change_version(version)
#
#     """ 编译成游戏 """
#     dol_we.compile()
#     dol_we.run()

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

    """ 获取最新版本 """
    await dol_common.fetch_latest_version()

    """ 下载源码 """
    await dol_common.download_from_gitgud()

    """ 创建生肉词典 """
    await dol_common.create_dicts()

    """ 下载汉化词典 成品在 `raw_dicts` 文件夹里 """
    download_flag = await pt.download_from_paratranz()  # 如果下载，需要在 consts 里填上管理员的 token, 在网站个人设置里找
    if not download_flag:
        return

    """ 替换生肉词典 """
    await dol_common.update_dicts()

    """ 替换游戏原文 用的是 `paratranz` 文件夹里的内容覆写 """
    blacklist_dirs = []
    blacklist_files = []
    await dol_common.apply_dicts(blacklist_dirs, blacklist_files, debug_flag=False)

    """ 有些额外需要更改的 """
    dol_common.change_css()
    dol_common.replace_banner()
    dol_common.change_version(chs_version)

    """ 编译成游戏 """
    dol_common.compile()
    dol_common.package_zip(chs_version)
    dol_common.run()


async def main():
    start = time.time()
    # =====
    dol_common = ProjectDOL(type_="common")  # 改成 “dev” 则下载最新开发版分支的内容common原版 world世界扩展
    # dol_we = ProjectDOL(type_="world")

    pt_common = Paratranz(type_="common")
    # pt_we = Paratranz(type_="world")
    if not PARATRANZ_TOKEN:
        logger.error("未填写 PARATRANZ_TOKEN, 汉化包下载可能失败，请前往 https://paratranz.cn/users/my 的设置栏中查看自己的 token, 并在 .env 中填写\n")
        return

    """编译原版用，编译世扩请注释掉这个"""
    await process_common(dol_common, pt_common, chs_version="0.4.2.4-chs-alpha1.0.0-pre")

    """编译世扩用，编译原版请注释掉这个"""
    # await process_world_expansion(dol_we, pt_common, pt_we, version="0.4.1.7-we-chs-alpha1.0.1")

    end = time.time()
    return end-start


if __name__ == '__main__':
     last = asyncio.run(main())
     logger.info(f"===== 总耗时 {last or -1}s =====")
