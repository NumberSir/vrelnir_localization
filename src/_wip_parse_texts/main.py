import json
import os
import re

from pathlib import Path

from src.parse_texts.log import logger
from src.parse_texts.consts import (
    DIR_PASSAGE,
    DIR_TARGET,
    DIR_GAME_TEXTS,
    DIR_PARATRANZ_EXPORT,
    GAME_TEXTS_NAME,
    PTN_COMMENT,
    PTN_MACRO,
    PTN_TAG,
    GENERAL_LIMIT,
)


class ParseTwine:
    def __init__(self) -> None:
        # 记录所有 twine 文件绝对路径
        self._twine_filepaths: list[Path] = []

        # 记录所有段落名称
        self._twine_passage_names: list[str] = []
        # 详细记录所有段落信息，等待进一步处理
        self._twine_passage_data: dict[str, dict] = {}
        # 扁平化处理，只有一层
        self._twine_passage_data_flat: list[dict] = []

        # 详细记录所有元素信息，等待进一步处理
        self._twine_elements_data: dict[str, dict] = {}
        # 扁平化处理，只有一层
        self._twine_elements_data_flat: list[dict] = []

        # 详细记录经过组合后的元素信息，等待进一步处理
        self._twine_combined_elements_data: dict[str, dict] = {}
        # 扁平化处理，只有一层
        self._twine_combined_elements_data_flat: list[dict] = []

        # 旧版汉化方式词条添加各种信息，等待进一步处理
        self._paratranz_detailed_raw_data: dict[str, list[dict]] = {}

        # 处理成可在 paratranz 导入的格式，等待进一步处理
        self._paratranz_elements_data: dict[str, dict] = {}
        # 扁平化处理，只有一层
        self._paratranz_elements_data_flat: list[dict] = []

    @staticmethod
    def init_dirs() -> None:
        """创建目录"""
        for dir_ in {DIR_PASSAGE, DIR_TARGET}:
            os.makedirs(dir_, exist_ok=True)

    # 入口函数
    def parse(self) -> None:
        """入口函数"""
        self.get_all_twine_filepaths()
        self.get_all_twine_passages()

        self.get_all_basic_elements()
        self.get_all_plaintext_elements()

        self.combine_twine_element_pairs()
        self.combine_twine_element_full()

        self.build_paratranz_detailed_raw_data()
        self.build_paratranz_format()

    # 文件路径
    def get_all_twine_filepaths(self) -> None:
        """获取所有文件绝对路径，方便下一步提取"""
        logger.info("开始获取所有 twine 文件绝对路径……")
        self._twine_filepaths = [
            Path(root) / file
            for root, _, files in os.walk(DIR_GAME_TEXTS)
            for file in files
            if file.endswith(".twee")
        ]

        logger.info("所有 twine 文件绝对路径已获取！")

    # 段落信息
    def get_all_twine_passages(self):
        """获取所有的段落信息，方便下一步提取和元素位置记录"""
        logger.info("开始获取所有 twine 段落信息……")
        for filepath in self._twine_filepaths:
            with open(filepath, "r", encoding="utf-8") as fp:
                content = fp.read()

            if not content:  # 有些文件为空
                continue

            content = f"\n{content}"  # 方便分割段落
            content_slices = content.split("\n::")[1:]  # 按照段落标题的标识符分割

            # 这一步是以游戏源代码的 "game" 文件夹为根目录切割成相对路径
            relative_filepath = Path().joinpath(*filepath.parts[filepath.parts.index(GAME_TEXTS_NAME) + 2:]).__str__()
            for slice_ in content_slices:
                # 段落名称，在接下来的处理中会除去[]与{}中的内容
                passage_name = slice_.split("\n")[0].strip()
                # 段落内容，不包括段落标题行的所有内容
                passage_body = "\n".join(slice_.split("\n")[1:-1])
                passage_full = f":: {passage_name}\n{passage_body}"

                if passage_name.endswith("]"):
                    # 只保留段落名称的纯文本内容
                    passage_name = passage_name.split("[")[0].strip()

                passage_data = {
                    "filepath": relative_filepath,
                    "passage_name": passage_name,
                    "passage_body": passage_body,
                    "passage_full": passage_full,
                }

                self._twine_passage_names.append(passage_name)
                self._twine_passage_data_flat.append(passage_data)
                if relative_filepath not in self._twine_passage_data:
                    self._twine_passage_data[relative_filepath] = {passage_name: passage_data}
                elif passage_name not in self._twine_passage_data[relative_filepath]:
                    self._twine_passage_data[relative_filepath][passage_name] = passage_data
                else:
                    raise

        logger.info("所有 twine 段落信息已获取！")

    # 基础元素
    def get_all_basic_elements(self):
        """获取所有 comment, head, macro 和 tag 的信息，剩下的就是 plain text"""
        logger.info("开始获取所有 twine 基础元素……")

        def _add_element(fp: str, pg: str, match: re.Match, type_: str):
            """重复的部分提出来封装"""
            element = {
                "filepath": fp,
                "passage": pg,
                "type": type_,
                "element": match.group(),
                "pos_start": match.start(),
                "pos_end": match.end(),
            }
            self._twine_elements_data_flat.append(element)
            if fp not in self._twine_elements_data:
                self._twine_elements_data[fp] = {pg: [element]}
            elif pg not in self._twine_elements_data[fp]:
                self._twine_elements_data[fp][pg] = [element]
            else:
                self._twine_elements_data[fp][pg].append(element)

        for passage in self._twine_passage_data_flat:
            filepath = passage["filepath"]
            content = passage["passage_body"]
            passage_name = passage["passage_name"]

            comments = re.finditer(PTN_COMMENT, content)
            for comment in comments:
                _add_element(filepath, passage_name, comment, "comment")

            macros = re.finditer(PTN_MACRO, content)
            for macro in macros:
                _add_element(filepath, passage_name, macro, "macro")

            tags = re.finditer(PTN_TAG, content)
            for tag in tags:
                _add_element(filepath, passage_name, tag, "tag")

        self.sort_elements_data()
        self.filter_comment_inside()
        logger.info("所有 twine 基础元素已获取！")

    # 剔除注释中元素
    def filter_comment_inside(self):
        """因为按照正则提取，有些在注释里的内容也被抓出来了"""
        for filepath, elements_data in self._twine_elements_data.items():
            for passage, elements in elements_data.items():
                elements_copy = elements.copy()
                for idx, element in enumerate(elements_copy):
                    if element["type"] != "comment":
                        continue

                    for i in range(len(elements_copy) - idx):
                        # i 从 0 开始，所以直接跳过自己
                        if i == 0:
                            continue

                        # 因为按照 pos_start 排序过了，所以被注释包裹的元素一定在注释的后面
                        # 因此当出现后者开头小于前者结尾时一定是前者是注释，后者是被注释包住的元素
                        if elements_copy[idx + i]["pos_start"] < element["pos_end"]:
                            elements[idx + i] = None

                self._twine_elements_data[filepath][passage] = [element for element in elements if element is not None]
        self.sort_elements_data()

    # 纯文本
    def get_all_plaintext_elements(self):
        # sourcery skip: hoist-statement-from-if
        """夹在其它元素之间的就是 plain text"""
        logger.info("开始获取所有 twine 纯文本元素……")

        for filepath, elements_data in self._twine_elements_data.items():
            for passage, elements in elements_data.items():
                content = self._twine_passage_data[filepath][passage]["passage_body"]
                elements_copy = elements.copy()

                for idx, element in enumerate(elements_copy):
                    # 已经提取的元素开头之前可能有纯文本
                    # 这里比较特殊，因为要进行两次判断，一次向前判断一次向后判断
                    # 已经提取的元素开头不是段落开头的情况下，才有纯文本
                    if idx <= 0 < element["pos_start"]:
                        text = content[: element["pos_start"]]
                        pos_start = 0
                        pos_end = element["pos_start"]
                        elements.append({
                            "filepath": filepath,
                            "passage": passage,
                            "type": "text",
                            "element": text,
                            "pos_start": pos_start,
                            "pos_end": pos_end,
                        })

                    # 非末尾，开头的向后二次判断合并进这里
                    if idx < len(elements_copy) - 1:
                        # 前后两元素中间没有内容，因此没有纯文本
                        if element["pos_end"] == elements_copy[idx + 1]["pos_start"]:
                            continue

                        text = content[element["pos_end"]: elements_copy[idx + 1]["pos_start"]]
                        pos_start = element["pos_end"]
                        pos_end = elements_copy[idx + 1]["pos_start"]

                    # 已经提取的元素末尾之后可能有纯文本
                    else:
                        # 已经提取的元素末尾就是段落末尾，因此没有纯文本
                        if element["pos_end"] >= len(content):
                            continue

                        text = content[element["pos_end"] :]
                        pos_start = element["pos_end"]
                        pos_end = len(content)

                    text_element = {
                        "filepath": filepath,
                        "passage": passage,
                        "type": "text",
                        "element": text,
                        "pos_start": pos_start,
                        "pos_end": pos_end,
                    }
                    elements.append(text_element)

                self._twine_elements_data[filepath][passage] = elements
        self.sort_elements_data()
        logger.info("所有 twine 纯文本元素已获取！")

    # 排序
    def sort_elements_data(self):
        """按照元素的位置排序，方便下一步操作"""
        for filepath, elements_data in self._twine_elements_data.items():
            for passage, elements in elements_data.items():
                self._twine_elements_data[filepath][passage] = sorted(elements, key=lambda elem: elem["pos_start"])

    # 先按照开闭组合一遍
    def combine_twine_element_pairs(self):
        """将元素按照开闭/段落进行初次组合"""
        logger.info("开始初次组合所有元素……")

        def _add_element(fp: str, pg: str, elem: str, start: int, end: int):
            """这是添加元素的，重复的部分提出来封装"""
            combined = {
                "filepath": fp,
                "passage": pg,
                "element": elem,
                "pos_start": start,
                "pos_end": end,
                "length": end - start,
            }
            if fp not in self._twine_combined_elements_data:
                self._twine_combined_elements_data[fp] = {pg: [combined]}
            elif pg not in self._twine_combined_elements_data[fp]:
                self._twine_combined_elements_data[fp][pg] = [combined]
            else:
                self._twine_combined_elements_data[fp][pg].append(combined)

        for filepath, elements_data in self._twine_elements_data.items():
            for passage, elements in elements_data.items():
                content = self._twine_passage_data[filepath][passage]["passage_body"]
                # 先判断整个段落的字数是否在 1000 字以内，是的话直接打包装走
                if len(content) <= GENERAL_LIMIT:
                    _add_element(filepath, passage, content, 0, len(content))
                    continue

                jumped_idx = None  # 判断当前元素是否是需要跳过的被合并的部分
                elements_copy = elements.copy()
                for idx, element in enumerate(elements_copy):
                    # 合并元素的过程中需要跳过被合并的部分
                    if jumped_idx is not None and idx != jumped_idx:
                        continue

                    jumped_idx = None

                    head_elem = element["element"]
                    head_type = element["type"]
                    head_start = element["pos_start"]
                    head_end = element["pos_end"]

                    # 遇到注释直接加，接下来再进一步处理
                    if head_type == "comment":
                        _add_element(filepath, passage, content[head_start:head_end], head_start, head_end)
                        continue

                    # 找闭合的 macro
                    if head_type == "macro":
                        # 这个是结尾，因为正常情况下不会先遇到结尾再遇到开头，因此这是没有被合并的单个元素，直接添加
                        if head_elem.startswith("<</"):
                            _add_element(filepath, passage, content[head_start:head_end], head_start, head_end)
                            continue

                        macro_name = re.findall(r"^<<([\w=\-]+)", head_elem)[0]  # 方便判断结尾的位置
                        layer = 0  # 可能出现 if 套 if 这类情况，因此用层数判断是否在最外层
                        block_start = head_start

                        # 接下来在给定 macro 开头的情况下，找到对应的 macro 结尾
                        # 并判断字符数是否在限制以内，是的话就组合起来，不是则跳过去找下一个
                        # 一直到结尾都没找到对应的结尾，说明这个 macro 无需闭合，直接添加然后正常向下继续即可
                        flag = False
                        for i in range(len(elements_copy) - idx):
                            """
                            eg: 元素可为012345
                            元素是2时, idx=2, len=6, i=0~3
                            i=0时指向元素2，i=3时指向元素5
                            所以需要把i=0跳过
                            """
                            if i == 0:  # 代表当前的元素，直接跳过
                                continue

                            tail_elem = elements_copy[idx + i]["element"]
                            tail_type = elements_copy[idx + i]["type"]
                            tail_end = elements_copy[idx + i]["pos_end"]
                            if tail_type != "macro":  # 要找结尾，连 macro 都不是，直接跳过
                                continue

                            if tail_elem.startswith(f"<<{macro_name}"):  # 多加一层
                                layer += 1
                                continue

                            if not tail_elem.startswith(f"<</{macro_name}"):  # 不是结尾，直接跳过
                                continue

                            if layer > 0:  # 是结尾，但是不是最外层
                                layer -= 1
                                continue

                            # 现在是最外层结尾了
                            block_end = tail_end
                            length = block_end - block_start
                            flag = True

                            if length > GENERAL_LIMIT:  # 太长，因此不考虑这个组合，只单独把这一个 macro 元素加进去就好了，然后直接跳出
                                _add_element(filepath, passage, content[head_start:head_end], head_start, head_end,)
                                break

                            # 注意添加之后，应该跳过中间这些被合并的部分，从末尾的下一个元素开始继续大循环
                            jumped_idx = idx + i + 1
                            _add_element(filepath, passage, content[block_start:block_end], block_start, block_end)
                            break

                        # 因为正常情况下，无论是符合长度的，还是不符合长度的都是 flag = True
                        # 因此仅有不闭合的才会 flag = False，此时单独将这一个元素加入其中，然后正常循环即可
                        if not flag:
                            _add_element(filepath, passage, content[head_start:head_end], head_start, head_end)

                    # 找闭合的 tag, 原理同上
                    elif head_type == "tag":
                        # 这个是结尾，因为正常情况下不会先遇到结尾再遇到开头，因此这是没有被合并的单个元素，直接添加
                        if head_elem.startswith("</"):
                            _add_element(filepath, passage, content[head_start:head_end], head_start, head_end)
                            continue

                        tag_name = re.findall(r"^<(\w+)", head_elem)[0]  # 方便判断结尾的位置
                        layer = 0  # 可能出现 span 套 span 这类情况，因此用层数判断是否在最外层
                        block_start = head_start

                        # 接下来在给定 macro 开头的情况下，找到对应的 tag 结尾
                        # 并判断字符数是否在限制以内，是的话就组合起来，不是则跳过去找下一个
                        # 一直到结尾都没找到对应的结尾，说明这个 tag 无需闭合，直接添加然后正常向下继续即可
                        flag = False
                        for i in range(len(elements_copy) - idx):
                            """
                            eg: 元素可为012345
                            元素是2时, idx=2, len=6, i=0~3
                            i=0时指向元素2，i=3时指向元素5
                            所以需要把i=0跳过
                            """
                            if i == 0:  # 代表当前的元素，直接跳过
                                continue

                            tail_elem = elements_copy[idx + i]["element"]
                            tail_type = elements_copy[idx + i]["type"]
                            tail_end = elements_copy[idx + i]["pos_end"]
                            if tail_type != "tag":  # 要找结尾，连 tag 都不是，直接跳过
                                continue

                            if tail_elem.startswith(f"<{tag_name}"):  # 多加一层
                                layer += 1
                                continue

                            if not tail_elem.startswith(f"</{tag_name}"):  # 不是结尾，直接跳过
                                continue

                            if layer > 0:  # 是结尾，但是不是最外层
                                layer -= 1
                                continue

                            # 现在是最外层结尾了
                            block_end = tail_end
                            length = block_end - block_start
                            flag = True

                            if length > GENERAL_LIMIT:  # 太长，因此不考虑这个组合，只单独把这一个 tag 元素加进去就好了，然后直接跳出
                                _add_element(filepath, passage, content[head_start:head_end], head_start, head_end)
                                break

                            # 注意添加之后，应该跳过中间这些被合并的部分，从末尾的下一个元素开始继续大循环
                            jumped_idx = idx + i + 1
                            _add_element(filepath, passage, content[block_start:block_end], block_start, block_end)
                            break

                        # 因为正常情况下，无论是符合长度的，还是不符合长度的都是 flag = True
                        # 因此仅有不闭合的才会 flag = False，此时单独将这一个元素加入其中，然后正常循环即可
                        if not flag:
                            _add_element(filepath, passage, content[head_start:head_end], head_start, head_end)

                    # 只剩纯文本了，没什么好说的，直接无脑加就行
                    else:
                        _add_element(filepath, passage, content[head_start:head_end], head_start, head_end)

        logger.info("所有元素已初次组合！")

    # 再按照字数组合一遍
    def combine_twine_element_full(self):
        """将元素按照字数进行二次组合"""
        logger.info("开始二次组合所有元素……")
        for filepath, elements_data in self._twine_combined_elements_data.items():
            for passage, elements in elements_data.items():
                if len(elements) == 1:  # 这是一整个段落都合并了的情况，直接添加然后跳出就好
                    self._twine_combined_elements_data_flat.extend(elements)
                    continue

                elements_copy = elements.copy()
                temp_elements = []
                jumped_idx = None  # 判断当前元素是否是需要跳过的被合并的部分
                for idx, element in enumerate(elements_copy):
                    # 合并元素的过程中需要跳过被合并的部分
                    if jumped_idx is not None and idx != jumped_idx:
                        continue

                    jumped_idx = None

                    head_start = element["pos_start"]
                    head_end = element["pos_end"]

                    # 要累加的
                    full_elem = element["element"]
                    full_length = element["length"]
                    pos_start = head_start
                    pos_end = head_end
                    if full_length > GENERAL_LIMIT:  # 这一个已经超了，不需要继续组合
                        temp_elements.append(element)
                        self._twine_combined_elements_data_flat.append(element)
                        continue

                    flag = False
                    for i in range(len(elements_copy) - idx):
                        """
                        eg: 元素可为012345
                        元素是2时, idx=2, len=6, i=0~3
                        i=0时指向元素2，i=3时指向元素5
                        所以需要把i=0跳过
                        """
                        if i == 0:  # i==0 指自己，因此跳过
                            continue

                        tail_elem = elements_copy[idx + i]["element"]
                        tail_end = elements_copy[idx + i]["pos_end"]
                        tail_length = elements_copy[idx + i]["length"]
                        full_length += tail_length
                        if full_length > GENERAL_LIMIT:  # 超了，只合并到上一处
                            combined = {
                                "filepath": filepath,
                                "passage": passage,
                                "element": full_elem,
                                "pos_start": pos_start,
                                "pos_end": pos_end,
                                "length": full_length - tail_length,
                            }
                            temp_elements.append(combined)
                            self._twine_combined_elements_data_flat.append(combined)
                            # flag 用来判断在推出循环时是否加上了
                            flag = True
                            # 同样需要跳过被合并的部分
                            jumped_idx = idx + i
                            break

                        # 确定不超限后再加上
                        full_elem = f"{full_elem}{tail_elem}"
                        pos_end = tail_end

                    # 说明在退出循环时当前的元素没有添加入内
                    if not flag:
                        combined = {
                            "filepath": filepath,
                            "passage": passage,
                            "element": full_elem,
                            "pos_start": pos_start,
                            "pos_end": pos_end,
                            "length": full_length,
                        }
                        temp_elements.append(combined)
                        self._twine_combined_elements_data_flat.append(combined)
                        break  # 到头了，所以直接退出循环

                # 用新组合后的替换掉之前的
                self._twine_combined_elements_data[filepath][passage] = temp_elements

        logger.info("所有元素已二次组合！")

    # 一次性函数，将旧汉化方式的译文、词条状态提取出详细信息
    def build_paratranz_detailed_raw_data(self):
        """一次性函数，将旧汉化方式的译文、词条状态提取出详细信息"""
        logger.info("开始生成旧汉化方式译文详细信息……")

        def _add_element(fp_: str, orig: str, trns: str, stg: int, info: list):
            data = {
                "filepath": fp_,
                "original": orig,
                "translation": trns,
                "stage": stg,
                "pos_info": info,
            }
            if fp_ not in self._paratranz_detailed_raw_data:
                self._paratranz_detailed_raw_data[fp_] = [data]
            else:
                self._paratranz_detailed_raw_data[fp_].append(data)

        for root, dirs, files in os.walk(DIR_PARATRANZ_EXPORT):
            if "失效" in root or "日志" in root or "测试" in root:
                continue

            for file in files:
                if ".js." in file:
                    # TODO 对 JS 的处理
                    continue
                else:
                    filename = file.replace(".csv.json", ".twee")
                filepath = Path(root) / filename
                filepath = Path().joinpath(*filepath.parts[filepath.parts.index("raw") + 1:]).__str__()

                # 文件在新版里没有，可能删了或者改名了
                if filepath not in self._twine_passage_data:
                    logger.warning(f"{filepath} 不存在！可能删改了！")
                    continue

                with open(Path(root) / file, "r", encoding="utf-8") as fp:
                    paratranz_raws: list[dict] = json.load(fp)

                for pz_raw in paratranz_raws:
                    original = pz_raw["original"]
                    translation = pz_raw["translation"]
                    stage = pz_raw["stage"]
                    pos_info = []

                    flag = False
                    for passage_name, passage_data in self._twine_passage_data[filepath].items():
                        passage_body: str = passage_data["passage_body"]

                        # 词条不在这个段落里
                        if original not in passage_body:
                            continue

                        # 可能出现多次，全部找到
                        original_re = re.escape(original)
                        matches = re.finditer(original_re, passage_body)
                        pos_info.extend([
                            {
                                "passage": passage_name,
                                "pos_start": match.start(),
                                "pos_end": match.end(),
                            }
                            for match in matches
                        ])
                        # 也有可能在所有段落中都找不到，这种情况下报错
                        flag = True

                    if not flag:
                        logger.error(f"！找不到词条 - {original} | {filepath}")

                    _add_element(filepath, original, translation, stage, pos_info)
        logger.info("旧汉化方式译文详细信息已生成！")

    # 一次性函数，用来将旧汉化方式的译文、词条状态迁移到新汉化方式用的
    def build_paratranz_combined_raw_data(self):
        for filepath, paratranz_detailed_datas in self._paratranz_detailed_raw_data.items():
            for paratranz_data in paratranz_detailed_datas:
                original = paratranz_data["original"]
                translation = paratranz_data["translation"]
                stage = paratranz_data["stage"]
                for pos_info in paratranz_data["pos_info"]:
                    passage = pos_info["passage"]
                    paratranz_pos_start = pos_info["pos_start"]
                    paratranz_pos_end = pos_info["pos_end"]

                    for element in self._twine_combined_elements_data[filepath][passage]:
                        element_pos_start = element["pos_start"]
                        element_pos_end = element["pos_end"]
                        # 情况1: pz 被 elem 包住
                        if (
                            element_pos_start < paratranz_pos_start
                            and element_pos_end > paratranz_pos_end
                        ):
                            ...

                        # 情况2:

    # 修改格式为可以在 paratranz 导入的文件
    def build_paratranz_format(self):
        """将结果转为可供 paratranz 识别的格式"""
        logger.info("开始修改为 paratranz 格式……")

        def _add_element(fp: str, pg: str, k: str, orig: str, trns: str, ctx: str, stg: int):
            """
            这是添加元素的，重复的部分提出来封装
            :param fp:      文件路径
            :param pg:      段落名
            :param k:       键，唯一标识
            :param orig:    原文
            :param trns:    译文
            :param ctx:     前后文，可不写
            :param stg:     未翻译 0/已翻译 1/有疑问 2/已检查 3/已审核 5/已锁定 9/已隐藏 -1
            """
            paratranz = {
                "key": k,
                "original": orig,
                "translation": trns,
                "context": ctx,
                "stage": stg,
            }
            if fp not in self._paratranz_elements_data:
                self._paratranz_elements_data[fp] = {pg: [paratranz]}
            elif pg not in self._paratranz_elements_data[fp]:
                self._paratranz_elements_data[fp][pg] = [paratranz]
            else:
                self._paratranz_elements_data[fp][pg].append(paratranz)

        for filepath, elements_data in self._twine_combined_elements_data.items():
            for passage, elements in elements_data.items():
                for idx, element in enumerate(elements):
                    key = f"{filepath.replace('.twee', '')}|{passage}|{idx}"
                    _add_element(filepath, passage, key, element["element"], "", "", 0)
        logger.info("已修改为 paratranz 格式！")

    # 导出为文件
    def export_data(self):
        """导出数据"""
        logger.info("开始导出所有文件……")
        with open(DIR_TARGET / "twine_passage_names.json", "w", encoding="utf-8") as fp:
            json.dump(self._twine_passage_names, fp, ensure_ascii=False, indent=2)

        with open(DIR_TARGET / "twine_passage_data.json", "w", encoding="utf-8") as fp:
            json.dump(self._twine_passage_data, fp, ensure_ascii=False, indent=2)

        with open(DIR_TARGET / "twine_elements_data.json", "w", encoding="utf-8") as fp:
            json.dump(self._twine_elements_data, fp, ensure_ascii=False, indent=2)

        with open(DIR_TARGET / "twine_combined_elements_data.json", "w", encoding="utf-8") as fp:
            json.dump(self._twine_combined_elements_data, fp, ensure_ascii=False, indent=2)

        with open(DIR_TARGET / "twine_combined_elements_data_flat.json", "w", encoding="utf-8") as fp:
            json.dump(self._twine_combined_elements_data_flat, fp, ensure_ascii=False, indent=2,)

        with open(DIR_TARGET / "paratranz_detailed_raw_data.json", "w", encoding="utf-8") as fp:
            json.dump(self._paratranz_detailed_raw_data, fp, ensure_ascii=False, indent=2)

        with open(DIR_TARGET / "paratranz_elements_data.json", "w", encoding="utf-8") as fp:
            json.dump(self._paratranz_elements_data, fp, ensure_ascii=False, indent=2)
        logger.info("所有文件已导出！")


def main():
    parser = ParseTwine()
    parser.init_dirs()
    parser.parse()
    parser.export_data()


if __name__ == "__main__":
    main()

__all__ = ["ParseTwine"]
