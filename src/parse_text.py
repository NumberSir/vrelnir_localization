from typing import List
import re


# TODO
REGEX_PATTERNS = {
    "macro": r"""<<(/)?([A-Za-z][\w-]*|[=-])(?:\s*)((?:(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)|(?://.*\n)|(?:`(?:\\.|[^`\\\n])*?`)|(?:"(?:\\.|[^"\\\n])*?")|(?:'(?:\\.|[^'\\\n])*?')|(?:\[(?:[<>]?[Ii][Mm][Gg])?\[[^\r\n]*?\]\]+)|[^>]|(?:>(?!>)))*?)(/)?>>""",
    "tag": r"""(?<!\<)<(?:/)?[a-zA-Z]+.*?>(?:[\s\S]*?)""",
    "variable": r"""(?:(\$|_)(?:[A-Za-z_\$][A-Za-z0-9_\$]*))((?:\.[A-Za-z_\$][A-Za-z0-9_\$]*)*)\b""",
    "comment": r""""""
}


# TODO
# class ParseText:
#     def __init__(self):
#         self._high_rates: List[str] = ...
#         self._type: str = ...
#         self._lines: List[str] = ...
#
#     async def async_init(self, lines: List[str], type_: str = None, high_rates: List[str] = None) -> "ParseText":
#         self._lines = lines
#         self._type = type_
#         self._high_rates = high_rates
#         return self
#
#     async def parse(self):
#         ...
#
#     def find_macros(self, line: str):
#         """提出 <<MACROS>> """
#         macros = re.findall(REGEX_PATTERNS["macro"], line)
#
#     def _macro_script(self):
#         """<<script>> 通常不翻译"""
#
#     def _macro_link(self):
#         """<<link>> 通常要翻译"""
#
#     def _macro_set(self):
#         """<<set>> 通常要翻译"""
#
#     def find_tags(self, line: str):
#         """提出 <TAGS> """
#         tags = re.findall(REGEX_PATTERNS["tag"], line)
#
#     def _tag_span(self):
#         """<span> 通常要翻译"""
#
#     def find_variables(self, line: str):
#         """提出 $VARS """
#         vars = re.findall(REGEX_PATTERNS["variable"], line)
#
#     def find_comments(self):
#         """提出 //C /*C*/ <!--C--> """


class ParseText:
    """提取出要翻译的文本"""

    def __init__(self):
        self._high_rates: List[str] = ...
        self._type: str = ...
        self._lines: List[str] = ...

    async def async_init(self, lines: List[str], type_: str = None, high_rates: List[str] = None) -> "ParseText":
        self._lines = lines
        self._type = type_
        self._high_rates = high_rates
        return self

    async def parse(self) -> List[bool]:
        """导出要翻译的行"""
        if self._type == "cloth":
            return await self.parse_cloth()
        elif self._type == "plant":
            return await self.parse_plant()
        elif self._type == "trait":
            return await self.parse_trait()
        elif self._type == "option":
            return await self.parse_option()
        elif self._type == "canvas":
            return await self.parse_canvas()
        elif self._type == "image":
            return await self.parse_image()
        elif self._type == "init":
            return await self.parse_init()
        elif self._type == "generation":
            return await self.parse_generation()
        elif self._type == "name":
            return await self.parse_name()
        return await self.parse_normal()

    async def parse_cloth(self) -> List[bool]:
        """衣服"""
        return [
            "name_cap" in line.strip() or "description" in line.strip()
            for line in self._lines
        ]

    async def parse_plant(self) -> List[bool]:
        """种地"""
        return [
            "plural:" in line.strip()
            for line in self._lines
        ]

    async def parse_trait(self) -> List[bool]:
        """特性"""
        return [
            any((_ in line.strip() for _ in {"name:", "text:", "title:", "<summary", "<<option"}))
            for line in self._lines
        ]

    async def parse_option(self) -> List[bool]:
        """设置"""
        results = []
        multirow_comment_flag = False
        for line in self._lines:
            line = line.strip()
            """偶尔会出现的跨行注释"""
            if line in ["/*", "<!--"] or (any(line.startswith(_) for _ in {"/*", "<!--"}) and all(_ not in line for _ in {"*/", "-->"})):
                multirow_comment_flag = True
            elif line in ["*/", "-->"] or any(line.endswith(_) for _ in {"*/", "-->"}):
                multirow_comment_flag = False

            if multirow_comment_flag or not line:
                results.append(False)
            elif any((_ in line for _ in {"<<link", "<<option", "description", "<span class", "<div class"})):
                results.append(True)
            elif self.is_single_widget(line) or self.is_comment(line):
                results.append(False)
            else:
                results.append(True)
        return results

    async def parse_canvas(self) -> List[bool]:
        """壁纸吗"""
        return [
            "<<link" in line.strip()
            for line in self._lines
        ]

    async def parse_image(self) -> List[bool]:
        """图片显示"""
        return [
            "<<error {" in line.strip() or "<span" in line.strip()
            for line in self._lines
        ]

    async def parse_init(self) -> List[bool]:
        """初始设置"""
        results = []
        multirow_comment_flag = False
        for line in self._lines:
            line = line.strip()
            """偶尔会出现的跨行注释"""
            if not multirow_comment_flag and line in ["/*", "<!--"] or (any(line.startswith(_) for _ in {"/*", "<!--"}) and all(_ not in line for _ in {"*/", "-->"})):
                multirow_comment_flag = True
            elif multirow_comment_flag and line in ["*/", "-->"] or any(line.endswith(_) for _ in {"*/", "-->"}):
                multirow_comment_flag = False

            if multirow_comment_flag or not line or self.is_comment(line) or self.is_event(line) or self.is_only_marks(line) or ("[[" in line and self.is_high_rate_link(line)) or self.is_single_widget(line):
                results.append(False)
            elif "desc" in line or "<span" in line:
                results.append(True)
            else:
                results.append(True)

        return results

    async def parse_generation(self) -> List[bool]:
        """生成"""
        return [
            "<span" in line.strip()
            for line in self._lines
        ]

    async def parse_name(self) -> List[bool]:
        """名称"""
        return [
            '"' in line.strip()
            for line in self._lines
        ]

    async def parse_normal(self) -> List[bool]:
        """常规"""
        results = []
        multirow_comment_flag = False
        for line in self._lines:
            line = line.strip()
            """偶尔会出现的跨行注释"""
            if line in ["/*", "<!--"] or (any(line.startswith(_) for _ in {"/*", "<!--"}) and all(_ not in line for _ in {"*/", "-->"})):
                multirow_comment_flag = True
            elif line in ["*/", "-->"] or any(line.endswith(_) for _ in {"*/", "-->"}):
                multirow_comment_flag = False

            if multirow_comment_flag or not line or self.is_comment(line) or self.is_event(line) or self.is_only_marks(line) or ("[[" in line and self.is_high_rate_link(line)):
                results.append(False)
            elif "[[" in line or self.is_assignment(line):
                results.append(True)
            elif self.is_single_widget(line):
                results.append(False)
            else:
                results.append(True)
        return results

    @staticmethod
    def is_high_rate_link(line: str) -> bool:
        """高频选项"""
        return bool(re.findall(r"<<link\s\[\[(Next\||Next\s\||Leave\||Refuse\||Return\|)", line))

    @staticmethod
    def is_only_marks(line: str) -> bool:
        """只有符号没字母数字"""
        return not any(re.findall(r"([A-z\d]*)", line))

    @staticmethod
    def is_event(line: str) -> bool:
        """事件"""
        return line.startswith("::")

    @staticmethod
    def is_comment(line: str) -> bool:
        """注释"""
        return any(line.startswith(_) for _ in {"/*", "<!--", "*/", "*"})

    @staticmethod
    def is_assignment(line: str) -> bool:
        """专指 <<>>, < > 可能出现的特殊情况"""
        set_to = re.findall(r'<<set.*?[\"`\']', line)
        note = re.findall(r"<<note\s\"", line)
        link = re.findall(r"<<link\s[\"`]", line)
        action = re.findall(r"<<actionstentacleadvcheckbox\s[\"`]", line)
        option = re.findall(r'<<option\s\"', line)
        button = re.findall(r'<<button\s', line)
        input_ = re.findall(r'<input.*?value=\"', line)
        return any((set_to, note, link, action, option, button, input_))

    @staticmethod
    def is_single_widget(line: str) -> bool:
        """单独的 <<>>, <>, $VAR"""
        if "<" not in line and "$" not in line:
            return False

        widgets = {_ for _ in re.findall(r"(<<[^\n<>]*?>>)", line) if _}
        for w in widgets:
            if "[[" not in w or ("[" in w and '"' not in w and "'" not in w and "`" not in w):
                line = line.replace(w, "", -1)

        if "<" not in line and "$" not in line:
            return (not line.strip()) or ParseText.is_comment(line.strip()) or False
        tags = {_ for _ in re.findall(r"(<[/\sA-z\"=]*>)", line) if _}
        for t in tags:
            line = line.replace(t, "", -1)

        if "$" not in line:
            return (not line.strip()) or ParseText.is_comment(line.strip()) or False

        vars_ = {_ for _ in re.findall(r"(\$[A-z\._\(\)]*)", line) if _}
        for v in vars_:
            line = line.replace(v, "", -1)
        return (not line.strip()) or ParseText.is_comment(line.strip()) or False

    @staticmethod
    def is_half_widget(line: str) -> bool:
        """只有一半 <<, >>, <, >"""
        return any((
            "<<" in line and ">>" not in line,
            ">>" in line and "<<" not in line,
            "<" in line and ">" not in line,
            ">" in line and "<" not in line
        ))


__all__ = [
    "ParseText"
]

if __name__ == '__main__':
    import asyncio
    async def main():
        lines = ["""<span class="red">Your <<genitalsintegrity>> $worn.genitals.name <<if playerChastity("anus")>>with an anal shield<</if>> gives you no comfort.</span>"""]
        return await (await ParseText().async_init(lines=lines)).parse()

    print(asyncio.run(main()))

