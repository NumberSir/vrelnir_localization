# Vrelnir Localization([Degrees of Lewdity](https://gitgud.io/Vrelnir/degrees-of-lewdity))
<a href='https://gitee.com/Number_Sir/vrelnir_localization/stargazers'><img src='https://gitee.com/Number_Sir/vrelnir_localization/badge/star.svg?theme=dark' alt='star'></img></a>
![GitHub stars](https://img.shields.io/github/stars/NumberSir/vrelnir_localization?style=social)

## 简介
[黄油翻译小工具 0v0](https://github.com/NumberSir/vrelnir_localization)
1. 获取原仓库最新内容下载到本地
2. 生成对应版本的字典，放在 `raw_dict` 文件夹里
3. 从 `paratranz` 下载最新汉化包 (可能要在 `src/consts.py` 里填你的 `token`, 在个人设置里找)
4. 用最新的汉化包替换自动提取出的汉化包，保存失效值
5. 覆写游戏源文件的汉化 (检查简单的翻译错误如全角逗号: `"，`, 尖括号不对齐: `<< >`, 不该翻译的东西翻译了: `<<link [[该翻译的|不该翻译的]]>>`)
6. 编译为 `html` 并用默认浏览器运行

## 食用方法
1. 需要 Python 3.10+
2. 在根目录使用 `pip install -r requirements.txt` 安装依赖库
3. 在 `src/consts.py` 里填你的 `token`, 在 `https://paratranz.cn/users/my` 里找
4. 运行 `main.py` (`python -m main`)