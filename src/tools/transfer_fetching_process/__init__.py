"""
过渡使用：
旧版以行为单位提取文本，新版以块为单位提取文本
将旧版的已汉化的内容按照新版拼接
1. 获取旧版的 原文-译文 键值对，同时明确旧版的每个原文的起止位置
2. 获取新版的 原文-译文 键值对，同时明确新版的每个原文的起止位置
3. 逐个对比，如果旧版的起止位置在新版的起止位置之内，则按照起止位置拼接合并，如果需要合并的内容之间有旧版未提取的内容，则拼接原文
"""