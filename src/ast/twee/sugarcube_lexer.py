from dataclasses import dataclass
from typing import Union, List, Callable,Optional
from typing_extensions import Self
from enum import Enum, auto
@dataclass
class SugarCubeLexerState:
    LexNone = 0
    LexSpace = auto()
    LexBareword = auto()
    LexExpression = auto()
    LexDoubleQuote = auto()
    LexSingleQuote = auto()
    LexSquareBracket = auto()

class SugarCubeLexer:
    source:str = ""
    initial_state = None
    _state = None
    def __init__(self,source:str,initial_state:Callable[[Self],None]):
        self.source = source
        self.initial_state = initial_state

