"""Parte 2a — Modelado y heurísticas (agente/problema.py, agente/heuristicas.py).

Los algoritmos (bfs, ucs, astar) vienen hechos en engine/busqueda.py: aquí se
comprueba que vuestros PROBLEMAS y HEURÍSTICAS son correctos.
"""

import heapq
from collections import defaultdict
from dataclasses import replace

import pytest

from engine.busqueda import astar, bfs, ucs
from engine.juego import LANZAMIENTOS, Juego, destino
from engine.mundo import Mundo, generar_mundo

pytestmark = pytest.mark.parte2a

# (mapa, acciones mínimas, coste mínimo)
MAPAS = [("ejemplo_enunciado", 11, 11), ("pasillo_serpiente", 12, 12),
         ("escombros", 11, 11), ("expedicion", 13, 13)]
COSTES_SEMILLAS = {1: 10, 2: 12, 3: 11, 4: 10, 5: 11}               # 1 perdido
COSTES_EXPEDICION = {1: 11, 2: 17, 3: 12, 4: 19, 5: 15}             # 3 perdidos
COSTES_TOROIDAL = {1: 13, 2: 12, 3: 14, 4: 14, 5: 9}                # 3 perdidos, toroidal


def ejecutar(mundo, plan):
    """Ejecuta el plan en el simulador real y devuelve el juego."""
    juego = Juego(mundo)
    for accion in plan:
        assert not juego.terminado, "el plan sigue después de terminar la partida"
        juego.ejecutar(accion)
    return juego


def resolver(algoritmo, mundo):
    from agente.heuristicas import heuristica_rescate
    from agente.problema import ProblemaRescate
    p = ProblemaRescate(mundo)
    plan = astar(p, heuristica_rescate) if algoritmo == "astar" else algoritmo(p)
    assert plan is not None, "no se encuentra solución"
    return p, plan


# ---------------------------------------------------------------- ProblemaRescate
@pytest.mark.parametrize("mapa,acciones,coste", MAPAS)
def test_bfs_templo(mapa, acciones, coste):
    """[3 pts] Con vuestro problema, BFS rescata y sale con el MENOR NÚMERO de acciones."""
    mundo = Mundo.cargar(mapa)
    _p, plan = resolver(bfs, mundo)
    juego = ejecutar(mundo, plan)
    assert juego.exito, f"el plan no rescata a todos y sale (motivo: {juego.motivo})"
    assert len(plan) == acciones


@pytest.mark.parametrize("mapa,acciones,coste", MAPAS)
def test_ucs_templo(mapa, acciones, coste):
    """[4 pts] Con vuestro problema, UCS rescata y sale con el MENOR COSTE."""
    mundo = Mundo.cargar(mapa)
    p, plan = resolver(ucs, mundo)
    juego = ejecutar(mundo, plan)
    assert juego.exito, f"el plan no rescata a todos y sale (motivo: {juego.motivo})"
    assert juego.coste == coste
    assert p.coste_plan(plan) == coste, "los costes del problema no coinciden con los del juego"


def test_ucs_templos_aleatorios():
    """[4 pts] Óptimo en templos aleatorios con un perdido (semillas 1–5)."""
    for semilla, coste in COSTES_SEMILLAS.items():
        mundo = generar_mundo(semilla)
        _p, plan = resolver(ucs, mundo)
        juego = ejecutar(mundo, plan)
        assert juego.exito and juego.coste == coste, f"semilla {semilla}"


def test_ucs_expediciones():
    """[6 pts] Óptimo en expediciones con TRES perdidos (semillas 1–5)."""
    for semilla, coste in COSTES_EXPEDICION.items():
        mundo = generar_mundo(semilla, n_perdidos=3)
        _p, plan = resolver(ucs, mundo)
        juego = ejecutar(mundo, plan)
        assert juego.exito and juego.coste == coste, f"semilla {semilla}"


def test_antorcha():
    """[5 pts] Si la serpiente bloquea el paso, el plan óptimo usa la antorcha."""
    mundo = Mundo.cargar("pasillo_serpiente")
    _p, plan = resolver(ucs, mundo)
    assert any(a in LANZAMIENTOS for a in plan)
    assert ejecutar(mundo, plan).exito


# ---------------------------------------------------------------- heurística
def _coste_hasta_objetivo(problema):
    """Coste real mínimo desde cada estado alcanzable hasta un objetivo
    (Dijkstra hacia atrás sobre el grafo de estados del alumno)."""
    inicio = problema.estado_inicial()
    pendientes, vistos = [inicio], {inicio}
    inversas = defaultdict(list)
    objetivos = []
    while pendientes:
        s = pendientes.pop()
        if problema.es_objetivo(s):
            objetivos.append(s)
        for _a, t, c in problema.sucesores(s):
            inversas[t].append((s, c))
            if t not in vistos:
                vistos.add(t)
                pendientes.append(t)
    dist = {o: 0 for o in objetivos}
    cola = [(0, i, o) for i, o in enumerate(objetivos)]
    k = len(cola)
    while cola:
        d, _, t = heapq.heappop(cola)
        if d > dist.get(t, float("inf")):
            continue
        for s, c in inversas[t]:
            if d + c < dist.get(s, float("inf")):
                dist[s] = d + c
                k += 1
                heapq.heappush(cola, (d + c, k, s))
    return vistos, dist


@pytest.mark.parametrize("mapa", ["ejemplo_enunciado", "pasillo_serpiente", "escombros",
                                  "expedicion"])
def test_heuristica_admisible(mapa):
    """[4 pts] heuristica_rescate nunca sobrestima el coste real (todos los estados)."""
    from agente.heuristicas import heuristica_rescate
    from agente.problema import ProblemaRescate
    p = ProblemaRescate(Mundo.cargar(mapa))
    estados, dist = _coste_hasta_objetivo(p)
    for s in estados:
        if s in dist:
            h = heuristica_rescate(s, p)
            assert h <= dist[s] + 1e-9, f"h({s}) = {h} > coste real {dist[s]}"


def _comparar_con_ucs(semillas, n_perdidos, toroidal=False):
    nodos_a = nodos_u = 0
    for semilla in semillas:
        mundo = generar_mundo(semilla, n_perdidos=n_perdidos, toroidal=toroidal)
        pa, plan_a = resolver("astar", mundo)
        pu, plan_u = resolver(ucs, mundo)
        assert pa.coste_plan(plan_a) == pu.coste_plan(plan_u), f"A* no es óptimo (semilla {semilla})"
        nodos_a += pa.nodos_expandidos
        nodos_u += pu.nodos_expandidos
    return nodos_a, nodos_u


def test_heuristica_un_perdido():
    """[5 pts] Con un perdido, A* es óptimo y expande ≤ 60 % de los nodos de UCS."""
    nodos_a, nodos_u = _comparar_con_ucs(range(10, 30), 1)
    assert nodos_a <= 0.6 * nodos_u, f"A* expande {nodos_a} nodos y UCS {nodos_u}"


def test_heuristica_expedicion():
    """[10 pts] Con TRES perdidos, A* es óptimo y expande ≤ 30 % de los nodos de UCS
    (no basta con mirar solo la salida o solo el perdido más cercano)."""
    nodos_a, nodos_u = _comparar_con_ucs(range(10, 30), 3)
    assert nodos_a <= 0.3 * nodos_u, f"A* expande {nodos_a} nodos y UCS {nodos_u}"


# ---------------------------------------------------------------- templo toroidal
def test_ucs_toroidal():
    """[4 pts] Templo TOROIDAL: UCS cruza los bordes y encuentra el plan de menor coste."""
    mundo = replace(Mundo.cargar("toroidal"), toroidal=True)
    p, plan = resolver(ucs, mundo)
    juego = ejecutar(mundo, plan)
    assert juego.exito and juego.coste == 9, f"coste {juego.coste} (motivo: {juego.motivo})"
    assert p.coste_plan(plan) == 9, "los costes del problema no coinciden con los del juego"
    for semilla, coste in COSTES_TOROIDAL.items():
        mundo = generar_mundo(semilla, n_perdidos=3, toroidal=True)
        _p, plan = resolver(ucs, mundo)
        juego = ejecutar(mundo, plan)
        assert juego.exito and juego.coste == coste, f"semilla {semilla}"


def test_heuristica_admisible_toroidal():
    """[4 pts] En el templo toroidal, heuristica_rescate tampoco sobrestima
    (cuidado: la distancia Manhattan de siempre ignora los atajos por los bordes)."""
    from agente.heuristicas import heuristica_rescate
    from agente.problema import ProblemaRescate
    p = ProblemaRescate(replace(Mundo.cargar("toroidal"), toroidal=True))
    estados, dist = _coste_hasta_objetivo(p)
    for s in estados:
        if s in dist:
            h = heuristica_rescate(s, p)
            assert h <= dist[s] + 1e-9, f"h({s}) = {h} > coste real {dist[s]}"


def test_heuristica_toroidal():
    """[4 pts] Templos toroidales con TRES perdidos: A* es óptimo y expande
    ≤ 30 % de los nodos de UCS."""
    nodos_a, nodos_u = _comparar_con_ucs(range(10, 30), 3, toroidal=True)
    assert nodos_a <= 0.3 * nodos_u, f"A* expande {nodos_a} nodos y UCS {nodos_u}"


# ---------------------------------------------------------------- ProblemaRuta
def test_problema_ruta():
    """[5 pts] ProblemaRuta solo pisa celdas permitidas y respeta los escombros."""
    from agente.heuristicas import heuristica_ruta
    from agente.problema import ProblemaRuta
    permitidas = {(1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2), (3, 3)}
    # rodear por arriba (escombros) cuesta más que por la izquierda
    for alg in (ucs, lambda p: astar(p, heuristica_ruta)):
        p = ProblemaRuta((1, 1), {(3, 3)}, permitidas, frozenset({(1, 2), (1, 3)}))
        plan = alg(p)
        pos = (1, 1)
        for a in plan:
            pos = destino(pos, a)
            assert pos in permitidas, f"pisa {pos}, que no está permitida"
        assert pos == (3, 3)
        assert p.coste_plan(plan) == 4
    assert ucs(ProblemaRuta((1, 1), {(5, 5)}, {(1, 1), (1, 2)})) is None
