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
import time

from src import (
    logger,
    Paratranz,
    ProjectDOL,
    PARATRANZ_TOKEN,
    CHINESE_VERSION,
    SOURCE_TYPE,
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
    # await dol_common.patch_format_js()

    """ 预处理所有的 <<set>> """
    var = VP()
    var.fetch_all_file_paths()
    var.fetch_all_set_content()

    """ 创建生肉词典 """
    await dol_common.create_dicts()

    """ 下载汉化词典 成品在 `raw_dicts` 文件夹里 """
    download_flag = (
        await pt.download_from_paratranz()
    )  # 如果下载，需要在 consts 里填上管理员的 token, 在网站个人设置里找
    if not download_flag:
        return

    """ 替换生肉词典 """
    await dol_common.update_dicts()

    """ 替换游戏原文 用的是 `paratranz` 文件夹里的内容覆写 """
    blacklist_dirs = [
        # "00-framework-tools",
        # "01-config",
        # "03-JavaScript",
        # "04-Variables",
        # "base-clothing",
        # "base-combat",
        # "base-debug",
        # "base-system",
        # "flavour-text-generators",
        # "fonts",
        # "overworld-forest",
        # "overworld-plains",
        # "overworld-town",
        # "overworld-underground",
        # "special-dance",
        # "special-exhibition",
        # "special-masturbation",
        # "special-templates"
    ]
    blacklist_files = []
    await dol_common.apply_dicts(blacklist_dirs, blacklist_files, debug_flag=False)

    # """ 有些额外需要更改的 """
    dol_common.change_css()  # 更换一些样式和硬编码文本
    dol_common.replace_banner()  # 更换游戏头图
    dol_common.change_version(chs_version)  # 更换游戏版本号

    """ 编译成游戏 """
    dol_common.compile(chs_version)
    dol_common.package_zip(chs_version)  # 自动打包成 zip
    dol_common.run()  # 运行


async def main():
    start = time.time()
    # =====
    dol_common = ProjectDOL(
        type_=SOURCE_TYPE
    )  # 改成 “dev” 则下载最新开发版分支的内容 common原版

    pt_common = Paratranz(type_=SOURCE_TYPE)
    if not PARATRANZ_TOKEN:
        logger.error("未填写 PARATRANZ_TOKEN, 汉化包下载可能失败，请前往 https://paratranz.cn/users/my 的设置栏中查看自己的 token, 并在 .env 中填写\n")
        return

    await process_common(dol_common, pt_common, chs_version=CHINESE_VERSION)

    end = time.time()
    return end - start


if __name__ == "__main__":
    last = asyncio.run(main())
    logger.info(f"===== 总耗时 {last or -1:.2f}s =====")
    try:
        from win10toast import ToastNotifier
    except ImportError:
        pass
    else:
        ToastNotifier().show_toast(title="dol脚本运行完啦", msg=f"总耗时 {last or -1:.2f}s")
