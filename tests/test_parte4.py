"""Parte 4 — La expedición multiagente (agente/expedicion.lp, agente/coordinador.py)."""

import itertools
from dataclasses import replace

import pytest

from engine.asp import ProgramaInconsistente
from engine.expedicion import (ARQUEOLOGOS, PoliticaEgoista, ejecutar_expedicion,
                               generar_expedicion, jugar_coordinada, puede_rescatar,
                               repartos_validos)
from engine.juego import Juego
from engine.mundo import Mundo

pytestmark = pytest.mark.parte4

TRES_NORMALES = Mundo.desde_texto("AVV\n.S.\nV.E")


def esperados(mundo, capacidad):
    """Los repartos válidos, por fuerza bruta (2^n asignaciones)."""
    perdidos = sorted(mundo.perdidos)
    out = set()
    for asignacion in itertools.product(ARQUEOLOGOS, repeat=len(perdidos)):
        reparto = {n: frozenset(p for p, a in zip(perdidos, asignacion) if a == n)
                   for n in ARQUEOLOGOS}
        if all(puede_rescatar(n, mundo, p) for n, ps in reparto.items() for p in ps) \
                and all(0 < len(ps) <= capacidad for ps in reparto.values()):
            out.add(_clave(reparto))
    return out


def _clave(reparto):
    return tuple(tuple(sorted(reparto[n])) for n in ARQUEOLOGOS)


def obtenidos(mundo, capacidad=3):
    return {_clave(r) for r in repartos_validos(mundo, capacidad)}


# ---------------------------------------------------------------- expedicion.lp
def test_programa_tiene_modelos():
    """[2 pts] expedicion.lp tiene modelos y muestra rescata/2."""
    repartos = repartos_validos(Mundo.cargar("expedicion_roles"))
    assert repartos and any(r[n] for r in repartos for n in ARQUEOLOGOS)


def test_cada_perdido_un_arqueologo():
    """[3 pts] En todos los repartos, cada perdido lo rescata exactamente un arqueólogo."""
    for s in range(5):
        mundo = generar_expedicion(s)
        for r in repartos_validos(mundo):
            assert r["indy"] | r["lara"] == mundo.perdidos, f"semilla {s}: falta alguien"
            assert not r["indy"] & r["lara"], f"semilla {s}: alguien rescatado dos veces"


def test_roles():
    """[3 pts] Los heridos solo los rescata indy (botiquín); los atrapados, solo lara (pico)."""
    for s in range(5):
        mundo = generar_expedicion(s, n_heridos=2, n_atrapados=1)
        for r in repartos_validos(mundo):
            assert mundo.heridos <= r["indy"], f"semilla {s}: un herido sin botiquín"
            assert mundo.atrapados <= r["lara"], f"semilla {s}: un atrapado sin pico"


def test_capacidad():
    """[2 pts] Nadie rescata a más de capacidad(K) perdidos."""
    mundo = Mundo.cargar("expedicion_roles")
    for k in (3, 4):
        for r in repartos_validos(mundo, k):
            assert all(len(ps) <= k for ps in r.values())
    assert obtenidos(mundo, 4) == esperados(mundo, 4)


def test_todos_trabajan():
    """[2 pts] Los dos arqueólogos rescatan a alguien, aunque uno solo pudiera con todos."""
    assert obtenidos(TRES_NORMALES, 3) == esperados(TRES_NORMALES, 3)      # 6, no 8


def test_repartos_exactos():
    """[3 pts] Los modelos son EXACTAMENTE los repartos válidos (ni más, ni menos)."""
    for s in range(10):
        mundo = generar_expedicion(s, n_heridos=s % 3, n_atrapados=(s + 1) % 2)
        for k in (3, 4):
            assert obtenidos(mundo, k) == esperados(mundo, k), f"semilla {s}, capacidad {k}"


def test_imposible():
    """[1 pt] Cuatro heridos, un solo botiquín y capacidad 3: ningún reparto."""
    with pytest.raises(ProgramaInconsistente):
        repartos_validos(Mundo.cargar("expedicion_imposible"))


# ---------------------------------------------------------------- coordinador.py
def test_coste_individual():
    """[2 pts] coste_individual: coste óptimo de un arqueólogo con su parte."""
    from agente.coordinador import coste_individual
    mundo = Mundo.cargar("expedicion_roles")
    assert coste_individual(mundo, frozenset({(3, 1), (5, 3), (6, 6)})) == 16
    assert coste_individual(mundo, frozenset({(1, 6), (3, 2)})) == 16
    assert coste_individual(mundo, frozenset({(1, 6), (3, 2), (5, 3)})) == 20
    assert coste_individual(mundo, frozenset()) == 6           # directo a la salida y SALIR


def test_plan_individual():
    """[2 pts] plan_individual devuelve un plan que rescata a SUS perdidos y sale."""
    from agente.coordinador import coste_individual, plan_individual
    mundo = Mundo.cargar("expedicion_roles")
    for parte in (frozenset({(3, 1), (6, 6)}), frozenset({(1, 6), (3, 2), (5, 3)})):
        juego = Juego(replace(mundo, perdidos=parte))
        for accion in plan_individual(mundo, parte):
            juego.ejecutar(accion)
        assert juego.exito
        assert juego.coste == coste_individual(mundo, parte)


def test_elegir_reparto():
    """[2 pts] elegir_reparto devuelve un reparto de MENOR makespan."""
    from agente.coordinador import coste_individual, elegir_reparto
    def makespan(mundo, r):
        return max(coste_individual(mundo, ps) for ps in r.values())

    for mundo in (Mundo.cargar("expedicion_roles"), generar_expedicion(3), generar_expedicion(8)):
        repartos = repartos_validos(mundo)
        elegido = elegir_reparto(mundo, repartos)
        assert elegido in repartos
        assert makespan(mundo, elegido) == min(makespan(mundo, r) for r in repartos)
    mundo = Mundo.cargar("expedicion_roles")
    assert makespan(mundo, elegir_reparto(mundo, repartos_validos(mundo))) == 16


def test_expedicion_coordinada():
    """[3 pts] Coordinados nunca fallan y nunca tardan más que los egoístas."""
    for s in range(20):
        mundo = generar_expedicion(s)
        _, _, r = jugar_coordinada(mundo)
        assert r.exito, f"semilla {s}: {r.motivo}"
        e = ejecutar_expedicion(mundo, PoliticaEgoista())
        if e.exito:
            assert r.makespan <= e.makespan, f"semilla {s}"
