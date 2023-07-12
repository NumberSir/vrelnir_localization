import  dukpy
from src import *
from dataclasses import  dataclass, asdict
from typing import Optional,Literal,NewType,Union,TypedDict

__all__ = ["DIR_JS_MODULE_ROOT","DIR_ARCON_ROOT","ArconOptionParam","ArconOption","Arcon"]
DIR_JS_MODULE_ROOT = DIR_DATA_ROOT / "jsmodule"
DIR_ARCON_ROOT = DIR_JS_MODULE_ROOT / "acorn"
SOURCE_TYPE = Literal['script','module']
ECMA_VERSION = Literal[ 3, 5 , 6 , 7 , 8 , 9 , 10 , 11 , 12 , 13 , 14 , 15 , 2015 , 2016 , 2017 , 2018 ,2019 , 2020 , 2021 , 2022,  2023 , 2024 , 'latest']
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
    def to_dict(self):

        return  {k:str(v) if v is not None else None for k, v in asdict(self).items()}
    @staticmethod
    def parse_option(option:ArconOptionParam =None ):
        if option is None:
            option = {}
        return  ArconOption(**option).to_dict()

class Arcon:
    def __init__(self):
        self._jsi = dukpy.JSInterpreter()
        self._jsi.loader.register_path(DIR_JS_MODULE_ROOT/ "acorn"/"dist")
    def parse(self,code:str,option:ArconOptionParam = None):
        self.install_dep()
        arcon_option= ArconOption.parse_option(option)
        # print(arcon_option)
        return self._jsi.evaljs(["var acorn = require('acorn')","var result =acorn.parse(dukpy['code_text'],dukpy['option'])","result"],code_text= code,option =arcon_option)
    @staticmethod
    def install_dep():
        if not DIR_ARCON_ROOT.exists():
            dukpy.install_jspackage("acorn",None,DIR_ARCON_ROOT)

# arcon=Arcon()
# print(arcon.parse("test\n\nvar a = 1 +1",{'ecmaVersion':2022,'sourceType':'script'}))