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
    type:ItemType = 0
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
            
    def error_format(self,format_str:str,*args:tuple[any]):
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
text = """
:: Test
<<location "flats">><<effects>>
<<endcombat>>
<<link [[Test]]>><</link>>
<br><br>

<<pass 60>>

:: Robin
<<set $NPCName[$NPCNameList.indexOf("Robin")].love to 50>>
<<if $NPCName[$NPCNameList.indexOf("Robin")].love gte 50>>
<</if>>
<<nnpc_he Robin>>

<<link [["Ask " + $NPCList[0].pronouns.him + " how " + $NPCList[0].pronouns.he + " gets in and out"|Prison Wren Ask 2]]>><</link>>

<<run Furniture.set('owlplushie', 'owlplushie', {
	name	: 'owl plushie',
	nameCap	: 'Owl plushie'
})>>

:: Sex
<<if $sexstart is 1>>
	<<set $sexstart to 0>>
	<<consensual>>
	<<set $consensual to 1>>
	<<neutral 1>>
	<<maninit>>
	<<set $enemytrust += 100>><<promiscuity5>>
<</if>>

<<effects>>
<<effectsman>>
<<man>>
<<stateman>>
<br><br>
<<actionsman>>
<<if _combatend>>
	<span id="next"><<link [[Next|Sex Finish]]>><</link>></span><<nexttext>>
<<else>>
	<span id="next"><<link [[Next|Sex]]>><</link>></span><<nexttext>>
<</if>>

:: Sex Finish

<<set $outside to 0>><<effects>>
<<if $enemyarousal gte $enemyarousalmax>>
	<<ejaculation>>
	Text about the aftermath of them cumming.
	<br><br>
	<<tearful>> you recover.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<link [[Next|Sex]]>><</link>>/*Point links wherever you want the player to end up*/
<<elseif $enemyhealth lte 0>>
	Text about escaping.
	<br><br>
	<<tearful>> you recover.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<link [[Next|Sex]]>><</link>>
<<else>>
	Text about the encounter stopping because you ended it.
	<br><br>
	<<tearful>> you recover.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<link [[Next|Sex]]>><</link>>
<</if>>

:: Rape

<<if $molestationstart is 1>>
	<<set $molestationstart to 0>>
	<<controlloss>>
	<<violence 1>>
	<<neutral 1>>
	<<molested>>
	<<maninit>>
	<<enable_rescue>>/*Remove line if rescue is impossible*/
<</if>>

<<effects>>
<<effectsman>>
<<alarmstate>>
<<man>>
<<stateman>>
<br><br>
<<actionsman>>

<<if _combatend>>
	<span id="next"><<link [[Next|Rape Finish]]>><</link>></span><<nexttext>>
<<else>>
	<span id="next"><<link [[Next|Rape]]>><</link>></span><<nexttext>>
<</if>>

:: Rape Finish
<<effects>>
<<if $enemyarousal gte $enemyarousalmax>>
	<<ejaculation>>
	Text about the aftermath of them cumming.
	<br><br>
	<<tearful>> you recover.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<link [[Next|Rape]]>><<set $molestationstart to 1>><</link>>/*Link points wherever you want the player to end up*/

<<elseif $enemyhealth lte 0>>
	Text about escaping.
	<br><br>
	<<tearful>> you recover.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<link [[Next|Rape]]>><<set $molestationstart to 1>><</link>>

<<else>>
	<<set $rescued += 1>>/*Unnecessary if rescue is impossible*/
	Text about being rescued.
	<br><br>
	<<tearful>> you recover.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<link [[Next|Rape]]>><<set $molestationstart to 1>><</link>>

<</if>>

:: Fight
<<if $fightstart is 1>>
	<<set $fightstart to 0>>
	<<neutral 1>>
	<<maninit>>
	<<set $enemytrust -= 100>>
	<<set $enemyanger += 200>>
	<<npcidlegenitals>>
<</if>>

<<effects>>
<<effectsman>>
<<man>>
<<stateman>>
<br><br>
<<actionsman>>

<<if _combatend or ($pain gte 100 and $willpowerpain is 0)>>
	<span id="next"><<link [[Next|Fight Finish]]>><</link>></span><<nexttext>>
<<else>>
	<span id="next"><<link [[Next|Fight]]>><</link>></span><<nexttext>>
<</if>>

:: Fight Finish
<<effects>>
<<if $enemyarousal gte $enemyarousalmax>>
	<<ejaculation>>
	Text about the aftermath of them cumming.
	<br><br>
	<<tearful>> you recover.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<link [[Next|Fight]]>><</link>>/*Point links wherever you want the player to end up*/

<<elseif $enemyhealth lte 0>>
	Text about escaping.
	<br><br>
	<<tearful>> you recover.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<link [[Next|Fight]]>><</link>>

<<else>>
	Text about being too hurt to fight.
	<br><br>
	<<tearful>> you recover.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<link [[Next|Fight]]>><</link>>

<</if>>

:: Skulduggery
<<effects>>

<<set $skulduggerydifficulty to 200>>
<<link [[Next|Skulduggery 2]]>><</link>><<skulduggerydifficulty>>
<br>

:: Skulduggery 2
<<effects>>

Possible text describing your attempt.
<br><br>

<<skulduggerycheck>>
<<if $skulduggerysuccess is 1>>

	Text describing your success.
	<br><br>

	<<if $skulduggery lte ($skulduggerydifficulty + 100)>>
		<<skulduggeryskilluse>>
	<<else>>
		<span class="blue">That was too easy. You didn't learn anything.</span>
		<br><br>
	<</if>>

	<<link [[Next|Skulduggery]]>><</link>>
	<br>

<<else>>

	Text describing your failure.
	<br><br>

	<<if $skulduggery lte ($skulduggerydifficulty + 100)>>
		<<skulduggeryskilluse>>
	<<else>>
		<span class="blue">That was too easy. You didn't learn anything.</span>
		<br><br>
	<</if>>

	<<link [[Next|Skulduggery]]>><</link>>
	<br>

<</if>>

:: Beast Sex
<<if $sexstart is 1>>
	<<set $sexstart to 0>>
	<<consensual>>
	<<set $consensual to 1>>
	<<neutral 1>>
	<<beastNEWinit 1 dog>>/* - Delete if beasts are already generated*/
	<<beastCombatInit>>
	<<beastTrainGenerate>>/* - Delete if there aren't multiple beasts*/
<</if>>

<<effects>>
<<effectsman>>
<br>
<<beast $enemyno>>
<br><br>

<<stateman>>
<br><br>
<<actionsman>>

<<if _combatend>>
	<span id="next"><<link [[Next|Beast Sex Finish]]>><</link>></span><<nexttext>>
<<else>>
	<span id="next"><<link [[Next|Beast Sex]]>><</link>></span><<nexttext>>
<</if>>

:: Beast Sex Finish
<<effects>>

<<if $enemyarousal gte $enemyarousalmax>>

	<<beastejaculation>>

	Insert text about the aftermath of the beast cumming.
	<br><br>

	<<tearful>> you gather yourself.
	<br><br>

	<<clotheson>>
	<<endcombat>>

	<<link [[Next|Beast Rape]]>><<set $eventskip to 1>><</link>>

<<elseif $enemyhealth lte 0>>

	Insert text about the beast running.
	<br><br>

	<<tearful>> you gather yourself.
	<br><br>

	<<clotheson>>
	<<endcombat>>

	<<link [[Next|Beast Rape]]>><<set $eventskip to 1>><</link>>

<<else>>

	Insert text about the beast stopping because you asked it to.
	<br><br>

	<<tearful>> you gather yourself.
	<br><br>

	<<clotheson>>
	<<endcombat>>

	<<link [[Next|Beast Rape]]>><<set $eventskip to 1>><</link>>

<</if>>

:: Beast Rape
<<if $molestationstart is 1>>
	<<set $molestationstart to 0>>
	<<controlloss>>
	<<violence 1>>
	<<neutral 1>>
	<<molested>>
	<<beastNEWinit 2 dog>>/* - Delete if beasts are already generated*/
	<<beastCombatInit>>
	<<beastTrainGenerate>>/* - Delete if there aren't multiple beasts*/
<</if>>

<<effects>>
<<effectsman>>
<br><br>
<<beast $enemyno>>
<br><br>

<<stateman>>
<br><br>
<<actionsman>>

<<if _combatend>>
	<span id="next"><<link [[Next|Beast Rape Finish]]>><</link>></span><<nexttext>>
<<else>>
	<span id="next"><<link [[Next|Beast Rape]]>><</link>></span><<nexttext>>
<</if>>

:: Beast Rape Finish
<<effects>>

<<if $enemyarousal gte $enemyarousalmax>>

	<<beastejaculation>>

	Insert text about the aftermath of the beast cumming.
	<br><br>

	<<tearful>> you gather yourself.
	<br><br>

	<<clotheson>>
	<<endcombat>>

	<<link [[Next|Beast Rape]]>><<set $eventskip to 1>><</link>>

<<elseif $enemyhealth lte 0>>

	Insert text about the beast running.
	<br><br>

	<<tearful>> you gather yourself.
	<br><br>

	<<clotheson>>
	<<endcombat>>

	<<link [[Next|Beast Rape]]>><<set $eventskip to 1>><</link>>

<<else>><<set $rescued += 1>>

	Insert text about being rescued.
	<br><br>

	<<tearful>> you gather yourself.
	<br><br>

	<<clotheson>>
	<<endcombat>>

	<<link [[Next|Beast Rape]]>><<set $eventskip to 1>><</link>>

<</if>>

:: Beast Gang
<<if $molestationstart is 1>>
	<<set $molestationstart to 0>>
	<<controlloss>>
	<<violence 1>>
	<<neutral 1>>
	<<molested>>
	<<beastNEWinit 1 wolf>>
	<<beastCombatInit>>
	<<beastTrainGenerate>>
	<<enable_rescue>>/*optional*/
<</if>>
<<effects>>
<<effectsman>>
<<alarmstate>>
<<beast $enemyno>>
<br><br>
<<stateman>>
<br><br>
<<actionsman>>

<<if _combatend>>
	<span id="next"><<link [[Next|Beast Gang End]]>><</link>></span><<nexttext>>
<<else>>
	<span id="next"><<link [[Next|Beast Gang]]>><</link>></span><<nexttext>>
<</if>>

:: Beast Gang End
<<effects>>
<<if $enemyhealth lte 0>>
	<<beastwound>>
	<<if $combatTrain.length gt 0>>
		The <<beasttype>> recoils in pain and fear, but another is eager for a go.

		<<combatTrainAdvance>>
		<br><br>
		<<link [[Next|Beast Gang]]>><</link>>
	<<else>>
		The <<beasttype>> recoils in pain and fear.
		<<combatTrainAdvance>>
		<br><br>
		<<link [[Next|Beast Gang End]]>><<set $finish to 1>><</link>>
	<</if>>
<<elseif $enemyarousal gte $enemyarousalmax>>
	<<beastejaculation>>
	<<if $combatTrain.length gt 0>>
		Satisfied, the <<beasttype>> moves and another takes its turn.

		<<combatTrainAdvance>>
		<br><br>
		<<link [[Next|Beast Gang]]>><</link>>
	<<else>>
		Satisfied, the <<beasttype>> moves away from you.
		<<combatTrainAdvance>>
		<br><br>
		<<link [[Next|Beast Gang End]]>><<set $finish to 1>><</link>>
	<</if>>
<<elseif $finish is 1>>
	<<if $enemywounded is 1 and $enemyejaculated is 0>>
		The <<beasttype>> whimpers and flees.
	<<elseif $enemywounded is 0 and $enemyejaculated is 1>>
		Satisfied, the <<beasttype>> leaves.
	<<elseif $enemywounded gte 2 and $enemyejaculated is 0>>
		Feeling that you're more trouble than you're worth, the beasts flee.
	<<elseif $enemywounded is 0 and $enemyejaculated gte 2>>
		The beasts leave you spent and shivering.
	<<elseif $enemywounded gte 1 and $enemyejaculated gte 1>>
		The beasts leave you spent and shivering.
	<</if>>
	<br><br>
	<<tearful>> you gather yourself.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<destinationeventend>>
<<elseif $alarm is 1 and $rescue is 1>>
	<<set $rescued += 1>>

	You are rescued.
	<br><br>
	<<tearful>> you gather yourself.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<destinationeventend>>
<</if>>

:: Seduce
<<effects>>

<<set $seductiondifficulty to 6000>>
<<seductioncheck>>
<br><br>
<<if $seductionskill lt 1000>>
	<span class="gold">You feel more confident in your powers of seduction.</span>
	<br><br>
<</if>>
<<seductionskilluse>>

Text detailing your seduction attempt.
<<promiscuity3>>

<<if $seductionrating gte $seductionrequired>>

	Text detailing your seduction success.
	<br><br>

<<else>>

	Text detailing your seduction failure.
	<br><br>

<</if>>

:: Lock

<<set $lock to 300>>

The door is locked tight.
<br><br>

	<<if currentSkillValue('skulduggery') gte $lock>>
	<span class="green">The lock looks easy to pick.</span>
	<br><br>

	<<link [[Break in (0:05)|Elk Compound Interior]]>><<pass 5>><<crimeup 1>><</link>><<crime>>
	<br>
	<<else>>
	<span class="red">The lock looks beyond your ability to pick.</span><<skulduggeryrequired>>
	<br><br>
	<</if>>

You successfully pick the lock and enter the building.
<<set $compoundcentre to 1>><<set $compoundalarm += 1>>

<<if $skulduggery lt 400>>
<<skulduggeryskilluse>>
<<else>>
<span class="blue">There's nothing more you can learn from locks this simple.</span>
<</if>>

:: Template for a widget that outputs text based on character's state

<<widget "widgetname">>
	<<exposure>>/*Makes sure your clothing state is up to date*/
	<<if $optionalvariable is "something">>
		<<if $trauma gte (($traumamax / 5) * 4)>>
			<<if $stress gte (($stressmax / 5) * 4)>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<<elseif $stress gte (($stressmax / 5) * 1)>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<<else>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<</if>>
		<<elseif $trauma gte (($traumamax / 5) * 1)>>
			<<if $stress gte (($stressmax / 5) * 4)>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<<elseif $stress gte (($stressmax / 5) * 1)>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<<else>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<</if>>
		<<else>>
			<<if $stress gte (($stressmax / 5) * 4)>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<<elseif $stress gte (($stressmax / 5) * 1)>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<<else>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<</if>>
		<</if>>
	<<else>>
		<<if $trauma gte (($traumamax / 5) * 4)>>
			<<if $stress gte (($stressmax / 5) * 4)>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<<elseif $stress gte (($stressmax / 5) * 1)>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<<else>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<</if>>
		<<elseif $trauma gte (($traumamax / 5) * 1)>>
			<<if $stress gte (($stressmax / 5) * 4)>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<<elseif $stress gte (($stressmax / 5) * 1)>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<<else>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<</if>>
		<<else>>
			<<if $stress gte (($stressmax / 5) * 4)>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<<elseif $stress gte (($stressmax / 5) * 1)>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<<else>>
				<<if $arousal gte (($arousalmax / 5) * 4)>>

				<<elseif $arousal gte (($arousalmax / 5) * 1)>>

				<<else>>

				<</if>>
			<</if>>
		<</if>>
	<</if>>
<</widget>>

<<set $danger to random(1, 10000)>><<set $dangerevent to 0>>
	<<if $danger gte (9900 - $allure)>>

	<<else>>

	<</if>>

<<if $test is "" or $test is undefined>><<set $test to "default">><</if>>
<<textbox "$test" $test>>

<<if $physique gte $rng * 100 + 6000>>

<</if>>

		<<if $npcspeechcycle is 0>>
		<<He>> speaks. ""
		<<elseif $npcspeechcycle is 1>>
		<<He>> speaks. ""
		<<elseif $npcspeechcycle is 2>>
		<<He>> speaks. ""
		<<elseif $npcspeechcycle is 3>>
		<<He>> speaks. ""
		<<elseif $npcspeechcycle is 4>>
		<<He>> speaks. ""
		<<elseif $npcspeechcycle is 5>>
		<<He>> speaks. ""
		<<else>>
		<<He>> speaks. ""
		<</if>>

:: Save and load NPC
<<generate1>><<generate2>>
<<saveNPC 0 "john">>
<<saveNPC 1 "jane">>
<<endevent>>

<<loadNPC 0 "john">><<person1>>
<<loadNPC 1 "jane">><<person2>>

<<endevent>>

<<if $per_npc.john isnot undefined>>
	<<loadNPC 0 "john">><<person1>>
	<<endevent>>
<</if>>
<<if $per_npc.jane isnot undefined>>
	<<loadNPC 0 "jane">><<person1>>
	<<endevent>>
<</if>>

<<clearNPC "john">>
<<clearNPC "jane">>

:: Misc

$NPCName[$NPCNameList.indexOf("Robin")].love
<<npcincr Robin love 1>>

<<for _i to 0; _i lt $NPCName.length; _i++>>
<</for>>

<<set $antiquemoney += 40>><<museumAntiqueStatus "antiqueforestdagger" "found">>

/*To capitalise the first letter of a string:*/
<<print $string.toLocaleUpperFirst()>>

/*Using .length with a generic object*/
<<set _skin_keys to Object.keys(setup.bodywriting)>>
<<for _s to 0; _s lt _skin_keys.length; _s++>>
	<<print setup.bodywriting[_skin_keys[_s]].writing>>
	<br>
<</for>>

:: Tentacles
<<effects>>

<<if $molestationstart is 1>>
	<<set $molestationstart to 0>>
	<<set $combat to 1>>
	<<set $enemytype to "tentacles">>
	<<molested>>
	<<controlloss>>

	<<tentaclestart 8 15>>

<</if>>

<<statetentacles>>


<<effects>>
<<effectstentacles>>
<<tentacles>>
<<actionstentacles>>

<<if $tentacles.active lte ($tentacles.max / 2)>>
	<span id="next"><<link [[Next|Tentacles Finish]]>><</link>></span><<nexttext>>
<<else>>
	<span id="next"><<link [[Next|Tentacles]]>><</link>></span><<nexttext>>
<</if>>

:: Tentacles Finish
<<effects>>

Description of escaping/being left alone by the tentacles.
<br><br>

<<tearful>> you escape.
<br><br>

<<clotheson>>
<<endcombat>>

<<link [[Next|Tentacles]]>><</link>>
<br>

/*How to destroy a cursed item, replacing "face" with the slot in question:*/
<<set $worn.face.type.push("broken")>>
<<faceruined>>

<<if $exposed gte 2 and $exhibitionism lt 95 or $exposed gte 2 and $uncomfortable.nude is true>>

<<else>>

<</if>>

:: Masturbation

<<effects>>
<<if $masturbationstart is 1>>
	<<set $masturbationstart to 0>>
	<<set $masturbationstat += 1>>
	<<masturbationstart>>
<</if>>
<<masturbationeffects>>
<<masturbationactions>>

<div id="masturbationButtons">
	<div id="next"><<link [[Continue|Masturbation]]>><</link>><<nexttext>></div>

	<div><<link [[Stop|Masturbation Finish]]>><<set $finish to 1>><</link>></div>
</div>
<br>

:: Masturbation Finish

<<effects>>
Optional text about finishing masturbating.
<br><br>

<<endmasturbation>>
<<endcombat>>

<<tearful>> you continue on your adventure.
<br><br>

<<link [[Next|Masturbation]]>><<clotheson>><</link>>
<br>

/*Splits text by NPC genitals and breastsize*/
<<if $NPCList[0].penis isnot "none">>
	<<if $NPCList[0].breastsize gte 3>>
		They have a penis and reasonably sized breasts.
	<<else>>
		They have a penis and small/no breasts.
	<</if>>
<<else>>
	<<if $NPCList[0].breastsize gte 3>>
		They have no penis and reasonably sized breasts.
	<<else>>
		They have no penis and small/no breasts.
	<</if>>
<</if>>

:: Physique Check

<<physiquedifficulty arg1 arg2>>/*On previous passage after link. Displays the difficulty. First argument is the physique required to have any chance of success. Second argument is the physique required to have a 100% chance of success. Argument 1 defaults to 1 if left blank. Argument 2 defaults to $physiquemax if left blank, which is 20000 as of 0.2.9.0. Argument 3 accepts true and prevents any text from showing in cases where there are multiple checks of the same time in the previous passage*/

/*<<physiquedifficulty arg1 arg2 true>>Optional check just before here when there are multiple checks*/
<<if $physiqueSuccess>>/*Replace 1 and $physiquemax with whatever numbers/variables used as arguments in <<physiquedifficulty>>*/

Text about passing the physique check.

<<else>>

Text about failing the physique check.

<</if>>

:: Encounter Movements

<span class="blue"><<He>> positions <<his>> $NPCList[_n].penisdesc in front of your mouth.</span>
<<neutral 5 "mouth">><<set $mouthuse to "penis">><<set $NPCList[_n].penis to "mouthentrance">><<set $mouthstate to "entrance">><<set $speechmouthentrance to 1>><<set $mouthtarget to _n>>

<span class="purple"><<He>> wraps <<his>> legs around your head and presses <<his>> pussy against your mouth.</span>
<<submission 5>><<set $mouthuse to "othervagina">><<set $NPCList[_n].vagina to "mouth">><<set $mouthstate to "othervagina">><<violence 3>><<bruise face>><<set $speechvaginamouth to 1>><<set $mouthtarget to _n>>

<span class="blue"><<He>> moves between your legs, positioning <<his>> $NPCList[_n].penisdesc in front of your <<pussy>>.</span>
<<neutral 5 "genitals">><<set $vaginause to "penis">><<set $NPCList[_n].penis to "vaginaentrance">><<set $vaginastate to "entrance">><<set $speechvaginaentrance to 1>><<set $vaginatarget to _n>>

<<set $penisuse to "othervagina">><<set $NPCList[_n].vagina to "penisentrance">><<set $penisstate to "entrance">><<set $penistarget to _n>>
<span class="blue"><<He>> straddles you, <<his>> pussy hovering close to your <<penis>>.</span>

<span class="blue"><<He>> moves between your legs, positioning <<his>> $NPCList[_n].penisdesc in front of your <<bottom>>.</span>
<<neutral 5 "bottom">><<set $anususe to "penis">><<set $NPCList[_n].penis to "anusentrance">><<set $anusstate to "entrance">><<set $speechanusentrance to 1>><<set $anustarget to _n>>

:: Monster Selection
<!-- Modified for Monster People -->
<<if ($monsterchance gte 1 and $hallucinations gte 1) or ($monsterchance gte 1 and $monsterhallucinations is "f")>>
	<<if maleChance() lt random(1, 100)>>
		Monstergirl
	<<else>>
		Monsterboy
	<</if>>
<<else>>
	Beast
<</if>>

:: Reminder of how to impact plants outside tending

<<set _garden_location to "garden">>
<<for _i to 0; _i lt $plots[_garden_location].length; _i++>>
	<<set _tending_temp to _i>>
	<<set $plots[_garden_location][_tending_temp].water to 1>>
<</for>>


:: Reminder of how to give plants to the player outside planting

<<tending_harvest red_rose medium 3>>


:: Machine

<<if $molestationstart is 1>>
	<<set $molestationstart to 0>>
	<<controlloss>>
	<<violence 1>>
	<<neutral 1>>

	<<set $machine_health to 10>><<set $machine_ammo to 3>>/*Used by following widget. Must be set.*/
	<<machine_init tattoo vaginal anal arm_chains leg_chains>>/*Include each machine type you want present as an argument*/
	<<set $machine.tattoo.armed to 1>>/*Remove if there's no tattoo gun, or you don't want the tattoo gun to be able to remove tattoos*/
	<<set $machine.vaginal.armed to 1>>/*Remove if there's no vaginal sex machine, or you don't want the sex machine to be able to easily destroy clothes.*/
	<<set $machine.anal.armed to 1>>
	<<prop rails table milk neck_shackle>>/*Delete props as appropriate*/
	<<set $bodywriting_special to "dungeon">>/*Makes all tattoos appropriate for dungeon. Remove for a broader range of tattoos.*/
<</if>>

<<effects>>

<<machine_effects>><<machine_combat>>
<<machine_state>>

/*Debug info. Remove from playable events*/
Number of active machines: <<print $machine.number>><br>
<br>
<<if $machine.tattoo>>
	Tattoo gun use: <<print $machine.tattoo.use>><br>
	Tattoo gun state: <<print $machine.tattoo.state>><br>
	Tattoo gun health: <<print $machine.tattoo.health>><br>
	Tattoo gun hack: <<print $machine.tattoo.hack>><br>
<</if>>
<br>
<<if $machine.vaginal>>
	Phallic machine use: <<print $machine.vaginal.use>><br>
	Phallic machine state: <<print $machine.vaginal.state>><br>
	Phallic machine health: <<print $machine.vaginal.health>><br>
	Phallic machine hack: <<print $machine.vaginal.hack>><br>
	Phallic machine ammo: <<print $machine.vaginal.ammo>><br>
	Phallic machine speed: <<print $machine.vaginal.speed>><br>
<</if>>
<br>
<<if $machine.anal>>
	Small phallic machine use: <<print $machine.anal.use>><br>
	Small phallic machine state: <<print $machine.anal.state>><br>
	Small phallic machine health: <<print $machine.anal.health>><br>
	Small phallic machine hack: <<print $machine.anal.hack>><br>
	Small phallic machine ammo: <<print $machine.anal.ammo>><br>
	Small phallic machine speed: <<print $machine.anal.speed>><br>
<</if>>
<br>
<<if $machine.arm_chains>>
	Arm chains use: <<print $machine.arm_chains.use>><br>
	Arm chains state: <<print $machine.arm_chains.state>><br>
	Arm chains health: <<print $machine.arm_chains.health>><br>
	Arm chains hack: <<print $machine.arm_chains.hack>><br>
<</if>>
<br>
<<if $machine.leg_chains>>
	Leg chains use: <<print $machine.leg_chains.use>><br>
	Leg chains state: <<print $machine.leg_chains.state>><br>
	Leg chains health: <<print $machine.leg_chains.health>><br>
	Leg chains hack: <<print $machine.leg_chains.hack>><br>
<</if>>
/*Debug info end*/


<br><br>
<<machine_actions>>

<<if $machine.number lte 0 or $finish is 1>>
	<<link [[Next|Machine End]]>><</link>>
<<else>>
	<<link [[Next|Machine]]>><</link>>
	<<if $machine.vaginal or $machine.anal>>
		<br>
		<<if $machine.vaginal.speed is "high" or $machine.anal.speed is "high">>
			<<link [[SLOW DOWN|Machine]]>><<machine_speed "normal">><</link>>
		<<else>>
			<<link [[SPEED UP|Machine]]>><<machine_speed "high">><</link>>
		<</if>>
	<</if>>
<</if>>
<br>

<<link [[End|Machine End]]>><</link>>
<br>


:: Machine End
<<effects>>

<<machine_end>>
<<clotheson>>

<<link [[Machine]]>><<set $molestationstart to 1>><</link>>
<br>


:: Struggle
<<effects>>

<<if $struggle_start is 1>>
	<<struggle_init>>
	<<set $struggle.creature to "lurker">>/*Creature species*/
	<<struggle_creatures 5 2>>/*How many creatures will be involved, and their health.*/
	<<set $combat to 1>>
	<<controlloss>>
	<<violence 1>>
	<<molested>>
	<<set $struggle.mouth.creature to "lurker">><<set $mouthuse to "struggle">><<set $mouthstate to "struggle">><<set $struggle.enemy[0].location to "mouth">>/*Encounters can begin with a creature already attached to a body part. Optional.*/
	<<unset $struggle_start>>
<</if>>

<<if $condition is "met">>
	<<struggle_add 1 1>>/*Adds more creatures, with a specific health.*/
	<span class="pink">Another creature attacks!</span>
	<br><br>
<</if>>

<<struggle>>



<<if $struggle.done gte $struggle.number>>
	<span id="next"><<link [[Next|Struggle End]]>><</link>></span>
	<br>
<<else>>
	<span id="next"><<link [[Next|Struggle]]>><</link>></span>
	<br>
<</if>>


:: Struggle End
<<effects>>

Stuff happens.
<br><br>

<<clotheson>>
<<endcombat>>

<<link [[Next|Struggle]]>><<set $struggle_start to 1>><</link>>
<br>

/*Farm stage reminders:
$farm_stage = 1: Alex met, farm work explained.
$farm_stage = 2: Farm work accepted. 1 field clear
$farm_stage = 3: Worked at the farm a little, harasser appeared.
$farm_stage = 4: 2 fields clear. Alex offered booze.
$farm_stage = 5: 3 fields clear. Remy threatened Alex.
$farm_stage = 6: 4 fields clear. Alex's parent visits.
$farm_stage = 7: Time passed since Alex's parent's visit. Bailey visits. Fields are now controlled by the player, steeds can be saddled, and Alex can be chosen as a love interest. Attacks begin. Wall can be upgraded.
$farm_stage = 8: 5 fields clear. More upgrades can be bought.
$farm_stage = 9: 6 fields clear. Lab unlocked. 1 phial available for PC to sell to compound.
$farm_stage = 10: 7 fields clear. "Hurl net" ability unlocked, and more phials can now be produced.
$farm_stage = 11: 8 fields clear. Strange flowers can now be grown.
$farm_stage = 12: 9 fields clear. Remy threatens again.
*/

/*
$kylar_camera = undefined: Event not started.
$kylar_camera = 0: Gift offered, not opened.
$kylar_camera = 1: Gift opened, not accepted.
$kylar_camera = 2: Gift accepted.
$kylar_camera = 3: Given to orphan.
$kylar_camera = 4: Camera discovered in bedroom.
$kylar_camera = 5: Camera discovered in living room.
$kylar_camera = 6: Camera removed.
$kylar_camera = 7: Camera left.
*/

:: Stalk

<<if $molestationstart is 1>>
	<<set $molestationstart to 0>>
	<<violence 1>>
	<<neutral 1>>
	<<maninit>>
	<<stalk_init>>
	<<if Time.dayState isnot "night">>
		<<enable_rescue>>/*Remove if rescue is impossible*/
	<</if>>
	<<set $location to "town">>
<</if>>

<<effects>>
<<effectsman>>
<<alarmstate>>
<<man>>
<<if $audience_active>>
	<<audience>>
<</if>>
<<stateman>>
<br><br>
<<actionsman>>

<<if _combatend or $stalk_end>>
	<span id="next"><<link [[Next|Stalk Finish]]>><</link>></span><<nexttext>>
<<else>>
	<span id="next"><<link [[Next|Stalk]]>><</link>></span><<nexttext>>
<</if>>

:: Stalk Finish
<<effects>>
<<if $enemyarousal gte $enemyarousalmax>>
	<<ejaculation>>
	<<if $combat_end_text>>
		<<print $combat_end_text>>
	<<else>>
		Text about the aftermath of them cumming.
	<</if>>
	<br><br>
	<<tearful>> you recover.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<link [[Next|Stalk]]>><<set $molestationstart to 1>><</link>>/*Link points wherever you want the player to end up*/

<<elseif $enemyhealth lte 0>>
	Text about escaping.
	<br><br>
	<<tearful>> you recover.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<link [[Next|Stalk]]>><<set $molestationstart to 1>><</link>>
<<elseif $stalk_end is "escaped">>
	You slow to a walk. <<tearful>> you continue your journey.
	<br><br>

	<<clotheson>>
	<<endcombat>>

	<<link [[Next|Stalk]]>><<set $molestationstart to 1>><</link>>
	<br>

<<elseif $stalk_end is "passed">>
	You take a deep breath. <<tearful>> you continue your journey.
	<br><br>
	<<clotheson>>
	<<endcombat>>

	<<link [[Next|Stalk]]>><<set $molestationstart to 1>><</link>>
	<br>

<<elseif $stalk_end is "hide">>
	<<covered>> <<tearful>> you emerge from your hiding place. You continue your journey.
	<br><br>

	<<set $stealtextskip to 1>>
	<<stealclothes>>
	<<clotheson>>
	<<endcombat>>

	<<link [[Next|Stalk]]>><<set $molestationstart to 1>><</link>>
	<br>
<<elseif $stalk_end is "outpaced">>/*Unnecessary if the PC can't become the pursuer */
	<<if $exposed gte 1>>
		<<switch $location>>
		<<case alley>>
			<<tearful>> you slow to a stop. <<covered>> There's no one around, but this is still a public place.
		<<case forest lake>>
			<<tearful>> you slow to a stop. <<covered>> There's no one around right now, but there's no knowing who you could meet in the woods.
		<<case moor>>
			<<tearful>> you slow to a stop. <<covered>> There's no one around, but being exposed in such an open place is frightening regardless.
		<<default>>
			<<covered>> <<tearful>> you dive down an alley, hoping to shield your body from any prying eyes.
		<</switch>>
	<<else>>
		<<tearful>> you slow to stop.
	<</if>>
	<br><br>
	<<set $stealtextskip to 1>>
	<<stealclothes>>
	<<clotheson>>
	<<endcombat>>

	<<link [[Next|Stalk]]>><<set $molestationstart to 1>><</link>>
	<br>
<<else>>
	<<set $rescued += 1>>/*Unnecessary if rescue is impossible*/
	<<if $position is "stalk">>
		Text about being rescued while pursued.
	<<else>>
		Text about being rescued while assaulted.
	<</if>>
	<br><br>
	<<tearful>> you recover.
	<br><br>
	<<clotheson>>
	<<endcombat>>
	<<link [[Next|Stalk]]>><<set $molestationstart to 1>><</link>>

<</if>>
<br><br>
<<link [[Escape!|Domus Street]]>><<endevent>><</link>>
<br>

:: Dance
<<effects>>

<<if $dancestart is 1>>
	<<unset $dancestart>>
	<<danceinit>>
	<<set $dancing to 1>>
	<<set $audience to 25>>
	<<set $venuemod to 1>>
	<<set $dancelocation to "party">>
<</if>>

<<danceeffects>>
<<danceaudience>>
<<danceactions>>

<<if $corruptionDancing gt 0 and $danceevent is 0 and (($exhibitionism lte 74 and $exposed gte 2) or ($exhibitionism lte 34 and $exposed gte 1))>>
	There's no way you could normally continue dancing while so exposed.
<<elseif $danceevent is 0 and $exhibitionism lte 74 and $exposed gte 2>>
	There's no way you can continue dancing while so exposed! Face reddening, you flee the scene.
	<br><br>
<<elseif $danceevent is 0 and $exhibitionism lte 34 and $exposed gte 1 and !$worn.under_lower.type.includes("dance")>>
	There's no way you can continue dancing while so exposed! Face reddening, you flee the scene.
	<br><br>
<</if>>

<<if $danceevent is "finish">>
	<<unset $corruptionDancing>>
	<<link [[Next|Brothel]]>><<clotheson>><<endevent>><</link>>
<<elseif $danceevent is "private">>
	<<if $corruptionDancing is 2>>
		The slime wants you to have fun with more than an individual.
	<<elseif $promiscuity gte 35>>
		<<link [[Private room|Brothel Private]]>><<set $phase to 0>><<set $enemyno to 1>><<set $enemynomax to 1>><<unset $corruptionDancing>><</link>><<promiscuous3>>
	<<elseif $promiscuity lte 34 and $uncomfortable.prostituting is false>>
		<<link [[Private room|Brothel Private]]>><<set $phase to 0>><<set $enemyno to 1>><<set $enemynomax to 1>><<unset $corruptionDancing>><<set $desperateaction to 1>><</link>><<promiscuous3>>
		<br>
	<</if>>
<<elseif $danceevent is "rape">>
	<<link [[Next|Brothel Dance Rape]]>><<set $molestationstart to 1>><<unset $corruptionDancing>><</link>>
<<elseif $danceevent is "leighton">>
	<<if $corruptionDancing is 2>>
		The slime wants you to have fun with more than an individual.
	<<elseif $promiscuity gte 35>>
		<<link [[Private room|Leighton Private]]>><<clotheson>><<endevent>><<unset $corruptionDancing>><</link>><<promiscuous3>>
		<br>
	<</if>>
<<elseif $danceevent is "robin">>
	<<if $corruptionDancing is 2>>
		The slime wants you to have fun with more than an individual.
	<<else>>
		<<link [[Private room|Robin Brothel]]>><<clotheson>><<endevent>><<unset $corruptionDancing>><</link>>
	<</if>>

<<elseif $danceevent is 0>>
	<<if $corruptionDancing isnot undefined>>
		The slime in your ear is forcing you.
	<<elseif $exposed gte 2 and $exhibitionism lte 74>>
		<<link [[Flee|Brothel Dressing Room]]>><<clotheson>><<endevent>><<unset $corruptionDancing>><</link>>
	<<elseif $exposed gte 1 and $exhibitionism lte 34>>
		<<link [[Flee|Brothel Dressing Room]]>><<clotheson>><<endevent>><<unset $corruptionDancing>><</link>>
	<<else>>
		<<link [[Stop|Brothel]]>><<clotheson>><<endevent>><<unset $corruptionDancing>><</link>>
	<</if>>
<</if>>
/*More simple setup below */
<<if $danceevent is "rape">>
	<<link [[Next|Beach Party Dance Rape]]>><<set $molestationstart to 1>><</link>>
<<elseif $danceevent is "finish">>
	<<link [[Next|Beach Party]]>><<clotheson>><<endevent>><</link>>
<<elseif $danceevent is 0>>
	<<if $exposed gte 2 and $exhibitionism lte 74>>
		<<link [[Flee|Changing Room]]>><<clotheson>><<endevent>><</link>>
	<<elseif $exposed gte 1 and $exhibitionism lte 34>>
		<<link [[Flee|Changing Room]]>><<clotheson>><<endevent>><</link>>
	<<else>>
		<<link [[Stop|Beach Party]]>><<clotheson>><<endevent>><</link>>
	<</if>>
<</if>>

:: Preg


<<print $sexStats.vagina.sperm["plump man"].count>><br>
Menstruation state: <<print $sexStats.vagina.menstruation.currentState>><br>
Menstruation day: <<print $sexStats.vagina.menstruation.currentDay>><br>

"""
twee=TweeLexer.create_twee_lexer(text)
print(twee)
for item in twee.items:
    print(item.to_string())
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
