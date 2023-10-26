import re
from pathlib import Path

from . import logger
from .consts import *


class ParseTextTwee:

    def __init__(self, lines: list[str], filepath: Path):
        self._lines = lines
        self._filepath = filepath

        self._filename = self._filepath.name  # 文件名
        self._filedir = self._filepath.parent  # 文件夹

    def parse(self) -> list[bool]:
        if DirNamesTwee.NORMAL.value in self._filedir.name:
            return self.parse_normal()
        elif DirNamesTwee.FRAMEWORK.value in {
            self._filedir.name,
            self._filedir.parent.name,
        }:
            return self.parse_framework()
        elif DirNamesTwee.CONFIG.value == self._filedir.name:
            return self.parse_config()
        elif DirNamesTwee.VARIABLES.value == self._filedir.name:
            return self.parse_variables()
        elif DirNamesTwee.BASE_CLOTHING.value == self._filedir.name:
            return self.parse_base_clothing()
        elif DirNamesTwee.BASE_COMBAT.value in {
            self._filedir.name,
            self._filedir.parent.name,
        }:
            return self.parse_base_combat()
        elif DirNamesTwee.BASE_DEBUG.value == self._filedir.name:
            return self.parse_base_debug()
        # elif DirNamesTwee.BASE_HAIR.value == self._filedir.name:
        #     return self.parse_base_hair()
        elif DirNamesTwee.BASE_SYSTEM.value in {
            self._filedir.name,
            self._filedir.parent.name,
        }:
            return self.parse_base_system()
        elif DirNamesTwee.FLAVOUR_TEXT_GENERATORS.value == self._filedir.name:
            return self.parse_flavour_text()

        return self.parse_normal()

    """√ framework-tools """
    def parse_framework(self):
        """ 00-framework-tools"""
        if FileNamesTwee.WAITING_ROOM_FULL.value == self._filename:
            return self._parse_waiting_room()
        return self.parse_normal()

    def _parse_waiting_room(self):
        """很少很简单"""
        return [
            line.strip() and (
                "<span " in line.strip()
                or (not line.startswith("<") and "::" not in line)
            ) for line in self._lines
        ]

    """√ config """
    def parse_config(self):
        """ 01-config """
        if FileNamesTwee.START_FULL.value == self._filename:
            return self._parse_start()
        elif FileNamesTwee.VERSION_INFO_FULL.value == self._filename:
            return self._parse_version_info()
        return self.parse_normal()

    def _parse_start(self):
        """很少很简单"""
        return [
            line.strip() and (
                "<span " in line.strip()
                or "<<link [[" in line.strip()
                or any(re.findall(r"^(\w|- )", line.strip()))
            ) for line in self._lines
        ]

    def _parse_version_info(self):
        """很少很简单"""
        return [
            line.strip() and (
                not line.strip().startswith("<") and "::" not in line
            ) for line in self._lines
        ]

    """√ variables """
    def parse_variables(self):
        """ 04-Variables """
        if FileNamesTwee.CANVASMODEL_FULL.value == self._filename:
            return self._parse_canvasmodel()
        elif FileNamesTwee.VERSION_UPDATE_FULL.value == self._filename:
            return self._parse_version_update()
        elif FileNamesTwee.PASSAGE_FOOTER_FULL.value == self._filename:
            return self._parse_passage_footer()
        elif FileNamesTwee.PREGNANCY_VAR_FULL.value == self._filename:
            return self._parse_pregnancy_var()
        elif FileNamesTwee.VARIABLES_STATIC_FULL.value == self._filename:
            return self._parse_variables_static()
        elif FileNamesTwee.HAIR_STYLES_FULL.value == self._filename:
            return self._parse_hair_style()
        return self.parse_normal()

    def _parse_canvasmodel(self):
        """只有一个<<link"""
        return self.parse_type_only("<<link [[")

    def _parse_version_update(self):
        """只有 <span 和 <<link """
        return self.parse_type_only({"<span ", "<<link "})

    def _parse_passage_footer(self):
        """有点麻烦"""
        results = []
        multirow_error_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行error，逆天"""
            if line in ["<<error {", "<<script>>"]:
                multirow_error_flag = True
                results.append(False)
                continue
            elif line in ["}>>", "<</script>>"]:
                multirow_error_flag = False
                results.append(False)
                continue
            elif multirow_error_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif "<span" in line or "<<link" in line or not line.startswith("<"):
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_pregnancy_var(self):
        """只有 "name": """
        return self.parse_type_only({'"name": '})

    def _parse_variables_static(self):
        """ variables-static.twee """
        results = []
        multirow_set_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if (
                "<<set setup.npcPenisRemarks to {" in line
                or "<<set setup.crimeNames to {" in line
                or "<<set setup.crimeDescs to {" in line
            ):
                multirow_set_flag = True
                results.append(False)
                continue
            elif multirow_set_flag and "}>>" in line:
                multirow_set_flag = False
                results.append(False)
                continue
            elif multirow_set_flag:
                results.append(True)
                continue

            if "setup.breastsizes" in line:
                results.append(True)
            elif (
                '"name": "' in line
                or '"message": "' in line
            ):
                results.append(True)
            else:
                results.append(False)
        return results

    """√ base-clothing """
    def parse_base_clothing(self):
        """ base-clothing """
        if FileNamesTwee.CAPTIONTEXT_FULL.value == self._filename:
            return self._parse_captiontext()
        # elif FileNamesTwee.CLOTHING.value in self._filename and FileNamesTwee.CLOTHING_SETS_FULL.value != self._filename:
        #     return self._parse_clothing()
        elif FileNamesTwee.CLOTHING_SETS_FULL.value == self._filename:
            return self._parse_clothing_sets()
        elif FileNamesTwee.CLOTHING_IMAGES_FULL.value == self._filename:
            return self._parse_clothing_images()
        elif FileNamesTwee.INIT_FULL.value == self._filename:
            return self._parse_clothing_init()
        elif FileNamesTwee.WARDROBES_FULL.value == self._filename:
            return self._parse_wardrobes()
        return self.parse_normal()

    def _parse_captiontext(self):
        """有点麻烦"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if (
                self.is_comment(line)
                or self.is_event(line)
                or self.is_only_marks(line)
            ):
                results.append(False)
            elif self.is_tag_span(line) or self.is_widget_set_to(line, {
                r"\$_text_output", "_wearing", r"\$_output",
                "_finally", r"\$_verb", "_output",
                "_text_output", r"\$_pair", r"\$_a",
                r"\$_clothes", r"\$_highestLevelCovered"
            }):
                results.append(True)
            elif "<<run $_output " in line:
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)

        return results

    # def _parse_clothing(self):
    #     """json"""
    #     return self.parse_type_only({"name_cap:", "description:", "<<link `"})

    def _parse_clothing_sets(self):
        """好麻烦"""
        results = []
        multirow_comment_flag = False
        multirow_json_flag = False
        for idx, line in enumerate(self._lines):
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释，逆天"""
            if (line in ["/*", "<!--"] or (any(line.startswith(_) for _ in {"/*", "<!--"}) and all(_ not in line for _ in {"*/", "-->"}))):
                multirow_comment_flag = True
                results.append(False)
                continue
            elif multirow_comment_flag and (line in ["*/", "-->"] or any(line.endswith(_) for _ in {"*/", "-->"})):
                multirow_comment_flag = False
                results.append(False)
                continue
            elif multirow_comment_flag:
                results.append(False)
                continue

            """就为这一个单开一档，逆天"""
            if (line.startswith("<<run ") or line.startswith("<<set ")) and ">>" not in line:
                multirow_json_flag = True
                results.append(False)
                continue
            elif multirow_json_flag and any(_ in line for _ in {"}>>", "})>>"}):
                multirow_json_flag = False
                results.append(False)
                continue
            elif multirow_json_flag and any(_ in line for _ in {'"start"', '"joiner"', '"end"'}):
                results.append(True)
                continue
            elif multirow_json_flag:
                results.append(False)
                continue

            if "<<set _notEquipped[$_slot]" in line:
                results.append(True)
            elif self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif (
                self.is_tag_span(line)
                or self.is_tag_label(line)
                or self.is_widget_option(line)
                or self.is_widget_link(line)
                or self.is_widget_set_to(line, {
                    r"\$wearoutfittext", "_wardrobeName"
                })
                or "$_value2.name" in line
                or "<<print $_label" in line
                or "<<set $_options to []>>" in line
                or "(No access)" in line
            ):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_clothing_images(self):
        """只有 <span"""
        return self.parse_type_only("<span ")

    def _parse_clothing_init(self):
        """只有 desc:"""
        return self.parse_type_only({
            "desc:", "V.outfit = ", 'word:"',
            'name: "'
        })

    def _parse_wardrobes(self):
        """多了一个<<wearlink_norefresh " """
        results = []
        multirow_if_flag = False
        multirow_set_flag = False
        multirow_run_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行if，逆天"""
            if line.startswith("<<if ") and ">>" not in line:
                multirow_if_flag = True
                results.append(False)
                continue
            elif multirow_if_flag and ">>" in line:
                multirow_if_flag = False
                results.append(False)
                continue
            elif multirow_if_flag:
                results.append(False)
                continue

            """跨行set，逆天"""
            if (line.startswith("<<set _itemStats ") or line.startswith("<<set _sortedItemColors")) and ">>" not in line:
                multirow_set_flag = True
                results.append(False)
                continue
            elif multirow_set_flag and line in {"]>>", "})>>", "}>>"}:
                multirow_set_flag = False
                results.append(False)
                continue
            elif multirow_set_flag:
                results.append(False)
                continue

            """跨行run，逆天"""
            if line.startswith("<<run ") and ">>" not in line:
                multirow_run_flag = True
                results.append(False)
                continue
            elif multirow_run_flag and line in {"})>>", "}>>", ")>>", "]>>", "});>>"}:
                multirow_run_flag = False
                results.append(False)
                continue
            elif multirow_run_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif (
                self.is_tag_span(line)
                or '<<wearlink_norefresh "' in line
                or '>>.' in line
                or self.is_tag_label(line)
                or self.is_widget_print(line)
                or self.is_widget_option(line)
                or self.is_widget_link(line)
                or self.is_widget_set_to(line, {
                    r"\$_text_output", r"\$_output", "_linkOption1", "_linkOption2",
                    r"\$_itemNames", r"\$_link", r"\$_linkOption"
                })
                or "__" in line
                or '? "' in line
            ):
                results.append(True)
            elif self.is_only_widgets(line) or self.is_json_line(line):
                results.append(False)
            else:
                results.append(True)
        return results

    """√ base-combat """
    def parse_base_combat(self):
        """ base-combat """
        if FileNamesTwee.ACTIONS_FULL.value == self._filename or FileNamesTwee.ACTIONS.value in self._filename:
            return self._parse_actions()
        if FileNamesTwee.STALK_FULL.value == self._filename:
            return self._parse_stalk()
        elif FileNamesTwee.GENERATION.value in self._filename:
            return self._parse_generation()
        elif FileNamesTwee.TENTACLE_ADV_FULL.value == self._filename:
            return self._parse_tentacle_adv()
        elif FileNamesTwee.TENTACLES_FULL.value == self._filename:
            return self._parse_tentacles()
        elif FileNamesTwee.COMBAT_EFFECTS_FULL.value == self._filename:
            return self._parse_combat_effects()
        elif self._filename in {
            FileNamesTwee.NPC_GENERATION_FULL.value,
            FileNamesTwee.NPC_DAMAGE_FULL.value
        }:
            return self._parse_npc_span()
        elif FileNamesTwee.SPEECH_SYDNEY_FULL.value == self._filename:
            return self._parse_speech_sydney()
        elif FileNamesTwee.SPEECH_FULL.value == self._filename:
            return self._parse_speech()
        elif FileNamesTwee.STRUGGLE_FULL.value == self._filename:
            return self._parse_struggle()
        elif FileNamesTwee.SWARMS_FULL.value == self._filename:
            return self._parse_swarms()
        elif FileNamesTwee.SWARM_EFFECTS_FULL.value == self._filename:
            return self._parse_swarm_effects()
        elif FileNamesTwee.COMBAT_WIDGETS_FULL.value == self._filename:
            return self._parse_combat_widgets()
        elif FileNamesTwee.COMBAT_IMAGES_FULL.value == self._filename:
            return self._parse_combat_images()
        return self.parse_normal()

    def _parse_actions(self):
        """麻烦"""
        results = []
        multirow_if_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行if，逆天"""
            if line.startswith("<<if ") and ">>" not in line:
                multirow_if_flag = True
                results.append(False)
                continue
            elif multirow_if_flag and ">>" in line:
                multirow_if_flag = False
                results.append(False)
                continue
            elif multirow_if_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line) or line == "<<print either(":
                results.append(False)
            elif (
                self.is_tag_span(line)
                or self.is_widget_print(line)
                or self.is_tag_label(line)
                or self.is_widget_option(line)
                or self.is_widget_set_to(line, {
                    "_leftaction", "_rightaction", "_feetaction",
                    "_targetlistarms", "_targetlistall", "_mouthaction",
                    "_anusaction", "_actions", "_undressLeftTargets",
                    "_undressRightTargets", "_handGuideOptions", "_penisaction",
                    "_askActions", "_vaginaaction", "_text_output", "_chestaction",
                    "_thighaction", "_npccr", "_npcff", r"\$_doText", "_youraction",
                    "_otheraction", "_enjoying", "_mydesc", "_smoltext", r"\$_npc",
                    r"\$_pussyDesc", r"\$_penis", "_penis", "_pron", "_eagerclimax",
                    "_dick", r"\$_pp", "_eagerfor", "_pp", "_hammering", r"\$_hands",
                    r"\$_genital"
                })
                or "<<run delete " in line
                or "<<if $NPCList" in line
                or "<<if ($NPCList" in line
                or "<<takeKissVirginityNamed" in line
                or "<<set _feetaction" in line
                or "<<set _targetlist" in line
                or "<<set _anonymous" in line
                or "<<set _smollertext" in line
                or "_smollertext.includes" in line
                or "$NPCList[_j].breastsdesc." in line
            ):
                results.append(True)
            elif self.is_only_widgets(line) or self.is_json_line(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_stalk(self):
        """麻烦"""
        results = []
        multirow_if_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行if，逆天"""
            if line.startswith("<<if ") and ">>" not in line:
                multirow_if_flag = True
                results.append(False)
                continue
            elif multirow_if_flag and ">>" in line:
                multirow_if_flag = False
                results.append(False)
                continue
            elif multirow_if_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line) or line == "<<print either(":
                results.append(False)
            elif (
                self.is_tag_span(line)
                or self.is_widget_set_to(line, {
                    "_wraith_output"
                })
                or '<<skill_difficulty ' in line
                or ">>." in line
            ):
                results.append(True)
            elif self.is_only_widgets(line) or self.is_json_line(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_generation(self):
        """只有 <span """
        results = []
        multirow_d_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if "set _d to" in line:
                multirow_d_flag = True
                results.append(True)
                continue
            elif multirow_d_flag and "]>>" in line:
                multirow_d_flag = False
                results.append(False)
                continue
            elif multirow_d_flag:
                results.append(True)
                continue

            if (
                self.is_tag_span(line)
                or self.is_widget_set_to(line, {
                    r"\$NPCList\[_n\]\.hair",
                    r"\$_desc",
                    r"\$NPCList\[_slot\]\.fullDescription",
                    r"\$NPCList\[_n\]\.fullDescription",
                    r"\$NPCList\[_n\]\.breastsdesc",
                    r"\$NPCList\[_n\]\.breastdesc",
                    r"\$NPCList\[_n\]\.penisdesc",
                    r"\$NPCList\[_xx\]\.penisdesc",
                    "_brdes", "_pd", r"\$_strapon", "_dildoType", r"\$_modifier"
                })
            ):
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_tentacle_adv(self):
        """有点麻烦"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if (
                self.is_comment(line)
                or self.is_event(line)
                or self.is_only_marks(line)
                or line == "_tentacle.desc"
            ):
                results.append(False)
            elif self.is_tag_span(line) or self.is_widget_actions_tentacle(line) or self.is_widget_if(line):
                results.append(True)
            elif (
                '.desc.includes' in line
                or "fullDesc.includes" in line
                or "<<takeHandholdingVirginity" in line
                or "<<set _Slimy" in line
            ):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_tentacles(self):
        """有点麻烦"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if (
                self.is_comment(line)
                or self.is_event(line)
                or self.is_only_marks(line)
            ):
                results.append(False)
            elif any(_ in line for _ in {
                "_tentacledata.desc", "fullDesc.includes",
                '{"desc":', "you", "You", "YOU"
            }):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(False)
        return results

    def _parse_combat_effects(self):
        """有点麻烦"""
        results = []
        multirow_widget_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释/script，逆天"""
            if (
                line in ["/*", "<!--"]
                or (
                    any(line.startswith(_) for _ in {"/*", "<!--"})
                    and all(_ not in line for _ in {"*/", "-->"})
                )
            ):
                multirow_widget_flag = True
                results.append(False)
                continue
            elif multirow_widget_flag and line in ["*/", "-->"] or any(line.endswith(_) for _ in {"*/", "-->"}):
                multirow_widget_flag = False
                results.append(False)
                continue
            elif multirow_widget_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif (
                self.is_tag_span(line)
                or self.is_widget_print(line)
                or self.is_widget_set_to(line, {
                    "_wraith_output", "_npcDescription", "_insertions",
                    "_action"
                })
            ):
                results.append(True)
            elif any(_ in line for _ in {
                "<<wheeze",
                ">>."
            }):
                results.append(True)
            elif self.is_only_widgets(line) or self.is_json_line(line) or ("<<set " in line and ">>" not in line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_npc_span(self):
        """只有 <span"""
        return self.parse_type_only({
            "<span ", "<<set $NPCList[_n].fullDescription",
            "<<set $NPCList[_n].breastdesc"
        })

    def _parse_speech_sydney(self):
        """有点麻烦"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if (
                self.is_comment(line)
                or self.is_event(line)
                or self.is_only_marks(line)
            ):
                results.append(False)
            elif (
                self.is_widget_set_to(line, {
                    "_sexToy", "_sydneyText"
                })
                or line.startswith("`")
            ):
                results.append(True)
            elif (
                self.is_only_widgets(line)
                or ("<<set " in line and ">>" not in line)
            ):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_speech(self):
        """有点麻烦"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if (
                self.is_comment(line)
                or self.is_event(line)
                or self.is_only_marks(line)
            ):
                results.append(False)
            elif (
                self.is_widget_set_to(line, {
                    r"\$_text_output", r"\$_sexToy", r"\$_strings",
                    r"\$_toyOrFinger"
                })
                or line.startswith('"')
                or line.startswith('`')
                or line.startswith('<<default>>')
                or line.startswith('<<He>> ')
                or line.startswith('<<bHe>> ')
                or "<span " in line
                or any(re.findall(r"<<case \d", line))
            ):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(False)
        return results

    def _parse_struggle(self):
        """有点麻烦"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if (
                self.is_comment(line)
                or self.is_event(line)
                or self.is_only_marks(line)
                or self.is_json_line(line)
            ):
                results.append(False)
            elif self.is_widget_set_to(line, {
                r"\$_text_output", "_text_output", "_targetlistall",
                "_leftaction", "_feetaction", "_mouthaction",
                "_targetlistarms", "_rightaction", r"\$struggle\.descriptions",
                "_fulldesc", r"\$_desc"
            }):
                results.append(True)
            elif self.is_widget_print(line):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_swarms(self):
        """有点麻烦"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue
            if "$worn.upper.name," in line or "$worn.lower.name," in line:
                results.append(True)
            elif (
                self.is_comment(line)
                or self.is_event(line)
                or self.is_only_marks(line)
                or self.is_json_line(line)
            ):
                results.append(False)
            elif self.is_widget_set_to(line, {
                "_leftaction", "_rightaction", "_feetaction",
                "_targetlistarms", "_targetlistall", "_swarmname"
            }):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_swarm_effects(self):
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif (
                "<" in line and (
                    self.is_tag_span(line)
                    or self.is_tag_label(line)
                    or ("<<set " in line and self.is_widget_set_to(line, {
                        "_leftaction", "_rightaction", "_feetaction",
                        "_targetlistarms", "_targetlistall"
                    }))
                )
            ):
                results.append(True)
            elif "<" in line and (self.is_only_widgets(line) or self.is_json_line(line)):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_combat_widgets(self):
        """有点麻烦"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if (
                self.is_comment(line)
                or self.is_event(line)
                or self.is_only_marks(line)
                or self.is_json_line(line)
            ):
                results.append(False)
            elif self.is_tag_span(line) or self.is_widget_set_to(line, {
                "_text_output", "_leftaction", "_rightaction",
                r"\$player\.virginity", r"\$_alongside"
            }):
                results.append(True)
            elif (
                "<<if $_npc" in line
                or "<<if ($NPCList[$_" in line
                or "<<if $NPCList[$_" in line
            ):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_combat_images(self):
        results = []
        for idx, line in enumerate(self._lines):
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if "if $NPCList[$_target" in line:
                results.append(True)
            else:
                results.append(False)
        return results

    """ base-debug """
    def parse_base_debug(self):
        return self.parse_normal()

    """√ base-hair """
    # def parse_base_hair(self):
    #     if FileNamesTwee.HAIR_STYLES_FULL.value == self._filename:
    #         return self._parse_hair_style()
    #     return self.parse_normal()

    def _parse_hair_style(self):
        """json"""
        return self.parse_type_only("name_cap")

    """ base-system """
    def parse_base_system(self):
        """ base-system """
        if FileNamesTwee.CHARACTERISTICS_FULL.value == self._filename:
            return self._parse_characteristic()
        elif FileNamesTwee.SOCIAL_FULL.value == self._filename:
            return self._parse_social()
        elif FileNamesTwee.TRAITS_FULL.value == self._filename:
            return self._parse_traits()
        elif FileNamesTwee.BODYWRITING_FULL.value == self._filename:
            return self._parse_body_writing()
        elif FileNamesTwee.BODYWRITING_OBJECTS_FULL.value == self._filename:
            return self._parse_body_writing_objects()
        elif FileNamesTwee.CAPTION_FULL.value == self._filename:
            return self._parse_caption()
        elif self._filename in {
            FileNamesTwee.DEVIANCY_FULL.value,
            FileNamesTwee.SYSTEM_EXHIBITIONISM_FULL.value,
            FileNamesTwee.PROMISCUITY_FULL.value
        }:
            return self._parse_sex_stat()
        elif FileNamesTwee.FAME_FULL.value == self._filename:
            return self._parse_fame()
        elif FileNamesTwee.FEATS_FULL.value == self._filename:
            return self._parse_feats()
        elif FileNamesTwee.CLOTHING_IMAGES_FULL.value == self._filename:
            return self._parse_system_images()
        elif FileNamesTwee.MOBILE_STATS_FULL.value == self._filename:
            return self._parse_mobile_stats()
        elif FileNamesTwee.NAME_LIST_FULL.value == self._filename:
            return self._parse_name_list()
        elif FileNamesTwee.NICKNAMES_FULL.value == self._filename:
            return self._parse_nicknames()
        elif FileNamesTwee.PLANT_OBJECTS_FULL.value == self._filename:
            return self._parse_plant_objects()
        elif FileNamesTwee.RADIO_FULL.value == self._filename:
            return self._parse_radio()
        elif FileNamesTwee.SETTINGS_FULL.value == self._filename:
            return self._parse_settings()
        elif FileNamesTwee.SKILL_DIFFICULTIES_FULL.value == self._filename:
            return self._parse_skill_difficulties()
        elif FileNamesTwee.SLEEP_FULL.value == self._filename:
            return self._parse_sleep()
        elif FileNamesTwee.STAT_CHANGES_FULL.value == self._filename:
            return self._parse_stat_changes()
        elif FileNamesTwee.TENDING_FULL.value == self._filename:
            return self._parse_tending()
        elif FileNamesTwee.TEXT_FULL.value == self._filename:
            return self._parse_system_text()
        elif FileNamesTwee.TIME_FULL.value == self._filename:
            return self._parse_time()
        elif FileNamesTwee.TIPS_FULL.value == self._filename:
            return self._parse_tips()
        elif FileNamesTwee.TRANSFORMATIONS_FULL.value == self._filename:
            return self._parse_transformations()
        elif FileNamesTwee.SYSTEM_WIDGETS_FULL.value == self._filename:
            return self._parse_system_widgets()
        elif FileNamesTwee.NAMED_NPCS_FULL.value == self._filename:
            return self._parse_named_npcs()
        elif FileNamesTwee.PERSISTENT_NPCS_FULL.value == self._filename:
            return self._parse_persistent_npcs()
        return self.parse_normal()

    def _parse_characteristic(self):
        """有点麻烦"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if (
                self.is_comment(line)
                or self.is_event(line)
                or self.is_only_marks(line)
            ):
                results.append(False)
            elif (
                "description: " in line
                or "{ name :" in line
                or "preText: " in line
                or 'level: "None"' in line
                or line == '<<if $_number isnot "an unknown number of" and $_number isnot "more than one" and $_number gt 1>>'
                or self.is_tag_span(line)
                or self.is_widget_set_to(line, {
                    "_trimester",  "_vaginaWetnessTextConfig",
                    "_childType", r"\$_pregnancyRisk", r"\$_number",
                    "_milkCapacityTextConfig", r"\$_heatRutDisplay",
                    r"\$_bellyText"
                })
                or "bad.pushUnique" in line
                or "good.pushUnique" in line
                or ">>." in line
            ):
                results.append(True)
            elif (
                self.is_only_widgets(line)
                or ("<<set " in line and ">>" not in line and "preText: " not in line)
                or line == "states : ["
            ):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_social(self):
        """有点麻烦"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if (
                self.is_comment(line)
                or self.is_event(line)
                or self.is_only_marks(line)
            ):
                results.append(False)
            elif (
                "description: '" in line
                or self.is_tag_span(line)
                or "preText: " in line
                or self.is_widget_set_to(line, {
                    r"\$_pre", r"\$_flavor", r"\$_name"
                })
            ):
                results.append(True)
            elif (
                self.is_json_line(line)
                or self.is_only_widgets(line)
            ):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_traits(self):
        """half-json"""
        return self.parse_type_only({
            "name:", "text:", "title:", "<summary", "<<option",
            'return "Incubus', 'return "Succubus',
            'return "Bull boy', 'return "Cow girl',
            'return "Fox', 'return "Vixen', "Display Format:",
            "<label>S", "<<link"
        })

    def _parse_body_writing(self):
        """有点麻烦"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if (
                self.is_comment(line)
                or self.is_event(line)
                or self.is_only_marks(line)
            ):
                results.append(False)
            elif self.is_widget_set_to(line, {"_text_output", r"\$_writing"}) or self.is_tag_span(line):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_body_writing_objects(self):
        """half-json"""
        return self.parse_type_only({"writing: ", "special: ", "sprites: "})

    def _parse_caption(self):
        """竟然还有css"""
        results = []
        multirow_style_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释/script，逆天"""
            if line == "<style>":
                multirow_style_flag = True
                results.append(False)
                continue
            elif line == "</style>":
                multirow_style_flag = False
                results.append(False)
                continue
            elif multirow_style_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif self.is_tag_span(line) or self.is_widget_button(line) or self.is_widget_print(line):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_sex_stat(self):
        """纯文本"""
        return self.parse_type_pure_text()

    def _parse_fame(self):
        """set $_output to"""
        return self.parse_type_only({
            "<<set $_output"
        })

    def _parse_feats(self):
        """json"""
        results = []
        json_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if line in {"missing:{", "name:{"}:
                json_flag = True
                results.append(False)
            elif line == "},":
                json_flag = False
                results.append(False)
            elif json_flag:
                results.append(True)
            else:
                results.append(False)

        return results

    def _parse_system_images(self):
        """只有span"""
        return self.parse_type_only_regex(r"<span.*?>[\"\w]")

    def _parse_mobile_stats(self):
        """只有<span>"""
        return self.parse_type_only("<span>")

    def _parse_name_list(self):
        """只有 " """
        return self.parse_type_startwith('"')

    def _parse_named_npcs(self):
        """有点麻烦"""
        results = []
        multirow_comment_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释/set，逆天"""
            if (line in ["/*", "<!--"] or (any(line.startswith(_) for _ in {"/*", "<!--"}) and all(_ not in line for _ in {"*/", "-->"}))):
                multirow_comment_flag = True
                results.append(False)
                continue
            elif multirow_comment_flag and (line in ["*/", "-->"] or any(line.endswith(_) for _ in {"*/", "-->"})):
                multirow_comment_flag = False
                results.append(False)
                continue
            elif multirow_comment_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif line == "_npc":
                results.append(True)
            elif (
                "<<set $NPCList[_ii].breastsdesc" in line
                or "<<set $NPCList[_ii].breastdesc" in line
                or "<<set $NPCList[_ii].penisdesc" in line
            ):
                results.append(True)
            elif self.is_tag_span(line) or self.is_widget_set_to(line, {
                r"\$_npcName\.strapons", "_brdes", r"\$NPCList\[_npcno\]"
            }):
                results.append(True)
            elif "<<set $NPCName[_i" in line and all(_ not in line for _ in {
                ".gender", ".pronoun", "size to", "1>>", "0>>", ".outfits.pushUnique(",
                "_val", "_rollover", "9>>", "random", "undefined", "delete", "crossdressing"
            }):
                results.append(True)
            elif self.is_tag_span(line):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_nicknames(self):
        """只有 " """
        results = []
        multirow_set_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if line.startswith("<<set ") and ">>" not in line:
                multirow_set_flag = True
                results.append(False)
                continue
            elif multirow_set_flag and line in {"]>>", "})>>", "}>>", ")>>"}:
                multirow_set_flag = False
                results.append(False)
                continue
            elif multirow_set_flag and any(_ in line for _ in {
                "_names.push", "_pre.push"
            }):
                results.append(False)
                continue
            elif multirow_set_flag:
                results.append(True)
                continue

            if self.is_widget_set_to(line, {
                "_text_output", r"_pre\.push", r"_names\.push"
            }):
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_plant_objects(self):
        """json"""
        return self.parse_type_only("plural:")

    def _parse_radio(self):
        """有点麻烦"""
        results = []
        multirow_comment_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释，逆天"""
            if line in ["/*", "<!--"] or (
                    any(line.startswith(_) for _ in {"/*", "<!--"}) and all(_ not in line for _ in {"*/", "-->"})):
                multirow_comment_flag = True
                results.append(False)
                continue
            elif line in ["*/", "-->"] or any(line.endswith(_) for _ in {"*/", "-->"}):
                multirow_comment_flag = False
                results.append(False)
                continue
            elif multirow_comment_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line):
                results.append(False)
            elif (
                self.is_widget_link(line)
                or "<i>" in line
                or "<b>" in line
                or any(re.findall(r"^\"\w", line))
            ):
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_settings(self):
        """草"""
        results = []
        multirow_comment_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释/error，逆天"""
            if line in ["/*", "<!--", "<<error {"] or (any(line.startswith(_) for _ in {"/*", "<!--", "<<error {"}) and all(_ not in line for _ in {"*/", "-->", "}>>"})):
                multirow_comment_flag = True
                results.append(False)
                continue
            elif multirow_comment_flag and (line in ["*/", "-->", "}>>"] or any(line.endswith(_) for _ in {"*/", "-->", "}>>"})):
                multirow_comment_flag = False
                results.append(False)
                continue
            elif multirow_comment_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif (
                self.is_widget_button(line)
                or self.is_tag_span(line)
                or self.is_tag_label(line)
                or self.is_tag_input(line)
                or self.is_widget_print(line)
                or self.is_widget_link(line)
                or self.is_widget_set_to(line, {
                    "_buttonName", "_name", "_penisNames", "_breastDescriptionNPC",
                    "_breastsDescriptionNPC", "_hairColorNPCText", "_eyeColorNPCText"
                })
            ):
                results.append(True)
            elif (
                "<<set _npcList[clone($NPCNameList[$_i])]" in line
                or "<<run delete _npcList" in line
                or ".toUpperFirst()" in line
                or "<<if _npcList[$NPCName[_npcId].nam] is undefined>>" in line
                or "<<startOptionsComplexityButton" in line
                or "<<settingsTabButton" in line
                or "<<subsectionSettingsTabButton" in line
            ):
                results.append(True)
            elif "<" in line and self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_skill_difficulties(self):
        """麻烦"""
        results = []
        multirow_comment_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释/error，逆天"""
            if line in ["/*", "<!--", "<<error {"] or (
                    any(line.startswith(_) for _ in {"/*", "<!--", "<<error {"}) and all(
                    _ not in line for _ in {"*/", "-->", "}>>"})):
                multirow_comment_flag = True
                results.append(False)
                continue
            elif line in ["*/", "-->", "}>>"] or any(line.endswith(_) for _ in {"*/", "-->", "}>>"}):
                multirow_comment_flag = False
                results.append(False)
                continue
            elif multirow_comment_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif "<span " in line or "<<set _text_output" in line:
                results.append(True)
            elif line.startswith("<"):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_sleep(self):
        """<span , <<link, 纯文本"""
        return [
            line.strip() and (
                ("<<link [[" in line.strip() and "[[Next" not in line.strip())
                or (not line.strip().startswith("<") and not line.strip().startswith("/*") and "::" not in line.strip())
                or "<span " in line.strip()
            ) for line in self._lines
        ]

    def _parse_stat_changes(self):
        """只有<span"""
        return self.parse_type_only("<span ")

    def _parse_tending(self):
        """麻烦"""
        results = []
        multirow_comment_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释，逆天"""
            if line in ["/*", "<!--"] or (any(line.startswith(_) for _ in {"/*", "<!--"}) and all(_ not in line for _ in {"*/", "-->"})):
                multirow_comment_flag = True
                results.append(False)
                continue
            elif line in ["*/", "-->"] or any(line.endswith(_) for _ in {"*/", "-->"}):
                multirow_comment_flag = False
                results.append(False)
                continue
            elif multirow_comment_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line):
                results.append(False)
            elif (
                "<span " in line
                or "<<link " in line
                or not line.startswith("<")
                or '<<set _bedType to "' in line
                or "<<print $_plant.plural.toLocaleUpperFirst()>>" in line
                or self.is_widget_print(line)
                or self.is_widget_set_to(line, {r"\$tendingvars\.harvest_name"})
            ):
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_system_text(self):
        """麻烦"""
        results = []
        multirow_comment_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释，逆天"""
            if line in ["/*", "<!--"] or (any(line.startswith(_) for _ in {"/*", "<!--"}) and all(_ not in line for _ in {"*/", "-->"})):
                multirow_comment_flag = True
                results.append(False)
                continue
            elif line in ["*/", "-->"] or any(line.endswith(_) for _ in {"*/", "-->"}):
                multirow_comment_flag = False
                results.append(False)
                continue
            elif multirow_comment_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line):
                results.append(False)
            elif (
                line.startswith('"')
                or "<span " in line
                or self.is_widget_print(line)
                or self.is_widget_set_to(line, {
                    "_text_output", r"\$_text_output", "_actionText",
                    r"\$description", r"\$_chest", r"\$_pool",
                    "_bottoms", "_parts", r"_tops\.push", r"_bottoms\.push",
                    r"\$_men", r"\$_women"
                })
                or "<<set _args[0]" in line
                or '<<if $_npc.penisdesc' in line
            ):
                results.append(True)
            elif any(_ == line for _ in {
                "$worn.over_upper.name\\",
                "$worn.over_lower.name\\",
                "$worn.upper.name\\",
                "$worn.lower.name\\",
                "$worn.under_lower.name\\",
                "$worn.genitals.name"
            }):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_time(self):
        """只有<span"""
        return self.parse_type_only("<span ")

    def _parse_tips(self):
        """只有<h3>和 " """
        return self.parse_type_startwith({'"', "<h3>"})

    def _parse_transformations(self):
        """<span, <<print, 纯文本"""
        return [
            line.strip() and (
                "<span " in line.strip()
                or "<<print " in line.strip()
                or (
                    "::" not in line.strip()
                    and not line.strip().startswith("<")
                    and not line.strip().startswith("}")
                    and not line.strip().startswith("/*")
                    and not self.is_json_line(line.strip())
                )
            ) for line in self._lines
        ]

    def _parse_system_widgets(self):
        results = []
        multirow_comment_flag = False
        multirow_error_flag = False
        multirow_script_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释，逆天"""
            if (line in ["/*", "<!--"] or (any(line.startswith(_) for _ in {"/*", "<!--"}) and all(_ not in line for _ in {"*/", "-->"}))):
                multirow_comment_flag = True
                results.append(False)
                continue
            elif multirow_comment_flag and (line in ["*/", "-->"] or any(line.endswith(_) for _ in {"*/", "-->"})):
                multirow_comment_flag = False
                results.append(False)
                continue
            elif multirow_comment_flag:
                results.append(False)
                continue

            """跨行script，逆天"""
            if line == "<<script>>":
                multirow_script_flag = True
                results.append(False)
                continue
            elif multirow_script_flag and line == "<</script>>":
                multirow_script_flag = False
                results.append(False)
                continue
            elif multirow_script_flag:
                if 'name : "' in line or 'name: "' in line:
                    results.append(True)
                    continue
                results.append(False)
                continue

            if line.startswith("<<error {"):
                multirow_error_flag = True
                results.append(False)
                continue
            elif multirow_error_flag and line == "}>>":
                multirow_error_flag = False
                results.append(False)
                continue
            elif multirow_error_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif (
                self.is_tag_span(line)
                or self.is_tag_label(line)
                or self.is_widget_print(line)
                or self.is_widget_set_to(line, {
                    r"\$_text_output", "_colour", r"\$_fringe",
                    "_out", "_part", "_bug", r"\$_crDescStr",
                    r"\$_crimes_output"
                })
                or "<<print either(" in line and ">>" in line
                or 'name: "' in line or 'name : "' in line
                or ">>." in line
                or self.is_widget_link(line)
            ):
                results.append(True)
            elif "<" in line and self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_persistent_npcs(self):
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if self.is_widget_set_to(line, {
                "_brdes", r"\$per_npc\[\$_i\]\.breastdesc", r"\$per_npc\[\$_i\]\.penisdesc",
                r"\$per_npc\[\$_i\]\.breastsdesc", "_out"
            }):
                results.append(True)
            else:
                results.append(False)
        return results

    """ flavour-text-generators """
    def parse_flavour_text(self):
        """ flavour-text-generators """
        if FileNamesTwee.BODY_COMMENTS_FULL.value == self._filename:
            return self._parse_body_comments()
        elif FileNamesTwee.EXHIBITIONISM_FULL.value == self._filename:
            return self._parse_exhibitionism()
        elif FileNamesTwee.EZ_THESAURUS_FULL.value == self._filename:
            return self._parse_thesaurus()
        return self.parse_normal()

    def _parse_body_comments(self):
        """json"""
        results = []
        json_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)

            if "<<set " in line and line.endswith("["):
                json_flag = True
                results.append(False)
            elif json_flag and "]>>" in line:
                json_flag = False
                results.append(False)
            elif json_flag or "<<Penisremarkquote>>" in line:
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_exhibitionism(self):
        """json"""
        results = []
        needed_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释/script，逆天"""
            if line == "<<set _seatedflashcrotchunderskirtlines to [":
                needed_flag = True
                results.append(False)
                continue
            elif line in "]>>":
                needed_flag = False
                results.append(False)
                continue
            elif needed_flag:
                results.append(True)
                continue

            if self.is_widget_set_to(line, {"_output_line"}):
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_thesaurus(self):
        """json"""
        return self.parse_type_between(["<<set _possibilities to ["], ["]>>"])

    """ 其它 """
    def parse_normal(self):
        return self._parse_normal()

    def _parse_normal(self):
        results = []
        multirow_comment_flag = False
        multirow_script_flag = False
        multirow_run_flag = False
        multirow_if_flag = False
        multirow_error_flag = False
        maybe_json_flag = False
        multirow_run_line_pool_flag = False  # 草!
        multirow_print_flag = False  # 叠屎山了开始

        # 这两个是家具的
        multirow_wallpaper_flag = False
        multirow_poster_flag = False

        shop_clothes_hint_flag = False  # 草
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释，逆天"""
            if (line in ["/*", "<!--"] or (any(line.startswith(_) for _ in {"/*", "<!--"}) and all(_ not in line for _ in {"*/", "-->"}))):
                multirow_comment_flag = True
                results.append(False)
                continue
            elif multirow_comment_flag and (line in ["*/", "-->"] or any(line.endswith(_) for _ in {"*/", "-->"})):
                multirow_comment_flag = False
                results.append(False)
                continue
            elif multirow_comment_flag:
                results.append(False)
                continue

            """还有跨行print"""
            if line.endswith("<<print either("):
                multirow_print_flag = True
                results.append(False)
                continue
            elif multirow_print_flag and (line.startswith(")>>") or line.endswith(')>></span>"')):
                if line != ")>>":
                    results.append(True)
                else:
                    results.append(False)
                multirow_print_flag = False
                continue
            elif multirow_print_flag:
                results.append(True)
                continue

            """跨行script，逆天"""
            if line == "<<script>>":
                multirow_script_flag = True
                results.append(False)
                continue
            elif multirow_script_flag and line == "<</script>>":
                multirow_script_flag = False
                results.append(False)
                continue
            elif multirow_script_flag:
                results.append(False)
                continue

            """跨行if，逆天"""
            if line.startswith("<<if ") and ">>" not in line:
                multirow_if_flag = True
                results.append(False)
                continue
            elif multirow_if_flag and ">>" in line:
                multirow_if_flag = False
                results.append(False)
                continue
            elif multirow_if_flag:
                results.append(False)
                continue

            """跨行error，逆天"""
            if line.startswith("<<error ") and ">>" not in line:
                multirow_error_flag = True
                results.append(False)
                continue
            elif multirow_error_flag and ">>" in line:
                multirow_error_flag = False
                results.append(False)
                continue
            elif multirow_error_flag:
                results.append(False)
                continue

            """就这个特殊"""
            if line == "<<set _specialClothesHint to {":
                shop_clothes_hint_flag = True
                results.append(False)
                continue
            elif shop_clothes_hint_flag and line == "}>>":
                shop_clothes_hint_flag = False
                results.append(False)
                continue
            elif shop_clothes_hint_flag:
                results.append(True)
                continue

            """突如其来的json"""
            if ((line.startswith("<<set ") or line.startswith("<<error {")) and ">>" not in line) or line.endswith("[") or line.endswith("{") or line.endswith("("):
                maybe_json_flag = True
                if any(_ in line for _ in {
                    "<<set _hairColorByName",
                    "<<set _fringeColorByName"
                }):
                    results.append(True)
                    continue
                results.append(False)
                continue
            elif maybe_json_flag and line.endswith(">>") and self.is_only_marks(line):
                maybe_json_flag = False
                results.append(False)
                continue
            elif maybe_json_flag and (
                '"Orphan":"orphan"' in line or "hint:`" in line
                or 'museum:"' in line or 'journal: `' in line
                or 'name:"' in line or 'stolen:"' in line
                or 'recovered:"' in line or '"Rest":' in line
                or '"Stroke":' in line or '"Vines"' in line
                or '"Tentacles"' in line or '"Plainwhite"' in line
                or '"Wavywhite"' in line or '"Cowgirls"' in line
                or '"Hearts"' in line or '"Trees"' in line
                or '"Crosses"' in line or '"Cowgirl"' in line
                or '"Cat"' in line or '"Puppy"' in line
                or "'Owl plushie'" in line
                or '"Loose"' in line
                or '"Messy"' in line
                or '"Pigtails"' in line
                or '"Ponytail"' in line
                or '"Short"' in line
                or '"Straight"' in line
                or '"Twintails"' in line
                or '"Curl"' in line
                or '"Neat"' in line
                or '"Dreads"' in line
                or '"Ruffled"' in line
                or '"Shaved"' in line
                or '"Sidecut"' in line
                or '":"' in line
                or '": "' in line
                or '" : "' in line
            ):
                results.append(True)
                continue

            """还有这个"""
            if line.startswith("<<run $(`#${_id}") and ('"Take" : ' in line or '"Present" : ' in line):
                results.append(True)
                continue

            """以及这个"""
            if line.startswith("<<run _linePool"):
                if line.endswith(">>"):
                    results.append(True)
                else:
                    multirow_run_line_pool_flag = True
                    results.append(False)
                continue
            elif multirow_run_line_pool_flag and line.endswith(")>>"):
                multirow_run_line_pool_flag = False
                results.append(False)
                continue
            elif multirow_run_line_pool_flag:
                results.append(True)
                continue

            """跨行run，逆天"""
            if line.startswith("<<run ") and ">>" not in line:
                multirow_run_flag = True
                results.append(False)
                continue
            elif multirow_run_flag and line in {"})>>", "}>>", ")>>", "]>>", "});>>"}:
                multirow_run_flag = False
                results.append(False)
                continue
            elif multirow_run_flag and (
                "Enable indexedDB" in line
            ):
                multirow_run_flag = False
                results.append(True)
                continue
            elif multirow_run_flag and (
                "'Owl plushie'" in line
            ):
                results.append(True)
                continue
            elif multirow_run_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
                continue
            elif (
                "<" in line and (
                    self.is_tag_span(line)
                    or self.is_tag_label(line)
                    or self.is_tag_input(line)
                    or self.is_widget_note(line)
                    or self.is_widget_print(line)
                    or self.is_widget_option(line)
                    or self.is_widget_button(line)
                    or self.is_widget_link(line)
                    or ("<<set " in line and self.is_widget_set_to(line, {
                        r"\$_strings", r"\$_text_output", "_text_output", r"_container\.name",
                        r"\$_customertype", r"\$_theboy", "_clothesDesc", r"_container\.feederName",
                        "_actionText", r"\$_marked_text", r"\$_plural", r"\$NPCList\[0\]\.penisdesc",
                        r"\$_link_text", "_has_feelings_towards", "_causing_a_consequence", r"\$outbuildingBeast",
                        "_hilarity_ensues", "_linkText", r"\$_theshop", "_coffee", "_tempText", "_wornname",
                        "_wraithTitle", "_speaks", r"\$wraithOptions", "_speechWraith", "_flaunt",
                        "_dives_into", r"\$NPCList\[_n\]\.hair", "_pregnancyLink", r"_container\.decorations",
                        "_postOrgasmSpeech", r"_names\.push", r"_pre\.push", "_shopmusic", "_offeredclothing",
                        "_bodyWritingOptions", "_reactTone", "_reactPerson", "_shopnameshort",
                        "_clothesTrait", "_petname", "_leftaction", "_rightaction", "_littlething",
                        "_bigthing", "_feetaction", "_penisaction", "_mouthaction", "_chestaction",
                        "_anusaction", "_vaginaaction", r"\$_mirror", r"\$_examines", r"\$_reacts",
                        "_playPronoun", r"\$pubtask", "_elite", "_subject", r"_title\d", "_chest",
                        "_target", "_shopgreeting", "_predicament", "_gagname", "_shopnamelong", "_seen_cards_index_strings",
                        "_sydneysays", "_leftHand", "_rightHand", "_mouth", "_feet", "_askActions",
                        "_penis", "_vagina", "_anus", r"\$stallThiefPartner", r"\$NPCList\[_n\]\.fullDescription",
                        "_reactSpeech", "_looks", "_fucking", r"\$_eagerly", r"\$_npcpart", r"_npc\d",
                        "_colour", "_hairOptions", "_fringeOptions", "_dyeOptions", "_browsDyeOptions",
                        r"\$_rhythmically", r"\$_wet", "_lubricated", "_afinger", "_anotherfinger", r"\$_toy",
                        "_nectar", "_Nectar", r"\$_NPCBreastDesc", r"\$_buttplug", "_npc0", "_genitals", r"\$_sexToy",
                        "_impregnator", "_toyName", "_crowd", r"\$vorecreature", "_toy", "_sextoy", "_reactTitle",
                        r"\$_topic", "_pubfameOptions", r"\$boughtfurniturename", "_exposing", "_revealed_thing",
                        r"_tentacle\.desc", r"_tentacle\.fullDesc", r"\$_breed", "_sydneyText", "_featsTattooOptions",
                        "_penOptions", "_bodyPartOptions", "_output", "_speakPool", "_colorOptions", r"\$_clothing",
                        "_hairNames", "_fringeNames", "_dyeNames", "_secondaryColorOptions", "_liq", "_yourclit",
                        r"\$NPCList\[0\]\.fullDescription", "_kylarUnderLower", "_pants", r"_kylarUndies\.desc",
                        r"_kylarUndies\.colourDesc", r"\$audiencedesc", r"\$_alongsidearray", r"\$_linkName",
                        "_clothesColorOptions", "_clothes", "_fringeTypeByName", "_fringeLengthByName", "_fringeColorByName",
                        "_hairColorByName", "_name", "_fizzyNectar", r"\$_type", r"\$_babiesText", r"\$arcadeExposure",
                        "_them", "_hooks", "_lewdOrDeviant", r"\$_boundType", r"_stripOptions\[\$worn", r"\$schoolpoolundress",
                        r"\$_removed\.pushUnique", r"\$_broken\.pushUnique", r"\$_randomitem", r"\$hawk_loot",
                        r"\$_liquids\.push", "_plural_beast_type", r"\$temple_wall_victim", "_playerRole", r"\$_quiet",
                        "_dealer_distracted_text", r"\$removedItem", "_whitneyLower", r"_creatureTip\[_i\]\.pushUnique",
                        r"_luxuryTip\.pushUnique", "_tool", "_fluid", "_he", "_He", "_him", "_His", "_his", "_exercise",
                        "_pronoun", "_pronoun2", "_own", r"\$_balls", "_loc_text", "_writing", r"\$alex_parent", r"\$_parasiteMessage",
                        "_tmpsmoving", "_gender_body_words", "_bodysize_words", "_output_line", r"\$island\[\$island\.home\]\.decoration",
                        "_cumDesc", r"_pregnantNPC\[_pregEnabled\.nam\]", "_displayName"
                    }))
                )
            ):
                if '.replaceAll("["' in line or '.replace(/\[/g' in line:
                    results.append(False)
                    continue
                results.append(True)
                continue
            elif (
                '<<if $tentacles[$tentacleindex].desc.includes("pale")>>' in line
                or "<<if $_mirror is 'mirror'>>" in line
                or '<<run _bodyPartOptions.delete($featsBoosts.tattoos[_l].bodypart)>>' in line
                or '$_examine' in line
                or '<<if $pubtask is' in line
                or '<<run _featsTattooOptions.push(' in line
                or '<<if $NPCList[_nn].penis' in line
                or '<<if $watersportsdisable is "f" and $consensual is 0 and $enemyanger gte random(20, 200) and ($NPCList[_nn].penis is "none" or !$NPCList[_nn].penisdesc.includes("strap-on")) and _condomResult isnot "contained" and _args[0] isnot "short">>' in line
                or '<<if $NPCList[0].penisdesc' in line
                or '<<if $NPCList[_n].condom' in line
                or '<<takeKissVirginityNamed' in line
                or "<<cheatBodyliquidOnPart" in line
                or "<<generateRole" in line
                or "<<takeVirginity" in line
                or "<<recordSperm " in line
                or "<<NPCVirginityTakenByOther" in line
                or "<<run $rebuy_" in line
                or "<<swarminit" in line
                or "<<set _buy = Time.dayState" in line
                or "<<optionsfrom " in line
                or "<<run _options" in line
                or "<<listbox " in line
                or "<<run _potentialLoveInterests.delete" in line
                or "<<run _selectedToy.colour_options.forEach" in line
                or "$worn.upper.name." in line
                or "$worn.lower.name." in line
                or "$worn.over_upper.name." in line
                or "$worn.under_upper.name." in line
                or "<<girlfriend>>?" in line
                or "$_slaps" in line
                or '? "' in line
                or "<<gagged_speech" in line
                or "<<mirror" in line
                or ">>." in line
                or "<<skill_difficulty " in line
            ):
                results.append(True)
            elif (
                ("<" in line and self.is_only_widgets(line))
                or (maybe_json_flag and self.is_json_line(line))
            ):
                results.append(False)
                continue
            else:
                results.append(True)
        return results

    """ 归整 """
    def parse_type_only(self, pattern: str | set[str]) -> list[bool]:
        """指文件中只有一种或几种简单字符格式需要提取"""
        if isinstance(pattern, str):
            return [
                line.strip() and
                pattern in line.strip()
                for line in self._lines
            ]

        return [
            line.strip() and
            any((_ in line.strip() for _ in pattern))
            for line in self._lines
        ]

    def parse_type_only_regex(self, pattern: str | set[str]) -> list[bool]:
        """指文件中只有一种或几种正则格式需要提取"""
        if isinstance(pattern, str):
            return [
                line.strip() and
                any(re.findall(pattern, line.strip()))
                for line in self._lines
            ]

        return [
            line.strip() and
            any(re.findall(_, line.strip()) for _ in pattern)
            for line in self._lines
        ]

    def parse_type_startwith(self, pattern: str | set[str]) -> list[bool]:
        """以xx开头的"""
        if isinstance(pattern, str):
            return [
                line.strip() and
                line.strip().startswith(pattern)
                for line in self._lines
            ]

        return [
            line.strip() and
            any((line.strip().startswith(_) for _ in pattern))
            for line in self._lines
        ]

    def parse_type_pure_text(self) -> list[bool]:
        """指文件中只有纯文本需要提取"""
        return [
            line.strip() and
            not line.strip().startswith("<") and "::" not in line.strip()
            for line in self._lines
        ]

    def parse_type_between(self, starts: list[str], ends: list[str], contain: bool = False) -> list[bool]:
        """指文件中只有这两部分之间的内容需要提取"""
        results = []
        needed_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释/script，逆天"""
            if line in starts:
                needed_flag = True
                results.append(contain)
            elif line in ends:
                needed_flag = False
                results.append(contain)
            elif needed_flag:
                results.append(True)
            else:
                results.append(False)
        return results

    """ 判断 """
    @staticmethod
    def is_comment(line: str) -> bool:
        """注释"""
        if line.startswith("*") or line.startswith("*/") or line.startswith("-->"):
            return True
        return any(line.startswith(_) for _ in {"/*", "<!--"}) and any(line.endswith(_) for _ in {"*/", "-->"})

    @staticmethod
    def is_json_line(line: str) -> bool:
        """ xxx: yyy """
        return any(re.findall(r"^[\w\"]*\s*:\s*[ `\'/\$\.\w\":,\|\(\)\{\}\[\]]+,*$", line))

    @staticmethod
    def is_only_marks(line: str) -> bool:
        """只有符号没字母数字"""
        return not any(re.findall(r"([A-Za-z\d]+)", line))

    @staticmethod
    def is_event(line: str) -> bool:
        """事件"""
        return "::" in line

    @staticmethod
    def is_tag_span(line: str) -> bool:
        """<span???>xxx"""
        return any(re.findall(r'<span.*?>[\"\w\.\-+\$]', line))

    @staticmethod
    def is_tag_label(line: str) -> bool:
        """<label>xxx</label>"""
        return any(re.findall(r"<label>[\w\-+]", line)) or any(re.findall(r"\w</label>", line))

    @staticmethod
    def is_tag_input(line: str) -> bool:
        """<input """
        return any(re.findall(r"<input.*?value=\"", line))

    @staticmethod
    def is_widget_script(line: str) -> bool:
        """<<script """
        return any(re.findall(r"<<script", line))

    @staticmethod
    def is_widget_note(line: str) -> bool:
        """<note """
        return any(re.findall(r"<<note\s\"", line))

    @staticmethod
    def is_widget_set_to(line: str, keys: set[str]) -> bool:
        """<<set xxx yyy>>"""
        pattern = re.compile("<<set\s(?:" + r"|".join(keys) + ")[\'\"\w\s\[\]\$\+\.\(\)\{\}:\-\&£]*(?:to|\+|\+=|\(|\=).*?[\[\w\{\"\'`]+(?:\w| \w|<<|\"\w| |]|\.|,)")
        return any(re.findall(pattern, line))

    @staticmethod
    def is_widget_print(line: str) -> bool:
        """<<print xxx>>"""
        return any(re.findall(r"<<print\s[^<]*[\"\'`\w]+[\-\?\s\w\.\$,\'\"<>\[\]\(\)/]+(?:\)>>|\">>|\'>>|`>>|\]>>|>>)", line))

    @staticmethod
    def is_widget_if(line: str) -> bool:
        """<<if>>xxx</if>"""
        return any(re.findall(r"<<if\s.*?>>\w", line))

    @staticmethod
    def is_widget_option(line: str) -> bool:
        """<<option """
        return any(re.findall(r"<<option\s\"", line))

    @staticmethod
    def is_widget_button(line: str) -> bool:
        """<<option """
        return any(re.findall(r"<<button ", line))

    @staticmethod
    def is_widget_link(line: str) -> bool:
        """<<link [[xxx|yyy]]>>, <<link "xxx">> """
        return any(re.findall(r"<<link\s*(\[\[|\"\w|`\w|\'\w|\"\(|`\(|\'\(|_\w|`)", line))

    @staticmethod
    def is_widget_high_rate_link(line: str) -> bool:
        """高频选项"""
        return any(re.findall(r"<<link \[\[(Next\||Next\s\||Leave\||Refuse\||Return\||Resume\||Confirm\||Continue\||Stop\||Phase\|)", line))

    @staticmethod
    def is_widget_actions_tentacle(line: str) -> bool:
        """逆天"""
        return "<<actionstentacleadvcheckbox" in line

    @staticmethod
    def is_only_widgets(line: str) -> bool:
        """整行只有 <<>>, <>, $VAR"""
        if "<" not in line and "$" not in line and not line.startswith("_"):
            return False

        """特殊的半拉"""
        if line in {"<<print either(", "<<print ["}:
            return True

        widgets = {_ for _ in re.findall(r"(<<(?:[^<>]*?|run.*?|for.*?)>>)", line) if _}
        for w in widgets:
            # if "[[" not in w or ("[" in w and '"' not in w and "'" not in w and "`" not in w):
            line = line.replace(w, "", -1)

        if "<" not in line and "$" not in line and not line.startswith("_"):
            return (not line.strip()) or ParseTextTwee.is_comment(line.strip()) or ParseTextTwee.is_only_marks(line.strip()) or False
        tags = {_ for _ in re.findall(r"(<[/\s\w\"=\-@\$\+\'\.]*>)", line) if _}
        for t in tags:
            line = line.replace(t, "", -1)

        if "$" not in line and not line.startswith("_"):
            return (not line.strip()) or ParseTextTwee.is_comment(line.strip()) or ParseTextTwee.is_only_marks(line.strip()) or False

        vars_ = {_ for _ in re.findall(r"((?:\$|_)[^_][#;\w\.\(\)\[\]\"\'`]*)", line) if _}
        for v in vars_:
            line = line.replace(v, "", -1)
        return (not line.strip()) or ParseTextTwee.is_comment(line.strip()) or ParseTextTwee.is_only_marks(line.strip()) or False


class ParseTextJS:

    def __init__(self, lines: list[str], filepath: Path):
        self._lines = lines
        self._filepath = filepath

        self._filename = self._filepath.name  # 文件名
        self._filedir = self._filepath.parent  # 文件夹

    def parse(self) -> list[bool]:
        """"""
        if DirNamesJS.JAVASCRIPT.value == self._filedir.name:
            return self.parse_javascript()
        elif DirNamesJS.VARIABLES.value == self._filedir.name:
            return self.parse_variables()
        elif DirNamesJS.SPECIAL_MASTURBATION.value == self._filedir.name:
            return self.parse_masturbation()
        elif DirNamesJS.PREGNANCY.value == self._filedir.name:
            return self.parse_pregnancy()
        elif DirNamesJS.TIME.value == self._filedir.name:
            return self.parse_time()
        elif DirNamesJS.TEMPLATES.value == self._filedir.name:
            return self.parse_templates()
        elif DirNamesJS.EXTERNAL.value == self._filedir.name:
            return self.parse_external()
        elif DirNamesJS.BASE_CLOTHING.value == self._filedir.name:
            return self.parse_clothing()
        elif DirNamesJS.BASE_SYSTEM.value == self._filedir.name:
            return self.parse_system()
        return self.parse_normal()

    """ 03-JavaScript """
    def parse_javascript(self) -> list[bool]:
        """ 03-JavaScript """
        if FileNamesJS.BEDROOM_PILLS_FULL.value == self._filename:
            return self._parse_bedroom_pills()
        elif FileNamesJS.BASE_FULL.value == self._filename:
            return self._parse_base()
        elif FileNamesJS.DEBUG_MENU_FULL.value == self._filename:
            return self._parse_debug_menu()
        elif FileNamesJS.FURNITURE_FULL.value == self._filename:
            return self._parse_furniture()
        elif FileNamesJS.EYES_RELATED.value == self._filename:
            return self._parse_eyes_related()
        elif FileNamesJS.SEXSHOP_MENU_FULL.value == self._filename:
            return self._parse_sexshop_menu()
        elif FileNamesJS.SEXTOY_INVENTORY_FULL.value == self._filename:
            return self._parse_sextoy_inventory()
        elif FileNamesJS.IDB_BACKEND_FULL.value == self._filename:
            return self._parse_idb_backend()
        elif FileNamesJS.INGAME_FULL.value == self._filename:
            return self._parse_ingame()
        elif FileNamesJS.UI_FULL.value == self._filename:
            return self._parse_ui()
        elif FileNamesJS.NPC_COMPRESSOR_FULL.value == self._filename:
            return self._parse_npc_compressor()
        elif FileNamesJS.COLOUR_NAMER_FULL.value == self._filename:
            return self._parse_colour_namer()
        elif FileNamesJS.CLOTHING_SHOP_V2_FULL.value == self._filename:
            return self._parse_clothing_shop_v2()
        return self.parse_normal()

    def _parse_bedroom_pills(self):
        """..."""
        results = []
        next_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if any(_ in line for _ in {
                "name:", "description:", "onTakeMessage:", "warning_label:"
            }) and not line.startswith("*"):
                if line.endswith(":"):
                    next_flag = True
                    results.append(False)
                else:
                    results.append(True)
                continue
            elif next_flag:
                next_flag = False
                results.append(True)
                continue

            if (any(_ in line for _ in {
                '<span class="hpi_auto_label">',
                'class="hpi_take_pills"',
                "item.autoTake() ?",
                "item.hpi_take_pills ?",
                "</a>",
                '"Effective for "',
                'return "',
                "return this.autoTake()",
                "const itemName"
            })):
                results.append(True)
            else:
                results.append(False)

        return results

    def _parse_base(self):
        """ T.text_output """
        results = []
        for idx, line in enumerate(self._lines):
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if any(_ in line for _ in {
                'T.text_output = "cracked ";',
                'T.text_output = "scratched ";',
                'T.text_output = alt === "metal" ? "tarnished " : "discoloured ";',
                'T.text_output = kw + " ";',
                'T.text_output = worn.colour'
            }):
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_debug_menu(self):
        """..."""
        results = []
        inner_html_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if 'document.getElementById("debugEventsAdd").innerHTML' in line:
                inner_html_flag = True
                results.append(False)
                continue
            elif inner_html_flag and line == "`;":
                inner_html_flag = False
                results.append(False)
                continue
            elif inner_html_flag:
                if any(_ in line for _ in {
                    "<abbr>", "<span>", "<option", "<button",
                    "<h3>", "<<swarminit"
                }):
                    results.append(True)
                    continue
                results.append(False)
                continue

            if any(_ in line for _ in {"link: [`", 'link: ["', "link: [(", "text_only: "}):
                results.append(True)
            else:
                results.append(False)

        return results

    def _parse_eyes_related(self):
        """怪东西"""
        return self.parse_type_only({'sentence += ', '"."'})

    def _parse_furniture(self):
        """json"""
        return self.parse_type_only({"nameCap: ", "description: "})

    def _parse_sexshop_menu(self):
        """json"""
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if any(_ in line for _ in {
                "namecap: ", "description: ", "${item.owned()",
                "<span "
            }) or ("Buy it" in line and "/*" not in line) or "Make a gift for :" in line:
                results.append(True)
            else:
                results.append(False)

        return results

    def _parse_sextoy_inventory(self):
        """零碎东西"""
        results = []
        a_flag = False
        cursed_flag = False
        carry_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if "<a id=" in line:
                a_flag = True
                results.append(False)
                continue
            elif a_flag and line == "</a>":
                a_flag = False
                results.append(False)
                continue
            elif a_flag:
                results.append(True)
                continue

            if line == 'document.getElementById("stiCursedText").outerHTML =':
                cursed_flag = True
                results.append(False)
                continue
            elif cursed_flag and line == "return;":
                cursed_flag = False
                results.append(False)
                continue
            elif cursed_flag:
                results.append(True)
                continue

            if 'document.getElementById("carryCount")' in line:
                carry_flag = False
                results.append(False)
                continue
            elif carry_flag and line == "</div>`;":
                carry_flag = False
                results.append(False)
                continue
            elif carry_flag:
                results.append(True)
                continue

            if (
                ".textContent" in line
                or "(elem !== null)" in line
                or "invItem.worn" in line
                or "<span class=" in line
                or "const itemStatus" in line
            ):
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_idb_backend(self):
        """lastChild.innerText"""
        results = []
        inner_text_flag = False
        inner_html_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if "lastChild.innerText" in line and not line.endswith(";"):
                inner_text_flag = True
                results.append(False)
                continue
            elif inner_text_flag and line.endswith(';'):
                inner_text_flag = False
                results.append(True)
                continue

            if "innerHTML" in line and not line.endswith(";"):
                inner_text_flag = True
                results.append(False)
                continue
            elif inner_text_flag and line.endswith(';'):
                inner_text_flag = False
                results.append(True)
                continue

            if (
                "lastChild.innerText" in line
                or ('value: "' in line and "<" not in line and ">" not in line)
                or '"<div class=saveGroup>' in line
                or '.append("' in line
                or '", Date: " +' in line
                or '"Save Name: "' in line
                or 'saveButton.value' in line
                or 'loadButton.value' in line
                or 'lostSaves.innerHTML =' in line
            ):
                results.append(True)
            else:
                results.append(False)

        return results

    def _parse_ingame(self):
        """序数词词缀"""
        return self.parse_type_only({
            'return i + "st";', 'return i + "nd";',
            'return i + "rd";', 'return i + "th";'
        })

    def _parse_ui(self):
        """text"""
        results = []
        text_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if line == "text =":
                text_flag = True
                results.append(False)
            elif text_flag and line == "break;":
                text_flag = False
                results.append(False)
            elif text_flag and not self.is_only_marks(line):
                results.append(True)

            elif "text =" in line and "let text" not in line and "const text" not in line:
                results.append(True)
            elif "<span" in line:
                results.append(True)
            elif (
                "npc.breastdesc =" in line
                or "npc.breastsdesc =" in line
                or "const breastSizes =" in line
                or 'women = "' in line
                or 'men = ' in line
            ):
                results.append(True)
            elif "<span" in line:
                results.append(True)
            else:
                results.append(False)

        return results

    def _parse_npc_compressor(self):
        results = []
        multiconst_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if "DescList" in line or "descList" in line and not line.endswith(";"):
                multiconst_flag = True
                results.append(False)
                continue
            elif multiconst_flag and line.endswith(";"):
                multiconst_flag = False
                if "fullDescription =" in line:
                    results.append(True)
                    continue
                results.append(False)
                continue
            elif multiconst_flag and (line.endswith('",') or line.endswith('"')):
                results.append(True)
                continue
            elif multiconst_flag:
                results.append(False)
                continue

            if (
                "const breastdesc" in line
                or "const breastsdesc" in line
                or ("descList" in line and "]" in line)
                or ("DescList" in line and "]" in line)
                or "const plant =" in line
                or "const man =" in line
                or "const sizeList" in line
            ):
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_colour_namer(self):
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if (
                'return "' in line
                or 'main = "' in line
                or 'main === "' in line
                or 'colour = "' in line
                or "`rgb" in line
                or "aux = " in line
                or "= aux" in line
            ):
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_clothing_shop_v2(self):
        return self.parse_type_only({
            "const optionsFrom",
            "const optionsTo"
        })

    """ 04-variables """
    def parse_variables(self) -> list[bool]:
        """ 04-variables """
        if FileNamesJS.FEATS_FULL.value == self._filename:
            return self._parse_feats()
        elif FileNamesJS.COLOURS_FULL.value == self._filename:
            return self._parse_colours()
        return self.parse_normal()

    def _parse_feats(self):
        """json"""
        return self.parse_type_only({"title: ", "desc: ", "hint: "})

    def _parse_colours(self):
        """json"""
        return self.parse_type_only({'name_cap: "', 'name: "'})

    """ special-masturbation """
    def parse_masturbation(self) -> list[bool]:
        """ special-masturbation """
        if FileNamesJS.ACTIONS_FULL.value == self._filename:
            return self._parse_actions()
        elif FileNamesJS.EFFECTS_FULL.value == self._filename:
            return self._parse_effects()
        elif FileNamesJS.MACROS_MASTURBATION_FULL.value == self._filename:
            return self._parse_macros_masturbation()
        return self.parse_normal()

    def _parse_actions(self):
        """result.text"""
        results = []
        maybe_json_flag = False
        multirow_text_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if line.startswith("result.text") and line.endswith("{") or line.endswith("="):
                multirow_text_flag = True
                results.append(True)
                continue
            elif multirow_text_flag and line.endswith("`;"):
                multirow_text_flag = False
                results.append(True)
                continue
            elif multirow_text_flag:
                results.append(True)
                continue

            if line.endswith("{"):
                maybe_json_flag = True
                results.append(False)
                continue
            elif maybe_json_flag and any(line.endswith(_) for _ in {"};", ")};"}):
                maybe_json_flag = False
                results.append(False)
                continue
            elif maybe_json_flag and self.is_json_line(line) and "text:" in line:
                results.append(True)
                continue

            if any(_ in line for _ in {
                "result.text", "text:", "result.options.push", ".name;",
                '" : "',
            }):
                results.append(True)
            elif (
                line.startswith("? '")
                or line.startswith('? "')
                or line.startswith(': "')
                or line.startswith(": '")
            ):
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_effects(self):
        results = []
        append_fragment_flag = False
        multirow_swikifier_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if line == "fragment.append(":
                append_fragment_flag = True
                results.append(False)
                continue
            elif append_fragment_flag and line == ");":
                append_fragment_flag = False
                results.append(False)
                continue
            elif (
                append_fragment_flag
                and not self.is_only_marks(line)
                and line not in {
                    "Wikifier.wikifyEval(", "span(",
                    "altText.selectedToy", "altText.toys =",
                    "toy1.name"
                }
            ):
                results.append(True)
                continue

            if line.startswith("sWikifier(") and ")" not in line:
                multirow_swikifier_flag = True
                results.append(False)
                continue
            elif multirow_swikifier_flag and line.endswith(");"):
                multirow_swikifier_flag = False
                results.append(False)
                continue
            elif multirow_swikifier_flag:
                results.append(True)
                continue

            if "sWikifier" in line:
                results.append(True)
            elif "`You" in line:
                results.append(True)
            elif '"You' in line:
                results.append(True)
            elif "fragment.append(wikifier(" in line:
                results.append(True)
            elif "fragment.append(" in line and any(
                _ not in line
                for _ in {"''", "' '", '""', '" "', "``", "` `", "br()"}
            ):
                results.append(True)
            elif (
                "altText.toys = " in line
                or "altText.start = " in line
                or "<span class" in line
                or "toy1.name" in line
                or line.startswith('? "')
                or line.startswith(': "')
                or line.startswith("altText.")
                or "T.text_output" in line
                or "altText.lubricated" in line
                or '? " semen-lubricated"' in line
                or ")}. <<gpain>>`" in line
                or "}.</span>`" in line
                or '" : "' in line
            ):
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_macros_masturbation(self):
        return self.parse_type_only({"namecap", "name : name"})

    """ 04-pregnancy """
    def parse_pregnancy(self) -> list[bool]:
        """ 04-pregnancy """
        if FileNamesJS.CHILDREN_STORY_FUNCTIONS_FULL.value == self._filename:
            return self._parse_children_story_functions()
        elif FileNamesJS.PREGNANCY_FULL.value == self._filename:
            return self._parse_pregnancy()
        elif FileNamesJS.STORY_FUNCTIONS_FULL.value == self._filename:
            return self._parse_story_functions()
        elif FileNamesJS.PREGNANCY_TYPES_FULL.value == self._filename:
            return self._parse_pregnancy_types()
        return self.parse_normal()

    def _parse_children_story_functions(self):
        """就一个 wordList"""
        return self.parse_type_only({"const wordList", "wordList.push"})

    def _parse_pregnancy(self):
        return self.parse_type_only({
            "names = ['", "names.pushUnique", "spermOwner.name +", "spermOwner.fullDescription +"
        })

    def _parse_story_functions(self):
        return self.parse_type_only({
            "name = (caps ?", "name = caps ?", "name = name[0]"
        })

    def _parse_pregnancy_types(self):
        return self.parse_type_only({
            'return "tiny";',
            'return "small";',
            'return "normal";',
            'return "large";',
            'return ["tiny",'
        })

    """ time """
    def parse_time(self) -> list[bool]:
        """ time """
        if FileNamesJS.TIME_FULL.value == self._filename:
            return self._parse_time()
        elif FileNamesJS.TIME_MACROS_FULL.value == self._filename:
            return self._parse_time_macros()
        return self.parse_normal()

    def _parse_time(self):
        """只有月份和星期"""
        return self.parse_type_only({"const monthNames", "const daysOfWeek"})

    def _parse_time_macros(self):
        """只有几句话"""
        return self.parse_type_only({
            "School term finishes today.", "School term finishes on ", "School term starts on ",
            "ampm = hour"
        })

    """ 03-Templates """
    def parse_templates(self) -> list[bool]:
        if FileNamesJS.T_MISC_FULL.value == self._filename:
            return self._parse_t_misc()
        elif FileNamesJS.T_ACTIONS_FULL.value == self._filename:
            return self._parse_t_actions()
        elif FileNamesJS.T_BODYPARTS_FULL.value == self._filename:
            return self._parse_t_bodyparts()
        return self.parse_normal()

    def _parse_t_misc(self):
        """t-misc"""
        results = []
        print_either_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if line == "either(":
                print_either_flag = True
                results.append(False)
                continue
            elif print_either_flag and line == ")":
                print_either_flag = False
                results.append(False)
                continue
            elif print_either_flag:
                results.append(True)
                continue

            if 'Template.add("' in line and line.endswith(";"):
                results.append(True)
                continue
            else:
                results.append(False)
        return results

    def _parse_t_actions(self):
        """t-actions"""
        return self.parse_type_only("either(")

    def _parse_t_bodyparts(self):
        """t-actions"""
        return self.parse_type_only("either(")

    """ external """
    def parse_external(self) -> list[bool]:
        if FileNamesJS.COLOR_NAMER_FULL.value == self._filename:
            return self._parse_color_namer()
        return self.parse_normal()

    def _parse_color_namer(self):
        return self.parse_type_between(
            starts=["var colors = {"],
            ends=["}"]
        )

    """ base-clothing """
    def parse_clothing(self):
        if FileNamesJS.UDPATE_CLOTHES_FULL.value == self._filename:
            return self._parse_update_clothes()
        elif FileNamesJS.CLOTHING.value in self._filename:
            return self._parse_clothing()
        return self.parse_normal()

    def _parse_update_clothes(self):
        results = []
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if line.startswith("V") and ".name =" in line:
                results.append(True)
            elif "name: " in line:
                results.append(True)
            else:
                results.append(False)
        return results

    def _parse_clothing(self):
        """ 0.4.2.3 改动"""
        return self.parse_type_only({"name_cap:", "description:", "<<link `", "altDamage:"})

    """ base-system """
    def parse_system(self):
        if FileNamesJS.WIDGETS_FULL.value == self._filename:
            return self._parse_widgets()
        return self.parse_normal()

    def _parse_widgets(self):
        return self.parse_type_only({".name_cap,", "addfemininityfromfactor(", "playerAwareTheyArePregnant()"})

    """ 常规 """
    def parse_normal(self) -> list[bool]:
        """常规"""
        results = []
        append_fragment_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            if line == "fragment.append(":
                append_fragment_flag = True
                results.append(False)
            elif append_fragment_flag and line == ");":
                append_fragment_flag = False
                results.append(False)
            elif (
                append_fragment_flag
                and not self.is_only_marks(line)
                and line not in {
                    "Wikifier.wikifyEval(", "span(", "altText.selectedToy"
                }
            ):
                results.append(True)
            elif "fragment.append(" in line and any(
                _ not in line
                for _ in {"''", "' '", '""', '" "', "``", "` `", "br()"}
            ):
                results.append(True)
            elif ("addfemininityfromfactor(" in line and line.endswith(');')) or '"Pregnant Looking Belly"' in line:
                results.append(True)
            elif (
                "altText.toys = " in line
                or "altText.start = " in line
            ):
                results.append(True)
            else:
                results.append(False)

        return results

    """ 归整 """
    def parse_type_only(self, pattern: str | set[str]) -> list[bool]:
        """指文件中只有一种或几种简单字符格式需要提取"""
        if isinstance(pattern, str):
            return [
                line.strip() and
                pattern in line.strip()
                for line in self._lines
            ]

        return [
            line.strip() and
            any((_ in line.strip() for _ in pattern))
            for line in self._lines
        ]

    def parse_type_between(self, starts: list[str], ends: list[str], contain: bool = False) -> list[bool]:
        """指文件中只有这两部分之间的内容需要提取"""
        results = []
        needed_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释/script，逆天"""
            if line in starts:
                needed_flag = True
                results.append(contain)
            elif line in ends:
                needed_flag = False
                results.append(contain)
            elif needed_flag:
                results.append(True)
            else:
                results.append(False)
        return results

    @staticmethod
    def is_json_line(line: str) -> bool:
        """json"""
        return ParseTextTwee.is_json_line(line)

    @staticmethod
    def is_only_marks(line: str) -> bool:
        """只有符号"""
        return ParseTextTwee.is_only_marks(line)

    @staticmethod
    def is_only_widgets(line: str) -> bool:
        return ParseTextTwee.is_only_widgets(line)


__all__ = [
    "ParseTextTwee",
    "ParseTextJS"
]
