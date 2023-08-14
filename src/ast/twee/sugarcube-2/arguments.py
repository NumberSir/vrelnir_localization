from dataclasses import dataclass, field
from enum import Enum, auto

class LexerState(Enum):
    EOF = None

EOFT = -1
EOF: EOFT = -1


@dataclass
class LexerItem:
    type_: any
    text: str
    start: int
    position: int
    message: str = None

@dataclass
class Lexer:
    source: str = ""
    state: LexerState | None = None
    start: int = 0
    pos: int = 0
    depth: int = 0
    items: list[LexerItem] = field(default_factory=list)
    data: dict[str, any] = field(default_factory=dict)

    def run(self) -> list[LexerItem]:
        while self.state is not None:
            ...
        return self.items

    def next(self) -> EOFT | str:
        ch = self.peek()
        self.pos += 1
        return ch

    def peek(self) -> EOFT | str:
        if self.pos >= len(self.source):
            return EOF
        return self.source[self.pos]

    def backup(self, num: int = None):
        self.pos -= num or 1

    def forward(self, num: int = None):
        self.pos += num or 1

    def ignore(self):
        self.start = self.pos

    def accept(self, valid: str) -> bool:
        ch = self.next()
        if ch == EOF:
            return False
        elif ch in valid:
            return True
        self.backup()
        return False

    def accept_run(self, valid: str):
        while True:
            ch = self.next()
            if ch == EOF:
                return
            elif ch not in valid:
                break
        self.backup()

    def emit(self, type_: any):
        self.items.append(
            LexerItem(
                type_=type_,
                text=self.source[self.start: self.pos],
                start=self.start,
                position=self.pos
            )
        )
        self.start = self.pos

    def error(self, type_: any, message: str) -> None:
        self.items.append(
            LexerItem(
                type_=type_,
                message=message,
                text=self.source[self.start: self.pos],
                start=self.start,
                position=self.pos
            )
        )
        return


class ParsedArguments:
    errors: list["ArgumentParseError"]
    warnings: list["ArgumentParseWarning"]
    arguments: list["Arg"]


class ArgumentParseErrorKind(Enum):
    FAILURE = 0
    SQUARE_BRACKET_FAILURE = auto()
    SQUARE_BRACKET_EXPECTED_CHARACTER = auto()


class ArgumentParseError:
    kind: "ArgumentParseErrorKind"
    range_: range
    message: str = None


class ArgumentParseWarningKind(Enum):
    INVALID_PASSAGE_NAME = 0


class ArgumentParseWarning:
    kind: "ArgumentParseWarningKind"
    range_: range
    message: str = None


class ArgType(Enum):
    LINK = 0
    IMAGE = auto()
    VARIABLE = auto()
    SETTINGS_SETUP_ACCESS = auto()
    NULL = auto()
    UNDEFINED = auto()
    TRUE = auto()
    FALSE = auto()
    NAN = auto()
    NUMBER = auto()
    BAREWORD = auto()
    EMPTY_EXPRESSION = auto()
    EXPRESSION = auto()
    STRING = auto()

class LinkArgument:
    type_: ArgType.LINK
    range_: range
    passage:
