import pytest

from filemanager.errors import FMError
from filemanager.security.names import logical_name, terminal_safe


@pytest.mark.parametrize("name", [
    "../evil", "a/../../evil", "/absolute", "C:/evil", "C:relative",
    "\\\\server/share", "a\\b", "file:ads", "CON", "con.txt", "LPT1.log",
    "COM¹.txt", "trail.", "trail ", "double//slash", "./name", "a/..",
    "a\x00b", "a\x1bb", "a\u202eb", "a?b", "",
])
def test_windows_path_attacks(name):
    with pytest.raises(FMError):
        logical_name(name)


def test_terminal_escapes():
    assert terminal_safe("\x1b]0;owned\x07\n\u202e") == "\\u001b]0;owned\\u0007\\u000a\\u202e"


def test_safe_unicode():
    assert logical_name("данные/отчёт.json") == "данные/отчёт.json"

