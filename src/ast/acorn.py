import dukpy
from src import *
from dataclasses import dataclass, asdict
from typing import Literal, Union, TypedDict, Callable, Any
from typing_extensions import Self
from types import FunctionType

DIR_JS_MODULE_ROOT = DIR_DATA_ROOT / "jsmodule"
DIR_ARCON_ROOT = DIR_JS_MODULE_ROOT / "acorn"
SOURCE_TYPE = Literal['script', 'module']
ECMA_VERSION = Literal[
    3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 'latest']
REGISTER_FUNC = """
function registerFunc(key) {
        return function () { var param = Array.prototype.slice.call(arguments); return call_python.call.apply(call_python, [null, key].concat(param)); };
}
"""


class Position(TypedDict):
    line: int
    column: int
    offset: int


class TokenType(TypedDict, total=False):
    label: str
    keyword: str
    beforeExpr: bool
    startsExpr: bool
    isLoop: bool
    isAssign: bool
    prefix: bool
    postfix: bool
    binop: int
    updateContext: Callable[[Self], None] | None  # Optional[] 是 3.9 之前的写法


class SourceLocation(TypedDict):
    start: Position
    end: Position
    source: str | None


class Token(TypedDict):
    type: TokenType
    value: Any
    start: int
    end: int
    range: list[int] | None
    loc: SourceLocation | None


class Comment(TypedDict):
    type: Literal['Line', 'Block']
    value: str
    start: int
    end: int
    range: list[int] | None
    loc: SourceLocation | None


class AcornOptionParam(TypedDict, total=False):
    ecmaVersion: ECMA_VERSION
    sourceType: SOURCE_TYPE
    ranges: bool
    preserveParens: bool
    locations: bool
    checkPrivateFields: bool
    allowHashBang: bool
    allowReturnOutsideFunction: bool
    allowImportExportEverywhere: bool
    allowReserved: bool | None
    allowAwaitOutsideFunction: bool | None
    allowSuperOutsideMethod: bool | None
    onInsertedSemicolon: Callable[[int, Position | None], None]
    onTrailingComma: Callable[[int, Position | None], None]
    onToken: Union[Callable[[Token], None], list[Token]]
    onComment: Union[Callable[[bool, str, int, int, Position | None, int, Position | None], None], list[Token]]


@dataclass
class AcornOption:
    ecmaVersion: ECMA_VERSION = 2020
    sourceType: SOURCE_TYPE = "script"
    ranges: bool = False
    preserveParens: bool = False
    locations: bool = False
    checkPrivateFields: bool = True
    allowHashBang: bool = False
    allowReturnOutsideFunction: bool = False
    allowImportExportEverywhere: bool = False
    allowReserved: bool | None = None
    allowAwaitOutsideFunction: bool | None = None
    allowSuperOutsideMethod: bool | None = None
    onToken = None
    onComment = None

    def to_dict(self):
        return {
            k: str(v) if v is not None else None 
            for k, v in asdict(self).items()
        }

    @staticmethod
    def parse_option(option: AcornOptionParam = None):
        if option is None:
            option = {}
        _option = {}
        func = {}
        for key, value in option.items():
            if hasattr(AcornOption, key) and not isinstance(value, FunctionType):
                _option[key] = value
            if isinstance(value, FunctionType):
                func[key] = value
        return AcornOption(**_option).to_dict(), func


@dataclass
class JSSyntaxError(Exception):
    pos: int = -1
    loc: dict[str, int] = dict
    raisedAt: int = -1
    name: str = ""
    message: str = ""
    def to_string(self):
        return f"{self.name}:{self.message}({self.line}行:{self.column}位)"
    def __str__(self):
        return self.to_string()
    @property
    def line(self):
        return  self.loc["line"] if "line" in self.loc else -1

    @property
    def column(self):
        return self.loc["column"]if "column" in self.loc else -1
    def err_code(self,code:list[str]):
        res = code[self.line - 1]
        column = self.column
        err_str = ""
        if column < len(res):
            # char = res[column]
            # res = res.replace(char,f"<b><u>{char}</u></b>",column)
            line_str= len(str(self.line))
            err_str += "<W>"
            for _ in range(line_str):
                err_str += " "
            err_str +="</W> "
            for _ in range(column):
                err_str += " "
            err_str +="<r>~</r>"
        msg = f"<r>{self.to_string()}</r>\n<W><k>{self.line}</k></W> {res}"
        if err_str != "":
            msg += "\n" + err_str
        return msg

class Acorn:
    def __init__(self):
        self._jsi = dukpy.JSInterpreter()
        self._jsi.loader.register_path(DIR_JS_MODULE_ROOT / "acorn" / "dist")

    @property
    def jsi(self):
        return self._jsi


    def parse(self, code_text:str, option:AcornOptionParam = None):
        self.install_dep()
        arcon_option,func= AcornOption.parse_option(option)
        # print(arcon_option)
        code = [REGISTER_FUNC,"var acorn = require('acorn')","function parseArcon() {var option = Object.assign({},dukpy['option']); try{"]
        for key, value in func.items():
            code.append(f"option['{key}'] = registerFunc('{key}')")
            self._jsi.export_function(key,value)
        code.extend(("var result =acorn.parse(dukpy['code_text'], option);return result}catch (e){if (!(e instanceof SyntaxError)) throw e;var err = Object.assign({}, e); err.name = e.name;err.message = e.message;return err;}}", "parseArcon()"))
        result = self._jsi.evaljs(code, code_text= code_text, option =arcon_option)
        if "name" in result and result["name"] == 'SyntaxError':
            raise JSSyntaxError(**result)
        return result

    @staticmethod
    def install_dep():
        if not DIR_ARCON_ROOT.exists():
            dukpy.install_jspackage("acorn", None, DIR_ARCON_ROOT)


__all__ = [
    "DIR_JS_MODULE_ROOT",
    "DIR_ARCON_ROOT",

    "AcornOptionParam",
    "AcornOption",
    "Acorn",

    "Position",
    "TokenType",
    "SourceLocation",
    "Token",
    "Comment",
    "JSSyntaxError"

]
