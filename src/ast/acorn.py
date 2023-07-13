import  dukpy
from src import *
from dataclasses import  dataclass, asdict
from typing import Optional,Literal,NewType,Union,TypedDict,Callable,Any
from typing_extensions import Self
from types import  FunctionType,LambdaType


DIR_JS_MODULE_ROOT = DIR_DATA_ROOT / "jsmodule"
DIR_ARCON_ROOT = DIR_JS_MODULE_ROOT / "acorn"
SOURCE_TYPE = Literal['script','module']
ECMA_VERSION = Literal[ 3, 5 , 6 , 7 , 8 , 9 , 10 , 11 , 12 , 13 , 14 , 15 , 2015 , 2016 , 2017 , 2018 ,2019 , 2020 , 2021 , 2022,  2023 , 2024 , 'latest']
REGISTER_FUNC = """
function registerFunc(key) {
        return function () { var param = Array.prototype.slice.call(arguments); return call_python.call.apply(call_python, [null, key].concat(param)); };
}
"""
class Position(TypedDict):
    line:int
    column:int
    offset:int

class TokenType(TypedDict,total = False):
    label: str
    keyword: str
    beforeExpr: bool
    startsExpr: bool
    isLoop: bool
    isAssign: bool
    prefix: bool
    postfix: bool
    binop: int
    updateContext: Optional[Callable[[Self],None]]
class SourceLocation(TypedDict):
    start: Position
    end: Position
    source: Optional[str]
class Token(TypedDict):
    type:TokenType
    value:Any
    start: int
    end: int
    range:Optional[list[int]]
    loc:Optional[SourceLocation]
class Comment(TypedDict):
    type:Literal['Line' ,'Block']
    value: str
    start: int
    end: int
    range: Optional[list[int]]
    loc: Optional[SourceLocation]
class ArconOptionParam(TypedDict,total = False):
    ecmaVersion: ECMA_VERSION
    sourceType: SOURCE_TYPE
    ranges:bool
    preserveParens: bool
    locations:bool
    checkPrivateFields:bool
    allowHashBang:bool
    allowReturnOutsideFunction:bool
    allowImportExportEverywhere:bool
    allowReserved:Optional[bool]
    allowAwaitOutsideFunction:Optional[bool]
    allowSuperOutsideMethod:Optional[bool]
    onInsertedSemicolon:Callable[[int,Optional[Position]],None]
    onTrailingComma:Callable[[int,Optional[Position]],None]
    onToken:Union[Callable[[Token],None],list[Token]]
    onComment:Union[Callable[[bool,str,int,int,Optional[Position],int,Optional[Position]],None],list[Token]]

@dataclass
class ArconOption:
    ecmaVersion:ECMA_VERSION = 2020
    sourceType:SOURCE_TYPE   = "script"
    ranges: bool =False
    preserveParens: bool =False
    locations: bool =False
    checkPrivateFields: bool=True
    allowHashBang: bool =False
    allowReturnOutsideFunction: bool =False
    allowImportExportEverywhere: bool=False
    allowReserved: Optional[bool] =None
    allowAwaitOutsideFunction: Optional[bool]=None
    allowSuperOutsideMethod: Optional[bool]=None
    onToken = None
    onComment = None
    def to_dict(self):

        return  {k:str(v) if v is not None else None for k, v in asdict(self).items()}
    @staticmethod
    def parse_option(option:ArconOptionParam =None ):
        if option is None:
            option = {}
        _option = {}
        func = {}
        for key,value in option.items():
            if hasattr(ArconOption,key) and not isinstance(value,FunctionType):
                _option[key] = value
            if isinstance(value,FunctionType):
                func[key] = value
        return  ArconOption(**_option).to_dict(),func

class Arcon:
    def __init__(self):
        self._jsi = dukpy.JSInterpreter()
        self._jsi.loader.register_path(DIR_JS_MODULE_ROOT/ "acorn"/"dist")
    @property
    def jsi(self):
        return self._jsi
    def parse(self,code_text:str,option:ArconOptionParam = None):
        self.install_dep()
        arcon_option,func= ArconOption.parse_option(option)
        # print(arcon_option)
        code = ["var acorn = require('acorn')",REGISTER_FUNC,"var option = Object.assign({},dukpy['option'])"]
        for key, value in func.items():
            code.append(f"option['{key}'] = registerFunc('{key}')")
            self._jsi.export_function(key,value)
        code.extend(("var result =acorn.parse(dukpy['code_text'], option)", "result"))
        return self._jsi.evaljs(code,code_text= code_text,option =arcon_option)
    @staticmethod
    def install_dep():
        if not DIR_ARCON_ROOT.exists():
            dukpy.install_jspackage("acorn",None,DIR_ARCON_ROOT)
__all__ = [
    "DIR_JS_MODULE_ROOT",
    "DIR_ARCON_ROOT",

    "ArconOptionParam",
    "ArconOption",
    "Arcon",

    "Position",
    "TokenType",
    "SourceLocation",
    "Token",
    "Comment",

]
# def on_token(token):
#     print(token)
# arcon=Arcon()
# print(REGISTER_FUNC)
# print(arcon.parse("test\n\nvar a = 1 +1",ArconOptionParam(ecmaVersion=2020,sourceType='script',onToken= lambda token:print(token))))