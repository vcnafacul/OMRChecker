"""O OMRChecker tem que importar num ambiente sem monitor nenhum (container/CI headless).

`src/utils/interaction.py` roda no import de qualquer execução do motor
(`main` -> `entry` -> `template` -> `core` -> `interaction`). Se esse import exigir um monitor,
o OMRChecker morre com exit 1 antes de olhar a imagem em qualquer ambiente headless — foi o que
aconteceu num container `python:3.11-slim` (sem X11 e sem /dev/dri), onde o screeninfo levanta
`ScreenInfoError: No enumerators available`.

O headless é simulado (stub do screeninfo) em vez de depender do ambiente, para o teste valer
também em máquinas com display, onde `get_monitors()` funciona e o bug some.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# subprocess porque o stub precisa estar em sys.modules ANTES do primeiro import
_IMPORTA_SEM_MONITOR = """
import sys
import types


class ScreenInfoError(Exception):
    pass


def get_monitors(*args, **kwargs):
    raise ScreenInfoError("No enumerators available")


common = types.ModuleType("screeninfo.common")
common.ScreenInfoError = ScreenInfoError

fake = types.ModuleType("screeninfo")
fake.common = common
fake.ScreenInfoError = ScreenInfoError
fake.get_monitors = get_monitors

sys.modules["screeninfo"] = fake
sys.modules["screeninfo.common"] = common

import src.entry  # noqa: F401

print("import ok")
"""


def test_imports_without_any_monitor_available():
    proc = subprocess.run(
        [sys.executable, "-c", _IMPORTA_SEM_MONITOR],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert proc.returncode == 0, f"OMRChecker does not import headless:\n{proc.stderr[-2000:]}"
    assert "ScreenInfoError" not in proc.stderr
