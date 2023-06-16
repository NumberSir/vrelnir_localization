import re
from pathlib import Path
from typing import List, Union, Set

from .consts import DirNames, FileNames
from .log import logger


class ParseTextTwee:

    def __init__(self, lines: List[str], filepath: Path):
        self._lines = lines
        self._filepath = filepath

        self._filename = self._filepath.name  # 文件名
        self._filedir = self._filepath.parent  # 文件夹

    def parse(self) -> List[bool]:
        if DirNames.NORMAL.value in self._filedir.name:
            return self.parse_normal()
        elif DirNames.FRAMEWORK.value in {
            self._filedir.name,
            self._filedir.parent.name,
        }:
            return self.parse_framework()
        elif DirNames.CONFIG.value == self._filedir.name:
            return self.parse_config()
        elif DirNames.VARIABLES.value == self._filedir.name:
            return self.parse_variables()
        elif DirNames.BASE_CLOTHING.value == self._filedir.name:
            return self.parse_base_clothing()
        elif DirNames.BASE_COMBAT.value in {
            self._filedir.name,
            self._filedir.parent.name,
        }:
            return self.parse_base_combat()
        elif DirNames.BASE_DEBUG.value == self._filedir.name:
            return self.parse_base_debug()
        elif DirNames.BASE_SYSTEM.value in {
            self._filedir.name,
            self._filedir.parent.name,
        }:
            return self.parse_base_system()
        return self.parse_normal()

    """√ framework-tools """
    def parse_framework(self):
        """ 00-framework-tools"""
        if FileNames.WAITING_ROOM_FULL.value == self._filename:
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
        if FileNames.START_FULL.value == self._filename:
            return self._parse_start()
        elif FileNames.VERSION_INFO_FULL.value == self._filename:
            return self._parse_version_info()
        return self.parse_normal()

    def _parse_start(self):
        """很少很简单"""
        return [
            line.strip() and (
                "<span " in line.strip()
                or "<<link [[" in line.strip()
                or any(re.findall(r"^(\w|- S)", line.strip()))
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
        if FileNames.CANVASMODEL_FULL.value == self._filename:
            return self._parse_canvasmodel()
        elif FileNames.VERSION_UPDATE_FULL.value == self._filename:
            return self._parse_version_update()
        elif FileNames.PASSAGE_FOOTER_FULL.value == self._filename:
            return self._parse_passage_footer()
        return self.parse_normal()

    def _parse_canvasmodel(self):
        """只有一个<<link"""
        return self._parse_type_only("<<link [[")

    def _parse_version_update(self):
        """只有 <span 和 <<link """
        return self._parse_type_only({"<span ", "<<link "})

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

    """√ base-clothing """
    def parse_base_clothing(self):
        """ base-clothing """
        if FileNames.CAPTIONTEXT_FULL.value == self._filename:
            return self._parse_captiontext()
        elif FileNames.CLOTHING.value in self._filename and FileNames.CLOTHING_SETS_FULL.value != self._filename:
            return self._parse_clothing()
        elif FileNames.CLOTHING_SETS_FULL.value == self._filename:
            return self._parse_clothing_sets()
        elif FileNames.IMAGES_FULL.value in self._filename:
            return self._parse_clothing_images()
        elif FileNames.INIT_FULL.value in self._filename:
            return self._parse_clothing_init()
        elif FileNames.WARDROBES_FULL.value in self._filename:
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
                "_text_output", r"\$_pair", r"\$_a"
            }):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)

        return results

    def _parse_clothing(self):
        """json"""
        return self._parse_type_only({"name_cap:", "description:"})

    def _parse_clothing_sets(self):
        """好麻烦"""
        results = []
        multirow_widget_flag = False
        multirow_json_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释/script，逆天"""
            if (
                line in ["<<script>>", "<<error {"]
                or (
                    any(line.startswith(_) for _ in {"<<script>>", "<<error {", "<<set "})
                    and all(_ not in line for _ in {"<</script>>", "}>>"})
                )
            ):
                multirow_widget_flag = True
                results.append(False)
                continue
            elif line in ["<</script>>", "}>>"] or any(line.endswith(_) for _ in {"*/", "-->", "<</script>>", "}>>"}):
                multirow_widget_flag = False
                results.append(False)
                continue
            elif multirow_widget_flag:
                results.append(False)
                continue

            """就为这一个单开一档，逆天"""
            if line.startswith("<<run ") and "}>>" not in line:
                multirow_json_flag = True
                results.append(False)
            elif "}>>" in line:
                multirow_json_flag = False
                results.append(False)
            elif multirow_json_flag and any(_ in line for _ in {'"start"', '"joiner"', '"end"'}):
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif (
                self.is_tag_span(line)
                or self.is_tag_label(line)
                or self.is_widget_option(line)
                or self.is_widget_link(line)
            ):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_clothing_images(self):
        """只有 <span"""
        return self._parse_type_only("<span ")

    def _parse_clothing_init(self):
        """只有 desc:"""
        return self._parse_type_only("desc:")

    def _parse_wardrobes(self):
        """多了一个<<wearlink_norefresh " """
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

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif (
                self.is_tag_span(line)
                or self.is_tag_label(line)
                or self.is_widget_option(line)
                or (self.is_widget_link(line) and not self.is_widget_high_rate_link(line))
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
        if FileNames.ACTIONS_FULL.value == self._filename or FileNames.ACTIONS.value in self._filename:
            return self._parse_actions()
        if FileNames.STALK_FULL.value == self._filename:
            return self._parse_stalk()
        elif FileNames.GENERATION.value in self._filename:
            return self._parse_generation()
        elif FileNames.TENTACLE_ADV_FULL.value == self._filename:
            return self._parse_tentacle_adv()
        elif FileNames.TENTACLES_FULL.value == self._filename:
            return self._parse_tentacles()
        elif FileNames.COMBAT_EFFECTS_FULL.value == self._filename:
            return self._parse_combat_effects()
        elif self._filename in {
            FileNames.NPC_GENERATION_FULL.value,
            FileNames.NPC_DAMAGE_FULL.value
        }:
            return self._parse_npc_span()
        elif FileNames.SPEECH_SYDNEY_FULL.value == self._filename:
            return self._parse_speech_sydney()
        elif FileNames.SPEECH_FULL.value == self._filename:
            return self._parse_speech()
        elif FileNames.STRUGGLE_FULL.value == self._filename:
            return self._parse_struggle()
        elif FileNames.SWARMS_FULL.value == self._filename:
            return self._parse_swarms()
        elif FileNames.SWARM_EFFECTS_FULL.value == self._filename:
            return self._parse_swarm_effects()
        elif FileNames.COMBAT_WIDGETS_FULL.value == self._filename:
            return self._parse_combat_widgets()
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
                or self.is_tag_label(line)
                or self.is_widget_set_to(line, {
                    "_leftaction", "_rightaction", "_feetaction",
                    "_targetlistarms", "_targetlistall", "_mouthaction",
                    "_anusaction", "_actions", "_undressLeftTargets",
                    "_undressRightTargets", "_handGuideOptions", "_penisaction",
                    "_askActions", "_vaginaaction", "_text_output", "_chestaction",
                    "_thighaction", "_npccr", "_npcff"
                })
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
            ):
                results.append(True)
            elif self.is_only_widgets(line) or self.is_json_line(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_generation(self):
        """只有 <span """
        return self._parse_type_only("<span ")

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
                or self.is_only_widgets(line)
            ):
                results.append(False)
            elif '{"desc":' in line or "you" in line.lower():
                results.append(True)
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
                or self.is_widget_set_to(line, {"_wraith_output"})
            ):
                results.append(True)
            elif self.is_only_widgets(line) or self.is_json_line(line) or ("<<set " in line and ">>" not in line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_npc_span(self):
        """只有 <span"""
        return self._parse_type_only("<span ")

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
                self.is_widget_set_to(line, {"_sydneyText"})
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
                self.is_widget_set_to(line, {r"\$_text_output", r"\$_sexToy", r"\$_strings"})
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
                "_targetlistarms", "_rightaction"
            }):
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

            if (
                self.is_comment(line)
                or self.is_event(line)
                or self.is_only_marks(line)
                or self.is_json_line(line)
            ):
                results.append(False)
            elif self.is_widget_set_to(line, {
                "_leftaction", "_rightaction", "_feetaction",
                "_targetlistarms", "_targetlistall"
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
            elif self.is_tag_span(line) or self.is_widget_set_to(line, {"_text_output"}):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    """ base-debug """
    def parse_base_debug(self):
        return self.parse_normal()

    """ base-system """
    def parse_base_system(self):
        """ base-system """
        if FileNames.CHARACTERISTICS_FULL.value == self._filename:
            return self._parse_characteristic()
        elif FileNames.SOCIAL_FULL.value == self._filename:
            return self._parse_social()
        elif FileNames.TRAITS_FULL.value == self._filename:
            return self._parse_traits()
        elif FileNames.BODYWRITING_FULL.value == self._filename:
            return self._parse_body_writing()
        elif FileNames.BODYWRITING_OBJECTS_FULL.value == self._filename:
            return self._parse_body_writing_objects()
        elif FileNames.CAPTION_FULL.value == self._filename:
            return self._parse_caption()
        elif self._filename in {
            FileNames.DEVIANCY_FULL.value,
            FileNames.EXHIBITIONISM_FULL.value,
            FileNames.PROMISCUITY_FULL.value
        }:
            return self._parse_sex_stat()
        elif FileNames.IMAGES_FULL.value == self._filename:
            return self._parse_system_images()
        elif FileNames.MOBILE_STATS_FULL.value == self._filename:
            return self._parse_mobile_stats()
        elif FileNames.NAME_LIST_FULL.value == self._filename:
            return self._parse_name_list()
        elif FileNames.NICKNAMES_FULL.value == self._filename:
            return self._parse_nicknames()
        elif FileNames.PLANT_OBJECTS_FULL.value == self._filename:
            return self._parse_plant_objects()
        elif FileNames.RADIO_FULL.value == self._filename:
            return self._parse_radio()
        elif FileNames.SETTINGS_FULL.value == self._filename:
            return self._parse_settings()
        elif FileNames.SKILL_DIFFICULTIES_FULL.value == self._filename:
            return self._parse_skill_difficulties()
        elif FileNames.SLEEP_FULL.value == self._filename:
            return self._parse_sleep()
        elif FileNames.STAT_CHANGES_FULL.value == self._filename:
            return self._parse_stat_changes()
        elif FileNames.TENDING_FULL.value == self._filename:
            return self._parse_tending()
        elif FileNames.TEXT_FULL.value == self._filename:
            return self._parse_system_text()
        elif FileNames.TIME_FULL.value == self._filename:
            return self._parse_time()
        elif FileNames.TIPS_FULL.value == self._filename:
            return self._parse_tips()
        elif FileNames.TRANSFORMATIONS_FULL.value == self._filename:
            return self._parse_transformations()
        elif FileNames.SYSTEM_WIDGETS_FULL.value == self._filename:
            return self._parse_system_widgets()
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
                or self.is_tag_span(line)
                or self.is_widget_set_to(line, {
                    "_trimester",  "_vaginaWetnessTextConfig",
                    "_childType", r"\$_pregnancyRisk", r"\$_number"
                })
            ):
                results.append(True)
            elif (
                self.is_only_widgets(line)
                or ("<<set " in line and ">>" not in line)
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
            elif "description: '" in line or self.is_tag_span(line):
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
        return self._parse_type_only({"name:", "text:", "title:", "<summary", "<<option"})

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
            elif self.is_widget_set_to(line, {"_text_output"}) or self.is_tag_span(line):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_body_writing_objects(self):
        """half-json"""
        return self._parse_type_only("writing")

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
            elif self.is_tag_span(line) or self.is_widget_button(line):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_sex_stat(self):
        """纯文本"""
        return self._parse_type_pure_text()

    def _parse_system_images(self):
        """只有span"""
        return self._parse_type_only_regex(r"<span.*?>[\"\w]")

    def _parse_mobile_stats(self):
        """只有<span>"""
        return self._parse_type_only("<span>")

    def _parse_name_list(self):
        """只有 " """
        return self._parse_type_startwith('"')

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
            if line in ["/*", "<!--", "<<set "] or (any(line.startswith(_) for _ in {"/*", "<!--", "<<set "}) and all(
                    _ not in line for _ in {"*/", "-->", ">>"})):
                multirow_comment_flag = True
                results.append(False)
                continue
            elif line in ["*/", "-->", ">>"] or any(line.endswith(_) for _ in {"*/", "-->", ">>"}):
                multirow_comment_flag = False
                results.append(False)
                continue
            elif multirow_comment_flag:
                results.append(False)
                continue

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif self.is_tag_span(line):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_nicknames(self):
        """只有 " """
        return self._parse_type_only(r"<<set _text_output to")

    def _parse_plant_objects(self):
        """json"""
        return self._parse_type_only("plural:")

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
            elif (
                    self.is_tag_span(line)
                    or self.is_tag_label(line)
                    or self.is_tag_input(line)
                    or self.is_widget_button(line)
                    or (self.is_widget_link(line) and not self.is_widget_high_rate_link(line))
                    or "<<set _buttonName " in line or "<<set _name " in line or "<<set _penisNames " in line
            ):
                results.append(True)
            elif self.is_only_widgets(line):
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
                (not line.strip().startswith("<") and not line.strip().startswith("/*") and "::" not in line.strip())
                or "<span " in line.strip() or ("<<link [[ " in line.strip() and "[[Next" not in line.strip())
            ) for line in self._lines
        ]

    def _parse_stat_changes(self):
        """只有<span"""
        return self._parse_type_only("<span ")

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
                    "<span " in line
                    or "<<link " in line
                    or not line.startswith("<")
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
                    line.startswith('"')
                    or "<span " in line
                    or '<<set _text_output to "' in line
                    or "<<set _text_output to '" in line
                    or '<<set _text_output to `' in line
            ):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    def _parse_time(self):
        """只有<span"""
        return self._parse_type_only("<span ")

    def _parse_tips(self):
        """只有<h3>和 " """
        return self._parse_type_startwith({'"', "<h3>"})

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
        multirow_script_flag = False
        for line in self._lines:
            line = line.strip()
            if not line:
                results.append(False)
                continue

            """跨行注释，逆天"""
            if (
                line in ["/*", "<!--"]
                or (
                    any(line.startswith(_) for _ in {"/*", "<!--"})
                    and all(_ not in line for _ in {"*/", "-->"})
                )
            ):
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

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif (
                    self.is_tag_span(line)
                    or self.is_tag_label(line)
                    or self.is_widget_print(line)
                    or (self.is_widget_link(line) and not self.is_widget_high_rate_link(line))
            ):
                results.append(True)
            elif self.is_only_widgets(line):
                results.append(False)
            else:
                results.append(True)
        return results

    """ 其它 """
    def parse_normal(self):
        results = []
        multirow_comment_flag = False
        multirow_script_flag = False
        multirow_run_flag = False
        multirow_if_flag = False
        maybe_json_flag = False
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
                results.append(False)
                continue

            """跨行run，逆天"""
            if line.startswith("<<run ") and ">>" not in line:
                multirow_run_flag = True
                results.append(False)
                continue
            elif multirow_run_flag and line in {"})>>", "}>>"}:
                multirow_run_flag = False
                results.append(False)
                continue
            elif multirow_run_flag:
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

            """突如其来的json"""
            if ((line.startswith("<<set ") or line.startswith("<<error {")) and ">>" not in line) or line.endswith("[") or line.endswith("{") or line.endswith("("):
                maybe_json_flag = True
            elif maybe_json_flag and ">>" in line:
                maybe_json_flag = False

            if self.is_comment(line) or self.is_event(line) or self.is_only_marks(line):
                results.append(False)
            elif (
                "<" in line and (
                    self.is_tag_span(line)
                    or self.is_tag_label(line)
                    or self.is_tag_input(line)
                    or self.is_widget_note(line)
                    or self.is_widget_print(line)
                    or self.is_widget_option(line)
                    or (self.is_widget_link(line) and not self.is_widget_high_rate_link(line))
                    or ("<<set " in line and self.is_widget_set_to(line, {
                        r"\$_strings", r"\$_text_output", "_text_output", r"\$_customertype", r"\$_theboy"
                    }))
                    or any(re.findall(r"<<set (?:(?:\$|_)[^_][#;\w\.\(\)\[\]\"\'`]*) to \[[\"\'`\w,\s]*\]>>", line))
                )
            ):
                results.append(True)
            elif ("<" in line and self.is_only_widgets(line)) or (maybe_json_flag and self.is_json_line(line)):
                results.append(False)
            else:
                results.append(True)
        return results

    """ 归整 """
    def _parse_type_only(self, pattern: Union[str, Set[str]]) -> List[bool]:
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

    def _parse_type_only_regex(self, pattern: Union[str, Set[str]]) -> List[bool]:
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

    def _parse_type_startwith(self, pattern: Union[str, Set[str]]) -> List[bool]:
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

    def _parse_type_pure_text(self) -> List[bool]:
        """指文件中只有纯文本需要提取"""
        return [
            line.strip() and
            not line.strip().startswith("<") and "::" not in line.strip()
            for line in self._lines
        ]

    def _parse_type_between(self, starts: List[str], ends: List[str], contain: bool = False) -> List[bool]:
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
        return any(line.startswith(_) for _ in {"/*", "<!--", "*/", "*"})

    @staticmethod
    def is_json_line(line: str) -> bool:
        """ xxx: yyy """
        return any(re.findall(r"^[\w\"]*:\s*[ \$\.\w\":,\|\(\)\{\}\[\]]+,*$", line))

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
        return any(re.findall(r'<span.*?>[\"\w\.]', line))

    @staticmethod
    def is_tag_label(line: str) -> bool:
        """<label>xxx</label>"""
        return any(re.findall(r"<label>\w", line))

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
    def is_widget_set_to(line: str, keys: Set[str]) -> bool:
        """<<set xxx yyy>>"""
        pattern = re.compile("<<set\s(?:" + r"|".join(keys) + ")[\'\"\w\s\[\]\$\+\.\(\)\{\}:\-]*(?:to|\+|\+=|\().*?[\w\{\"\'`]+(?:\w| \w|<<|\"\w)")
        return any(re.findall(pattern, line))

    @staticmethod
    def is_widget_print(line: str) -> bool:
        """<<print xxx>>"""
        return any(re.findall(r"<<print\s[^<]*[\"\'`\w]+[\?\s\w\.\$,\'\"<>\[\]\(\)/]+(?:\)>>|\">>|\'>>|`>>|\]>>)", line))

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
        return any(re.findall(r"<<option\s\"", line))

    @staticmethod
    def is_widget_link(line: str) -> bool:
        """<<link [[xxx|yyy]]>>, <<link "xxx">> """
        return any(re.findall(r"<<link\s*(\[\[|\"\w)", line))

    @staticmethod
    def is_widget_high_rate_link(line: str) -> bool:
        """高频选项"""
        return any(re.findall(r"<<link \[\[(Next\||Next\s\||Leave\||Refuse\||Return\||Resume\||Confirm\||Continue\||Stop\|)", line))

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

        widgets = {_ for _ in re.findall(r"(<<(?:[^<>]*?|for.*?)>>)", line) if _}
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


__all__ = [
    "ParseTextTwee"
]