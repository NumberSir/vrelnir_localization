"""
如:
<<set VAR ...>>
<<if VAR ...>>
<<run VAR ...>>
"""
import asyncio
import json
import os
import re
from enum import Enum
from pathlib import Path
from pprint import pprint

from src import logger
from src.consts import *
from aiofiles import open as aopen

SELF_ROOT = Path(__file__).parent

set_CONTENTS = None

FREQ_FUNCTIONS = {
    ".push(",
    ".pushUnique(",
    ".delete(",
    ".deleteAt(",
    ".splice("
}


class Regexes(Enum):
    VARS_REGEX = re.compile("""([$_][$A-Z_a-z][$0-9A-Z_a-z]*)""")

    SET_RUN_REGEXES: re.Pattern = re.compile("""<<(run|set)(?:\s+((?:(?:\/\*[^*]*\*+(?:[^/*][^*]*\*+)*\/)|(?:\/\/.*\n)|(?:`(?:\\.|[^`\\\n])*?`)|(?:"(?:\\.|[^"\\\n])*?")|(?:'(?:\\.|[^'\\\n])*?')|(?:\[(?:[<>]?[Ii][Mm][Gg])?\[[^\r\n]*?\]\]+)|[^>]|(?:>(?!>)))*?))?>>""")


class VariablesProcess:
    """我再也不会不写注释了"""
    def __init__(self):
        self._all_file_paths = set()  # 所有 .twee 文件绝对路径

        self._categorize_variables = []  # 所有 .twee 文件中的变量分类：{path, variables}
        self._all_variables = []  # 所有 .twee 文件中的变量

        self._categorize_all_set_contents = []
        self._all_set_contents = []
        self._categorize_all_needed_translated_set_contents = []
        self._all_needed_translated_set_contents = []

    def fetch_all_file_paths(self) -> set[Path]:
        """ 获取所有 .twee 文件绝对路径"""
        for root, dir_list, file_list in os.walk(DIR_GAME_TEXTS_COMMON):
        # for root, dir_list, file_list in os.walk(DIR_GAME_TEXTS_DEV):
            for file in file_list:
                if file.endswith(SUFFIX_TWEE):
                    self._all_file_paths.add(Path(root).absolute() / file)
        return self._all_file_paths

    async def fetch_all_variables(self) -> None:
        """ 获取所有 .twee 文件中存在的变量，写入文件，创建 vars 目录 """
        tasks = {
            self._fetch_all_variables(file)
            for file in self._all_file_paths
        }

        await asyncio.gather(*tasks)
        os.makedirs(SELF_ROOT / "vars", exist_ok=True)

        with open(SELF_ROOT / "vars" / "_variables.json", "w", encoding="utf-8") as fp:
            # self._categorize_variables = sorted(self._categorize_variables)
            json.dump(self._categorize_variables, fp, ensure_ascii=False, indent=2)

        with open(SELF_ROOT / "vars" / "_all_variables.json", "w", encoding="utf-8") as fp:
            json.dump(sorted(list(set(self._all_variables))), fp, ensure_ascii=False, indent=2)

    async def _fetch_all_variables(self, file: Path):
        """ 异步任务用 """
        filename = file.name
        async with aopen(file, "r", encoding="utf-8") as fp:
            raw = await fp.read()
        variables = re.findall(Regexes.VARS_REGEX.value, raw)
        
        if not variables:
            return

        self._categorize_variables.append({
            "path": str(file).split("\\game\\")[1],
            "variables": sorted(list(set(variables)))
        })
        self._all_variables.extend(list(set(variables)))
    
    async def build_variables_notations(self):
        """ 哪些变量可以翻译，写入文件，暂时弃用 """
        filepath = DIR_DATA_ROOT / "json" / "variables_notations.json"

        old_data = {}
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as fp:
                old_data: dict = json.load(fp)

        new_data = {
            var: {
                "var": var,
                "desc": "",
                "canBeTranslated": False
            } for var in self._all_variables
        }

        if old_data:
            for key, items in old_data.items():
                if items["desc"]:
                    new_data[key] = items

        with open(DIR_DATA_ROOT / "json" / "variables_notations.json", "w", encoding="utf-8") as fp:
            json.dump(new_data, fp, ensure_ascii=False, indent=2)

    def fetch_all_set_content(self):
        """ 获取所有 <<set>> 内容，写入 setto 目录里，有了就不要再创建了"""
        global set_CONTENTS

        if set_CONTENTS:
            return set_CONTENTS

        if (SELF_ROOT / "setto" / "_set_contents.json").exists():
            with open(SELF_ROOT / "setto" / "_set_contents.json", "r", encoding="utf-8") as fp:
                data = json.load(fp)
            set_CONTENTS = data
            return data

        for file in self._all_file_paths:
            self._fetch_all_set_content(file)

        set_CONTENTS = self._categorize_all_set_contents
        os.makedirs(SELF_ROOT / "setto", exist_ok=True)
        with open(SELF_ROOT / "setto" / "_set_contents.json", "w", encoding="utf-8") as fp:
            json.dump(self._categorize_all_set_contents, fp, ensure_ascii=False, indent=2)

        # ALL_NEEDED_TRANSLATED_set_CONTENTS = self._categorize_all_needed_translated_set_contents
        # with open(SELF_ROOT / "setto" / "_needed_translated_set_contents.json", "w", encoding="utf-8") as fp:
        #     json.dump(self._categorize_all_needed_translated_set_contents, fp, ensure_ascii=False, indent=2)
		#
        # self._all_set_contents = sorted(list(set(self._all_set_contents)))
        # with open(SELF_ROOT / "setto" / "_all_set_contents.json", "w", encoding="utf-8") as fp:
        #     json.dump(self._all_set_contents, fp, ensure_ascii=False, indent=2)
		#
        # self._all_needed_translated_set_contents = sorted(list(set(self._all_needed_translated_set_contents)))
        # with open(SELF_ROOT / "setto" / "_all_needed_translated_set_contents.json", "w", encoding="utf-8") as fp:
        #     json.dump(self._all_needed_translated_set_contents, fp, ensure_ascii=False, indent=2)

        return self._categorize_all_set_contents

    def _fetch_all_set_content(self, file: Path):
        """ 异步任务用 """
        filename = file.name
        with open(file, "r", encoding="utf-8") as fp:
            raw = fp.read()
        all_set_contents = re.findall(Regexes.SET_RUN_REGEXES.value, raw)
        """
        标准语法:
        <<set EXPRESSION>>
        
        1. 有明显标识符分割的:
          - set X to Y
          - set X is Y
          - set X = Y (+=, -=, *=, /=, %=)
        2. 没有明显标识符分割的:
          - set {X:Y, ...}
          - set X
          - set X[Y]
          - set X["Y"] ('', ``)
          - set X++ (--)
          - set X.FUNC(Y)
        """

        if len(all_set_contents) < 2:
            return

        # FIXME: 开摆，不分类了，全部提取出来。
        self._categorize_all_set_contents.append({
	        "path": file.__str__(),
	        "lines": list({
		        f"<<{head} {args}>>"
		        for (head, args) in all_set_contents
	        })
        })

        # all_heads, all_set_contents = [_[0] for _ in all_set_contents], [_[1] for _ in all_set_contents]
        # var_targets_dict = {}
        # var_lines_dict = {}
        # for idx, content in enumerate(all_set_contents):
        #     head = all_heads[idx]
        #     var, target, line = self._process_content(head, content)
        #     if not any({var, target, line}):
        #         continue
		#
        #     if var in var_targets_dict:
        #         var_targets_dict[var].append(target)
        #     else:
        #         var_targets_dict[var] = [target]
		#
        #     if var in var_lines_dict:
        #         var_lines_dict[var].append(line)
        #     else:
        #         var_lines_dict[var] = [line]
		#
        # self._categorize_all_set_contents.append({
        #     "path": file.__str__(),
        #     "vars": [
        #         {"var": var, "targets": targets, "lines": lines}
        #         for (var, targets), (var_, lines) in zip(
        #             var_targets_dict.items(),
        #             var_lines_dict.items()
        #         )
        #     ]
        # })
		#
        # all_set_contents = [
        #     f"set {content}"
        #     for content in all_set_contents
        # ]
        # self._all_set_contents.extend(list(set(all_set_contents)))
		#
        # vars_ = []
        # for (var, targets), (var_, lines) in zip(
        #     var_targets_dict.items(),
        #     var_lines_dict.items()
        # ):
        #     targets_ = [
        #         target
        #         for target in targets
        #         if self.is_needed_translated(target)
        #     ]
        #     lines_ = [
        #         lines[idx]
        #         for idx, target in enumerate(targets)
        #         if self.is_needed_translated(target)
        #     ]
        #     # if not targets_:
        #     #     continue
        #     vars_.append({"var": var, "targets": targets_, "lines": lines_})
		#
        # if vars_:
        #     self._categorize_all_needed_translated_set_contents.append({
        #         "path": file.__str__(),
        #         "vars": vars_
        #     })
		#
        #     vars_needed_translated = {var_item["var"] for var_item in vars_}
        #     self._all_needed_translated_set_contents.extend(list(set([
        #         content
        #         for content in all_set_contents
        #         if content.split(" ")[1] in vars_needed_translated
        #     ])))

    def _process_content(self, head: str,  content: str):
        """
        :param content: <<set content>>
        """
        content: str

        var = content
        target = content

        # 1. 一定不是字符串的
        if content.endswith("++") or content.endswith("--"):
            return None, None, None
        elif "Time.set" in content:
            return None, None, None

        # 2. 有明显分隔符的
        elif re.findall(r"\sto", content):
            var, target = re.split(r"\sto", content, 1)
        elif re.findall(r"[+\-*/%]*=", content):
            var, target = re.split(r"[+\-*/%]*=", content, 1)
        elif re.findall(r"\sis\s", content):
            var, target = re.split(r"\sis\s", content, 1)

        # 3. 纯函数/纯变量
        # 数量比较多的
        elif any(
            f in content
            for f in FREQ_FUNCTIONS
        ):
            for f_ in FREQ_FUNCTIONS:
                if f_ not in content:
                    continue
                vars_ = re.findall(Regexes.VARS_REGEX.value, content)
                if not vars_:
                    return None, None, None
                var = vars_[0]
                target = content.split(f_)[-1]
                break

        # 括号包起来的就是 target
        elif "(" in content:
            vars_ = re.findall(Regexes.VARS_REGEX.value, content)
            if not vars_:
                return None, None, None
            var = vars_[0]
            target = "(".join(content.split("(")[1:]).rstrip(")")
        # 没括号，纯变量
        else:
            vars_ = re.findall(Regexes.VARS_REGEX.value, content)
            if not vars_:
                return None, None, None
            var = vars_[0]
            target = content

        var = var.strip()
        target = target.strip()
        line = f"<<{head} {content}>>"

        if target.isnumeric():
            target = float(target)
        elif target in {"true", "false"}:
            target = target == "true"
        elif target == "null":
            target = None

        return var, target, line

    @staticmethod
    def is_needed_translated(target: str):
        return (
            False
            if target is None
            else not isinstance(target, (float, bool))
        )


def main():
    var = VariablesProcess()
    var.fetch_all_file_paths()
    var.fetch_all_set_content()
    # await var.fetch_all_variables()
    # await var.build_variables_notations()

if __name__ == '__main__':
    # line = "$_clothes[$_revealType].pushUnique($_wornClothing.name)"
    # def test():
    #     vp = VariablesProcess()
    #     vp.fetch_all_file_paths()
    #     return vp._process_content(line, {}, {})
    #
    # result = test()
    # pprint(result)
    main()

__all__ = [
    "VariablesProcess"
]
