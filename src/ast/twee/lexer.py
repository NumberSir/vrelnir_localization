import io
from dataclasses import dataclass
from typing import Union, List, Callable,Optional
from typing_extensions import Self
from enum import Enum, auto

EOF = b''
class ItemType(Enum):
    ItemError = 0
    ItemEOF = auto()
    ItemHeader = auto()
    ItemName = auto()
    ItemTags = auto()
    ItemMetadata = auto()
    ItemContent = auto()
@dataclass
class Item:
    _type:int = 0
    line:int =0
    pos:int = 0
    val:bytes = b""
    @property
    def type(self):
        return ItemType(self._type)
    @type.setter
    def type(self,item_type:ItemType):
        self._type = item_type.value
    def to_string(self):
        name = ""
        item_type = self.type
        if item_type == ItemType.ItemEOF:
            return f"[EOF: {self.line}行/{self.pos}位]"
        elif item_type == ItemType.ItemError:
            name = "Error"
        elif item_type == ItemType.ItemHeader:
            name = "Header"
        elif item_type == ItemType.ItemName:
            name = "Name"
        elif item_type == ItemType.ItemTags:
            name = "Tags"

        elif item_type == ItemType.ItemMetadata:
            name = "Metadata"
        elif item_type == ItemType.ItemContent:
            name = "Content"

        if item_type != ItemType.ItemError and len(self.val) > 80:
            return  f"[{name}:{self.line}行/{self.pos}位] {self.val:.80}..."
        return  f"[{name}:{self.line}行/{self.pos}位] {self.val}"
@dataclass
class ItemValue:
    item:Union[Item,None] = None
    @property
    def result(self):
        return self.has_value()
    def has_value(self):
        return self.item is not None

@dataclass
class TweeLexer:
    input:bytes = b""
    line:int = 0
    start:int = 0
    pos:int = 0
    items:List[Item] = list

    @property
    def now_chara(self):
        return self.input[self.pos].to_bytes(1,byteorder="big")

    @property
    def has_header_delim(self):
        return  self.input.startswith(HEADER_DELIM,self.pos)
    @property
    def newline_header_delim_index(self):
        return  self.input.index(NEWLINE_HEADER_DELIM,self.pos)
    @property
    def now_text(self):
        return self.input[self.pos:]
    @property
    def count_line_now(self):
        return self.input.count(b'\n',self.start,self.pos)
    @property
    def item_value(self):
        return self.input[self.start:self.pos]
    @property
    def next(self):
        if self.pos >= len(self.input):
            return EOF
        r = self.now_chara
        self.pos += 1
        if r == '\n':
            self.line += 1
        return  r

    @property
    def peek(self):
        return EOF if self.pos >= len(self.input) else self.now_chara


    def backup(self):  # sourcery skip: raise-specific-error
        if self.pos <= self.start:
            raise Exception("backup would leave pos < start")
        self.pos -=1
        if self.now_chara == '\n':
            self.line -= 1
    def append_item(self,item_type:ItemType):
        self.items.append(Item(item_type.value, self.line, self.pos, self.item_value))
    def emit(self,item_type:ItemType):
        self.append_item(item_type)
        if item_type == ItemType.ItemContent:
            self.line+= self.count_line_now
        self.start = self.pos

    def ignore(self):
        self.line +=self.count_line_now
        self.start = self.pos

    def accept(self,valid:bytes):
        if self.next  in valid:
            return True
        self.backup()
        return False

    def accept_run(self, valid: bytes):
        r = self.next
        while r in valid:
            r = self.next
        if r != EOF:
            self.backup()
    def error_format(self,format_str:str,*args):
        self.items.append(Item(ItemType.ItemError.value, self.line, self.pos, format_str.format(*args).encode()))
    def run(self):
        state = TweeLexerState.LexerProlog
        while state != TweeLexerState.LexerNone:
            callback = state.get_state_func()
            state = callback(self)
    @staticmethod
    def create_twee_lexer(input_str:bytes):
        twee_instance = TweeLexer(input_str, line=1, items=[])
        twee_instance.run()
        return twee_instance
    def get_items(self):
        return  self.items
    def next_items(self):
        if len(self.items) > 0:
            item = self.items.pop(0)
            return  ItemValue(item)
        return  ItemValue()
    def drain(self):
        pass




def accept_quoted(twee_lexer: TweeLexer, quote: str):
    while True:
        r = twee_lexer.next
        if r == "\\":
            r = twee_lexer.next
            if r not in ['\n', EOF]:
                break
            continue
        elif r in ['\n', EOF]:
            return repr("unterminated quoted string")
        elif r == quote:
            break
    return None

HEADER_DELIM = b"::"
NEWLINE_HEADER_DELIM = b"\n::"
class TweeLexerState(Enum):
    LexerNone = 0
    LexerProlog =auto()
    LexerContent =auto()
    LexerHeaderDelim =auto()
    LexerName =auto()
    LexerNextOptionalBlock =auto()
    LexerTags =auto()
    LexerMetadata =auto()

    STATE_FUNC = Optional[Callable[[TweeLexer], Optional[Self]]]
    @staticmethod
    def lex_prolog(twee_lexer: TweeLexer):
        print("进入Prolog解析器")
        if twee_lexer.has_header_delim:
            return TweeLexerState.LexerHeaderDelim
        text_index =twee_lexer.newline_header_delim_index
        if  text_index > -1:
            twee_lexer.pos += text_index + 1
            twee_lexer.ignore()
            return TweeLexerState.LexerHeaderDelim
        twee_lexer.emit(ItemType.ItemEOF)
        return TweeLexerState.LexerNone

    @staticmethod
    def lex_context(twee_lexer: TweeLexer):
        print("进入Context解析器")
        if twee_lexer.has_header_delim:
            return TweeLexerState.LexerHeaderDelim
        text_index = twee_lexer.newline_header_delim_index
        if text_index > -1:
            twee_lexer.pos += text_index + 1
            twee_lexer.emit(ItemType.ItemContent)
            return TweeLexerState.LexerHeaderDelim
        twee_lexer.pos = len(twee_lexer.input)
        if twee_lexer.pos > twee_lexer.start:
            twee_lexer.emit(ItemType.ItemContent)
        twee_lexer.emit(ItemType.ItemEOF)
        return TweeLexerState.LexerNone

    @staticmethod
    def lex_header_delim(twee_lexer: TweeLexer):
        print("进入HeaderDelim解析器")
        twee_lexer.pos += len(HEADER_DELIM)
        twee_lexer.emit(ItemType.ItemHeader)
        return TweeLexerState.LexerName

    @staticmethod
    def lex_name(twee_lexer: TweeLexer):
        print("进入Name解析器")
        while True:
            r = twee_lexer.next
            if r == "\\":
                r = twee_lexer.next
                if r not in  [b"\n",EOF]:
                    break
                continue
            elif r in  [b'[', b']', b'{', b'}',b"\n",EOF]:
                if r != EOF:
                    twee_lexer.backup()
                break
        twee_lexer.emit(ItemType.ItemName)
        if r == b'[':
            return  TweeLexerState.LexerTags
        if r == b']':
            return  twee_lexer.error_format("unexpected right square bracket %#U",r)
        if r == b'{':
            return TweeLexerState.LexerMetadata
        if r == b'}':
            return  twee_lexer.error_format("unexpected right curly bracket %#U",r)
        if r == b'\n':
            twee_lexer.pos += 1
            twee_lexer.ignore()
            return TweeLexerState.LexerContent
        twee_lexer.emit(ItemType.ItemEOF)
        return TweeLexerState.LexerNone


    @staticmethod
    def lex_next_optional_block(twee_lexer: TweeLexer):
        print("进入NextOptionalBlock解析器")
        twee_lexer.accept_run(b" \t")
        twee_lexer.ignore()
        r = twee_lexer.peek
        if r == b'[':
            return TweeLexerState.LexerTags
        if r == b']':
            return twee_lexer.error_format("unexpected right square bracket %#U", r)
        if r == b'{':
            return TweeLexerState.LexerMetadata
        if r == b'}':
            return twee_lexer.error_format("unexpected right curly bracket %#U", r)
        if r == '\n':
            twee_lexer.pos += 1
            twee_lexer.ignore()
            return TweeLexerState.LexerContent
        if r == EOF:
            twee_lexer.emit(ItemType.ItemEOF)
            return TweeLexerState.LexerNone
        return twee_lexer.error_format("illegal character %#U amid the optional block", r)
    @staticmethod
    def lex_tags(twee_lexer: TweeLexer):
        print("进入Tags解析器")
        twee_lexer.pos += 1

        if twee_lexer.pos > twee_lexer.start:
            twee_lexer.emit(ItemType.ItemTags)
        return TweeLexerState.LexerNextOptionalBlock
    @staticmethod
    def lex_metadata(twee_lexer: TweeLexer):
        print("进入Metadata解析器")
        twee_lexer.pos += 1

        if twee_lexer.pos > twee_lexer.start:
            twee_lexer.emit(ItemType.ItemTags)
        return TweeLexerState.LexerNextOptionalBlock
    def get_state_func(self: Self) ->STATE_FUNC:
        print(f"进入状态机:{self}")
        if self == TweeLexerState.LexerNone:
            return None
        if self == TweeLexerState.LexerProlog:
            return TweeLexerState.lex_prolog
        elif self == TweeLexerState.LexerContent:
            return TweeLexerState.lex_context
        elif self == TweeLexerState.LexerHeaderDelim:
            return TweeLexerState.lex_header_delim
        elif self == TweeLexerState.LexerName:
            return TweeLexerState.lex_name
        elif self == TweeLexerState.LexerNextOptionalBlock:
            return TweeLexerState.lex_next_optional_block
        elif self == TweeLexerState.LexerTags:
            return TweeLexerState.lex_tags
        elif self == TweeLexerState.LexerMetadata:
            return TweeLexerState.lex_metadata
        return None

# twee=TweeLexer.create_twee_lexer(b"::Test [demo]\n<<he>>")
# print(twee)
# for item in twee.items:
#     print(item.to_string())
__all__ = [
    "HEADER_DELIM",
    "NEWLINE_HEADER_DELIM",
    "EOF",

    "Item",
    "ItemType",
    "TweeLexer",
    "TweeLexerState",
    "accept_quoted",

]