from typing import List
import re


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
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
            elif any((_ in line for _ in {"<<link", "<<option", "description", "<span class", "<div class"})):
                results.append(True)
            elif self.is_single_widget(line) or self.is_comment(line):
                results.append(False)
            else:
                results.append(True)
        return results

    async def parse_normal(self) -> List[bool]:
        """常规"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line or self.is_comment(line) or self.is_event(line) or self.is_only_marks(line) or ("[[" in line and self.is_high_rate_link(line)):
                results.append(False)
            elif "[[" in line or self.is_assignment(line) or self.is_option(line):
                results.append(True)
            elif self.is_single_widget(line) or self.is_half_widget(line):
                results.append(False)
            else:
                results.append(True)
        return results

    @staticmethod
    def is_high_rate_link(line: str) -> bool:
        """高频选项"""
        return bool(re.findall(r"<<link\s\[\[(Next)|(Leave)|(Refuse)|(Return)", line))

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
        return any(line.startswith(_) for _ in {"//", "/*", "<!--", "*/", "*"})

    @staticmethod
    def is_assignment(line: str) -> bool:
        """专指 <<set>> 可能出现的特殊情况"""
        set_to = re.findall(r'<<set.*?to\s\"', line)
        return bool(set_to)

    @staticmethod
    def is_option(line: str) -> bool:
        """专指 <<option>> 可能出现的特殊情况"""
        set_to = re.findall(r'<<option\s\"', line)
        return bool(set_to)

    @staticmethod
    def is_single_widget(line: str) -> bool:
        """单独的 <<>>, <>, $VAR"""
        if "<" not in line and "$" not in line:
            return False

        widgets = {_ for _ in re.findall(r"(<<.*[^\[\n].*?>>)", line) if _}
        for w in widgets:
            line = line.replace(w, "", -1)

        if "<" not in line and "$" not in line:
            return (not line.strip()) or ParseText.is_comment(line.strip()) or False
        tags = {_ for _ in re.findall(r"(<[/\sA-z\"=]*>)", line) if _}
        for t in tags:
            line = line.replace(t, "", -1)

        if "$" not in line:
            return (not line.strip()) or ParseText.is_comment(line.strip()) or False

        vars_ = {_ for _ in re.findall(r"(\$[A-z])]", line) if _}
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
