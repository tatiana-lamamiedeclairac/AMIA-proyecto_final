"""Parte 3 — Agente lógico en ASP (agente/templo.lp, agente/agente_logico.py)."""

import pytest

from engine.asp import ConocimientoASP
from engine.juego import LANZAMIENTOS, Accion, Juego, ejecutar_partida
from engine.mundo import Mundo, generar_mundo

pytestmark = pytest.mark.parte3


def kb_tras(mapa, acciones):
    """ConocimientoASP con lo observado al ejecutar *acciones* en *mapa*."""
    juego = Juego(Mundo.cargar(mapa) if isinstance(mapa, str) else mapa)
    kb = ConocimientoASP()
    kb.observar(juego.observacion(), None)
    for a in acciones:
        kb.observar(juego.ejecutar(a), a)
    return kb


# ---------------------------------------------------------------- templo.lp
def test_programa_tiene_modelos():
    """[4 pts] templo.lp, solo con la primera observación, tiene modelos y muestra
    foso/2, serpiente/2, salida/2 y segura/2."""
    kb = kb_tras(generar_mundo(1), [])
    predicados = {p for p, _ in kb.bravas()}
    assert {"foso", "serpiente", "salida", "segura"} <= predicados


def test_inicio_seguro():
    """[4 pts] Sin corriente ni siseo en (1,1), sus vecinas son seguras."""
    kb = kb_tras(generar_mundo(1), [])
    assert {(1, 1), (1, 2), (2, 1)} <= kb.seguras()
    assert (3, 3) not in kb.seguras()


def test_razonamiento_4x4():
    """[10 pts] Ejemplo del enunciado: se deduce la serpiente en (3,1), el foso en (1,3)
    y que (2,2) es segura, combinando percepciones de varias celdas."""
    kb = kb_tras("razonamiento_4x4", [Accion.DERECHA, Accion.IZQUIERDA, Accion.ABAJO])
    assert {(1, 1), (1, 2), (2, 1), (2, 2)} <= kb.seguras()
    assert (1, 3) not in kb.seguras() and (3, 1) not in kb.seguras()
    assert ("serpiente", (3, 1)) in kb.cautas()
    assert ("foso", (1, 3)) in kb.cautas()


def test_salida_por_luz():
    """[4 pts] La luz acota dónde está la salida, y un SALIR fallido la descarta."""
    kb = kb_tras("razonamiento_4x4", [Accion.DERECHA])
    assert ("salida", (1, 3)) not in kb.bravas()                 # sin luz en (1,2)
    assert ("salida", (2, 4)) in kb.bravas()                     # aún es posible
    mundo = Mundo.desde_texto("AE..\n....\n..F.\nS..V")
    kb = kb_tras(mundo, [Accion.SALIR, Accion.ABAJO])
    assert ("salida", (1, 1)) not in kb.bravas()                 # SALIR fallido
    assert ("salida", (1, 2)) in kb.cautas()                     # luz en (1,1), no en (2,1)


def test_antorcha():
    """[4 pts] Tras el chillido, la celda de la serpiente deja de ser peligrosa."""
    mundo = Mundo.desde_texto("A..F\nS...\n....\n.FVE")
    kb = kb_tras(mundo, [Accion.LANZAR_ABAJO])
    assert ("serpiente", (2, 1)) in kb.cautas()
    assert (2, 1) in kb.seguras()


def test_seguras_son_seguras():
    """[8 pts] Lo que vuestro programa deduce como seguro nunca tiene peligro, y
    deduce al menos lo evidente: las vecinas de una celda sin corriente ni siseo
    (exploración del agente de referencia en 20 templos)."""
    from engine.referencia import AgenteExplorador
    for semilla in range(400, 420):
        mundo = generar_mundo(semilla)
        juego, agente, kb = Juego(mundo), AgenteExplorador(), ConocimientoASP()
        obs, accion = juego.observacion(), None
        while True:
            kb.observar(obs, accion)
            seguras = kb.seguras()
            for c in seguras:
                assert not mundo.es_mortal(c), f"semilla {semilla}: {c} no es segura"
            if not obs.percepto.corriente and not obs.percepto.siseo and juego.serpiente_presente:
                assert set(mundo.vecinos(obs.posicion)) <= seguras, \
                    f"semilla {semilla}: no deduce que las vecinas de {obs.posicion} son seguras"
            accion = agente.actuar(obs)
            if accion is None:
                break
            obs = juego.ejecutar(accion)
            if juego.terminado:
                break


# ---------------------------------------------------------------- agente
def test_agente_logico_no_muere():
    """[10 pts] El agente lógico no muere nunca (30 templos)."""
    from agente.agente_logico import AgenteLogico
    for semilla in range(100, 130):
        r = ejecutar_partida(generar_mundo(semilla), AgenteLogico())
        assert not r.muerto, f"muere ({r.motivo}) en la semilla {semilla}"


def test_agente_logico_rescata():
    """[10 pts] El agente lógico gana al menos el 90 % de 30 templos resolubles."""
    from agente.agente_logico import AgenteLogico
    exitos = sum(ejecutar_partida(generar_mundo(s), AgenteLogico()).exito
                 for s in range(200, 230))
    assert exitos >= 27, f"solo {exitos}/30 éxitos"


def test_agente_logico_antorcha():
    """[3 pts] Si nada más es seguro, usa la antorcha contra la serpiente localizada."""
    from agente.agente_logico import AgenteLogico
    r = ejecutar_partida(Mundo.cargar("pasillo_serpiente"), AgenteLogico())
    assert not r.muerto
    assert any(a in LANZAMIENTOS for a in r.acciones)
