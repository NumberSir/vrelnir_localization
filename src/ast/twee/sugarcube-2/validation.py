import re
from dataclasses import dataclass

from .passage import Passage

NOT_SPACE_REGEX = re.compile(r"\S")
SPACE_REGEX = re.compile(r"\s")
SETTINGS_SETUP_ACCESS_REGEX = re.compile(r"^(?:settings|setup)[.[]")
VAR_TEST_REGEX = re.compile(r"^[$_][$A-Z_a-z][$0-9A-Z_a-z]*")


@dataclass(frozen=True)
class Warning:
    message: str


class StateInfo:
    passages: list["Passage"]


@dataclass
class Evaluatable:
    original: ...
