# vrelnir_localization


黄油翻译小工具 0v0
1. 获取原仓库最新内容下载到本地
2. 生成对应版本的字典，放在 `raw_dict` 文件夹里
3. 从 `paratranz` 下载最新汉化包 (可能要在 `consts.py` 里填你的 `token`, 在个人设置里找)
4. 用最新的汉化包替换自动提取出的汉化包
5. 覆写游戏源文件的汉化
6. 编译为 `html` 并用默认浏览器运行

注:
- `raw_dicts` 自动提取出的字典，有 `csv` 和 `json` 两种格式
