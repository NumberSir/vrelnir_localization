from dataclasses import dataclass
from typing import Union, Optional,List
from enum import  Enum
__all__ = [
    "EOF",
    "Item",
    "ItemType",
    "TweeLexer"
]
EOF = -1
class ItemType(Enum):
    ItemError = 0
    ItemEOF = 1
    ItemHeader = 2
    ItemName = 3
    ItemTags = 4
    ItemMetadata = 5
    ItemContent = 6
@dataclass
class Item:
    _type:int = 0
    line:int =0
    pos:int = 0
    val:str = ""
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
            return f"[EOF: {self.line}/{self.pos}]"
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
            return  f"[{name}:{self.line}/{self.pos}]{self.val:.80}..."
        return  f"[{name}:{self.line}/{self.pos}]{self.val}"
@dataclass
class ItemValue:
    item:Union[Item,None] = None
    @property
    def result(self):
        return self.item is None
    def has_value(self):
        return self.item is None

@dataclass
class TweeLexer:
    input:str = ""
    line:int = 0
    start:int = 0
    pos:int = 0
    items:List[Item] = list

    @property
    def now_chara(self):
        return self.input[self.pos]
    @property
    def count_line_now(self):
        return self.input.count('\n',self.start,self.pos)
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

    def accept(self,valid:str):
        if self.next  in valid:
            return True
        self.backup()
        return False

    def accept_run(self, valid: str):
        r = self.next
        while r in valid:
            r = self.next
        if r != EOF:
            self.backup()
    def error_format(self,format_str:str,**args:List[any]):
        self.items.append(Item(ItemType.ItemError.value, self.line, self.pos, format_str.format(**args)))
    def run(self):
        pass
    @staticmethod
    def new_twee_lexer(input_str:str):
        twee = TweeLexer(input_str, line=1, items=[])
        twee.run()
        return twee
    def get_items(self):
        return  self.items
    def next_items(self):
        if len(self.items) > 0:
            item = self.items.pop(0)
            return  ItemValue(item)
        return  ItemValue()
    def drain(self):
        pass
def accept_quoted(twee_lexer:TweeLexer,quote:str):
    while True:
        r = twee_lexer.next
        if r =="\\":
            r = twee_lexer.next
            if r not in ['\n', EOF]:
                break
        elif r in ['\n', EOF]:
            return "unterminated quoted string"
        elif r == quote:
            continue
    return None

