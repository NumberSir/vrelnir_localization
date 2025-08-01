# Vrelnir Localization([Degrees of Lewdity](https://gitgud.io/Vrelnir/degrees-of-lewdity))
<a href='https://gitee.com/Number_Sir/vrelnir_localization/stargazers'><img src='https://gitee.com/Number_Sir/vrelnir_localization/badge/star.svg?theme=dark' alt='star'></img></a>
![GitHub stars](https://img.shields.io/github/stars/NumberSir/vrelnir_localization?style=social)

## 新项目（未完成）
[Sugarcube2-Localization](https://github.com/NumberSir/Sugarcube2-Localization)

## 简介
[黄油翻译小工具 0v0](https://github.com/NumberSir/vrelnir_localization)
1. 获取原仓库最新内容下载到本地
2. 生成对应版本的字典，放在 `raw_dict` 文件夹里
3. 从 `paratranz` 下载最新汉化包 (可能要在 `src/consts.py` 里填你的 `token`, 在个人设置里找)
4. 用最新的汉化包替换自动提取出的汉化包，保存失效值
5. 覆写游戏源文件的汉化 (检查简单的翻译错误如全角逗号: `"，`, 尖括号不对齐: `<< >`)
6. 修改版本号 `chs-x.y.z`
7. 生成供 `i18n` mod 加载的汉化字典包 (默认在 `data/json/i18n.json`)
8. 编译为 `html` 并用默认浏览器运行 (默认在 `degrees-of-lewdity-master`)

## 食用方法
1. 需要 [Python 3.10+](https://www.python.org/downloads/)
2. 安装 [uv](https://docs.astral.sh/uv/#installation)
   - Windows:
   ```shell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   - macOS / Linux:
   ```shell
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. 使用 uv 安装项目依赖
   ```shell
   uv sync
   ```
3. 在 `.env` 里填你的 `token` (`PARATRANZ_TOKEN`), 在 `https://paratranz.cn/users/my` 的设置里找
4. 在 `.env` 里修改版本号 (`CHINESE_VERSION`)
5. 运行 `main.py` 
   ```shell
   uv run main.py
   ```

## 关于版本号
汉化版本号的基本结构是 `chs-x.y.z`，如 `chs-alpha1.7.1`

游戏版本号的基本结构是 `{游戏版本号}-chs-{汉化版本号}`，如 `0.4.1.7-chs-alpha1.7.1`

汉化版本号的修改遵循如下规则：
1. `alpha` / `beta` / `release` 分别代表：
   - `alpha`: 当前翻译率达到 100%, 可能有漏提取的文本，润色不充分
   - `beta`: 当前翻译率达到 100%, 没有漏提取的文本，润色不充分 
   - `release`: 当前翻译率达到 100%, 没有漏提取的文本，已经充分润色
2. 如果游戏版本号发生破坏性更新：如 `0.4.1` => `0.4.2`, 或 `0.4` -> `0.5`，则汉化版本号重置，如：
   - `0.4.1.7-chs-alpha1.7.1` => `0.4.2.4-chs-alpha1.0.0`
3. 如果游戏版本号发生小修小补更新：如 `0.4.1.6` => `0.4.1.7`, 或 `0.4.2.0` => `0.4.2.5`，则汉化版本号第一位加一，如：
   - `0.4.2.4-chs-alpha1.0.0` => `0.4.2.5-chs-alpha2.0.0`
4. 每周五晚九点定期更新，则汉化版本号第二位加一，如：
   - `0.4.1.7-chs-alpha1.6.0` => `0.4.1.7-chs-alpha1.7.0`
5. 出现了导致游戏无法继续进行的恶性问题而临时更新，则汉化版本号末位加一，如：
   - `0.4.1.7-chs-alpha1.7.0` => `0.4.1.7-chs-alpha1.7.1`
6. 如果打包自用 / 群内用的临时前瞻版，则在汉化版本号后加 `-pre`，如：
   - `0.4.1.7-chs-alpha1.7.1` => `0.4.1.7-chs-alpha1.8.0-pre` 