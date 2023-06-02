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
<<link [[TEXT]]>>
<<link [[TEXT|EVENT]]>>

$VAR                | 变量
$VAR.FUNC(PARAM)    | 调用函数
$VAR.PROP           | 属性

STRING                  | 文本
<CHAR_1>ANY</CHAR_1>    | 有闭合的
<CHAR_0>                | 无闭合的

//COMMENT       | 注释
/*COMMENT*/     | 注释
<!--COMMENT-->  | 注释

要翻译的：
TEXT, STRING
"""
import asyncio
import time

from src import (
    logger,
    Paratranz,
    ProjectDOL
)


async def main():
    start = time.time()
    # =====
    dol = await ProjectDOL().async_init(type_="common")  # 改成 “dev” 则下载最新开发版分支的内容
    pt = Paratranz()

    """ 删库跑路 """
    await dol.drop_all_dirs()

    """ 获取最新版本 """
    await dol.fetch_latest_version()

    """ 提取键值 """
    await dol.download_from_gitgud()
    await dol.create_dicts()

    """ 更新导出的字典 成品在 `raw_dicts` 文件夹里 """
    await pt.download_from_paratranz()  # 如果下载，需要在 consts 里填上管理员的 token, 在网站个人设置里找
    await dol.update_dicts()

    """ 覆写汉化 用的是 `paratranz` 文件夹里的内容覆写 """
    await dol.apply_dicts()
    error = []

    """ 编译成游戏 """
    dol.compile()
    dol.run()
    # =====
    end = time.time()
    return end-start


if __name__ == '__main__':
    last = asyncio.run(main())
    logger.info(f"===== 总耗时 {last}s =====")
 
