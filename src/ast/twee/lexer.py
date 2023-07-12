import io
import time
from dataclasses import dataclass
from typing import Union, List, Callable,Optional
from typing_extensions import Self
from enum import Enum, auto

EOF = None
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
    type:ItemType = ItemType.ItemError
    line:int =0
    pos:int = 0
    end:int = 0
    val:bytes = b""

    # @property
    # def type(self):
    #     return ItemType(self._type)
    #
    # @type.setter
    # def type(self, item_type: ItemType):
    #     self._type = item_type.value
    @property
    def value(self):
        return self.val.decode(encoding="utf8")

    def to_string(self):
        name = ""
        item_type = self.type
        match item_type:
            case ItemType.ItemEOF:
                return f"[EOF: {self.line}行/{self.pos}位]"
            case ItemType.ItemError:
                name = "Error"
            case ItemType.ItemHeader:
                name = "Header"
            case ItemType.ItemName:
                name = "Name"
            case ItemType.ItemTags:
                name = "Tags"
            case ItemType.ItemMetadata:
                name = "Metadata"
            case ItemType.ItemContent:
                name = "Content"
        if item_type != ItemType.ItemError and len(self.value) > 80:
            return  f"[{name}:{self.line}行/{self.pos}位] {self.value:.80}..."
        return  f"[{name}:{self.line}行/{self.pos}位] {self.value}"

@dataclass
class ItemValue:
    item: Item | None = None

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
    _end:int = 0
    items:list[Item] = list

    def reset(self):
        self.line = 0
        self.start = 0
        self.pos = 0
        self._end = 0
        self.items = []
        self.input = b''
    def parse(self,input_str: Union[bytes,str]):
        self.reset()
        if type(input_str) == str:
            input_str = input_str.encode()
        self.input = input_str
        self.line =1
        self.run()
        return self


    @staticmethod
    def create_twee_lexer(input_str: Union[bytes,str]):
        if type(input_str) == str:
            input_str = input_str.encode()
        twee_instance = TweeLexer(input_str, line=1, items=[])
        twee_instance.run()
        return twee_instance

    @property
    def end(self):
        if self._end == 0 :
            self._end = len(self.input)
        return self._end

    @property
    def now_chara(self):
        return EOF if self.pos > self.end else chr(self.input[self.pos]).encode()

    @property
    def has_header_delim(self):
        return  self.input.startswith(HEADER_DELIM,self.pos)
    @property
    def newline_header_delim_index(self):

        return -1 if self.pos > self.end else self.input.find(NEWLINE_HEADER_DELIM,self.pos)
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
        return r

    @property
    def peek(self):
        return EOF if self.pos >= len(self.input) else self.now_chara


    def backup(self):  # sourcery skip: raise-specific-error
        if self.pos <= self.start:
            raise Exception("backup would leave pos < start")
        self.pos -= 1
        if self.now_chara == '\n':
            self.line -= 1

    def append_item(self, item_type: ItemType):
        end = len(self.item_value) + self.pos
        self.items.append(Item(item_type, self.line, self.pos,end, self.item_value))

    def emit(self, item_type: ItemType):
        self.append_item(item_type)
        if item_type == ItemType.ItemContent:
            self.line += self.count_line_now
        self.start = self.pos

    def ignore(self):
        self.line += self.count_line_now
        self.start = self.pos

    def accept(self,valid:list[bytes]):
        if self.next  in valid:
            return True
        self.backup()
        return False

    def accept_run(self, valid: list[bytes]):
        r = self.next
        while r in valid:
            r = self.next
        if r != EOF:
            self.backup()
            
    def error_format(self,format_str:str,*args:any):
        error_str =format_str.format(*args).encode()
        end = self.pos
        for text in args:
            end += len(text)
        self.items.append(Item(ItemType.ItemError, self.line, self.pos,end, error_str))
    
    def run(self):
        state = TweeLexerState.LexerProlog
        while state not in  [TweeLexerState.LexerNone,EOF]:
            callback = state.get_state_func()
            state = callback(self)

    


    def get_items(self):
        return self.items

    def next_items(self):
        if len(self.items) > 0:
            item_value = self.items.pop(0)
            return ItemValue(item_value)
        return ItemValue()

    def drain(self):
        pass


def accept_quoted(twee_lexer: TweeLexer, quote: list[bytes]):
    while True:
        r = twee_lexer.next
        if r in quote:
            break
        match r:
            case b"\\":
                r = twee_lexer.next
                if r not in [b"", None]:
                    break
                continue
            case [b'\n', None]:
                return repr("unterminated quoted string")

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
            twee_lexer.pos = text_index + 1
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
        match r:
            case b'[':
                return  TweeLexerState.LexerTags
            case b']':
                return  twee_lexer.error_format("unexpected right square bracket %#U",r)
            case b'{':
                return TweeLexerState.LexerMetadata
            case b'}':
                return  twee_lexer.error_format("unexpected right curly bracket %#U",r)
            case b'\n':
                twee_lexer.pos += 1
                twee_lexer.ignore()
                return TweeLexerState.LexerContent
        twee_lexer.emit(ItemType.ItemEOF)
        return TweeLexerState.LexerNone


    @staticmethod
    def lex_next_optional_block(twee_lexer: TweeLexer):
        print("进入NextOptionalBlock解析器")
        twee_lexer.accept_run([b" ",b"\t"])
        twee_lexer.ignore()
        r = twee_lexer.peek
        match r:
            case b'[':
                return TweeLexerState.LexerTags
            case b']':
                return twee_lexer.error_format("unexpected right square bracket %#U", r)
            case b'{':
                return TweeLexerState.LexerMetadata
            case b'}':
                return twee_lexer.error_format("unexpected right curly bracket %#U", r)
            case u'\n':
                twee_lexer.pos += 1
                twee_lexer.ignore()
                return TweeLexerState.LexerContent
            case None:
                twee_lexer.emit(ItemType.ItemEOF)
                return TweeLexerState.LexerNone
        return twee_lexer.error_format("illegal character %#U amid the optional block", r)

    @staticmethod
    def lex_tags(twee_lexer: TweeLexer):
        print("进入Tags解析器")
        twee_lexer.pos += 1
        while True:
            r = twee_lexer.next
            match r:
                case b"\\":
                    r = twee_lexer.next
                    if r not in [u'\n',EOF]:
                        break
                    continue
                case [b'\n',None]:
                    if r == '\n' :
                        twee_lexer.backup()
                    return twee_lexer.error_format("unterminated tag block")
                case b'[':
                    return twee_lexer.error_format("unexpected left square bracket %#U", r)
                case b']':
                    break
                case b'{':
                    return twee_lexer.error_format("unexpected left curly brace %#U", r)
                case b'}':
                    return twee_lexer.error_format("unexpected right curly brace %#U", r)
        if twee_lexer.pos > twee_lexer.start:
            twee_lexer.emit(ItemType.ItemTags)
        return TweeLexerState.LexerNextOptionalBlock

    @staticmethod
    def lex_metadata(twee_lexer: TweeLexer):
        print("进入Metadata解析器")
        twee_lexer.pos += 1
        depth = 1
        while True:
            r = twee_lexer.next
            match r:
                case b'"':
                    err = accept_quoted(twee_lexer,[b'"'])
                    if err is not None:
                        return twee_lexer.error_format(err)
                case b'\n':
                    twee_lexer.backup()
                    continue
                case None:
                    return twee_lexer.error_format("unterminated metadata block")
                case b'{':
                    depth+=1
                case b'}':
                    depth-=1
                    if depth == 0:
                        break
        if twee_lexer.pos > twee_lexer.start:
            twee_lexer.emit(ItemType.ItemTags)
        return TweeLexerState.LexerNextOptionalBlock

    def get_state_func(self: Self) ->STATE_FUNC:
        print(f"进入状态机:{self}")
        match self:
            case TweeLexerState.LexerNone:
                return None
            case TweeLexerState.LexerProlog:
                return TweeLexerState.lex_prolog
            case TweeLexerState.LexerContent:
                return TweeLexerState.lex_context
            case TweeLexerState.LexerHeaderDelim:
                return TweeLexerState.lex_header_delim
            case TweeLexerState.LexerName:
                return TweeLexerState.lex_name
            case TweeLexerState.LexerNextOptionalBlock:
                return TweeLexerState.lex_next_optional_block
            case TweeLexerState.LexerTags:
                return TweeLexerState.lex_tags
            case TweeLexerState.LexerMetadata:
                return TweeLexerState.lex_metadata
        return None

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
