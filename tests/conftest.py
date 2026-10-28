"""
tests/conftest.py — configuración del autograder (pytest).

  * Añade la raíz del proyecto al path.
  * Al final imprime los PUNTOS por partes, leyendo los puntos «[N pts]» del
    docstring de cada test.

Uso:
    pytest                    # todo
    pytest -m parte2a         # solo una parte (parte2a, parte2b, parte3, parte4)
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

_PUNTOS = re.compile(r"\[(\d+(?:\.\d+)?)\s*pts?\]", re.IGNORECASE)
_PARTES = ("parte2a", "parte2b", "parte3", "parte4")
_marcador: dict = defaultdict(lambda: [0.0, 0.0])   # parte -> [obtenidos, posibles]


def _parte(item) -> str:
    for p in _PARTES:
        if item.get_closest_marker(p):
            return p
    return "otros"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    resultado = yield
    rep = resultado.get_result()
    if rep.when == "call" or (rep.when == "setup" and rep.failed):
        m = _PUNTOS.search(item.function.__doc__ or "")
        pts = float(m.group(1)) if m else 0.0
        cuenta = _marcador[_parte(item)]
        cuenta[1] += pts
        if rep.passed:
            cuenta[0] += pts


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not _marcador:
        return
    tr = terminalreporter
    tr.write_sep("=", "AUTOGRADER · El templo perdido", bold=True)
    total = [0.0, 0.0]
    for parte in (*_PARTES, "otros"):
        if parte in _marcador:
            ob, pos = _marcador[parte]
            tr.write_line(f"  {parte:<7} {ob:6.1f} / {pos:6.1f} puntos")
            total[0] += ob
            total[1] += pos
    tr.write_line(f"  Total tests: {total[0]:.1f} / {total[1]:.1f} (no es la nota)")
    tr.write_sep("=", "")
