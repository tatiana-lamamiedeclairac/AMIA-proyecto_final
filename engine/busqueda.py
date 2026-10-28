"""
engine/busqueda.py — algoritmos de búsqueda genéricos (PROPORCIONADOS).

Son los mismos que ya programasteis en la práctica de pathFinding; aquí se dan
hechos para que el trabajo se centre en FORMULAR bien los problemas
(agente/problema.py) y en diseñar HEURÍSTICAS (agente/heuristicas.py).

Los cuatro algoritmos reciben un problema que hereda de
engine.busqueda_base.ProblemaBusqueda y devuelven la LISTA DE ACCIONES que
lleva del estado inicial a un estado objetivo (lista vacía si el inicial ya es
objetivo, None si no hay solución).

Cómo funcionan todos:
  * Búsqueda en GRAFO: no se vuelve a expandir un estado ya expandido.
  * Piden los sucesores con problema.expandir(estado), que llama a vuestro
    sucesores() y cuenta los nodos expandidos (los tests comparan esa cuenta).
  * El test de objetivo se aplica al EXTRAER un nodo de la frontera.

Este fichero es parte del MOTOR: no debes modificarlo.
"""

from __future__ import annotations

import heapq
import itertools
from collections import deque
from typing import Callable, Optional

from engine.busqueda_base import ProblemaBusqueda


def _camino(padres: dict, estado) -> list:
    acciones = []
    while padres[estado] is not None:
        estado, accion = padres[estado]
        acciones.append(accion)
    return acciones[::-1]


def bfs(problema: ProblemaBusqueda) -> Optional[list]:
    """Búsqueda en anchura: solución con el MENOR NÚMERO DE ACCIONES."""
    inicio = problema.estado_inicial()
    frontera = deque([inicio])
    padres = {inicio: None}
    expandidos = set()
    while frontera:
        estado = frontera.popleft()
        if problema.es_objetivo(estado):
            return _camino(padres, estado)
        if estado in expandidos:
            continue
        expandidos.add(estado)
        for accion, sig, _coste in problema.expandir(estado):
            if sig not in padres:
                padres[sig] = (estado, accion)
                frontera.append(sig)
    return None


def dfs(problema: ProblemaBusqueda) -> Optional[list]:
    """Búsqueda en profundidad (en grafo): una solución cualquiera."""
    inicio = problema.estado_inicial()
    frontera = [(inicio, None)]
    padres: dict = {}
    while frontera:
        estado, padre = frontera.pop()
        if estado in padres:
            continue
        padres[estado] = padre
        if problema.es_objetivo(estado):
            return _camino(padres, estado)
        for accion, sig, _coste in reversed(problema.expandir(estado)):
            if sig not in padres:
                frontera.append((sig, (estado, accion)))
    return None


def ucs(problema: ProblemaBusqueda) -> Optional[list]:
    """Búsqueda de coste uniforme: solución de MENOR COSTE."""
    return astar(problema, lambda estado, problema: 0)


def astar(problema: ProblemaBusqueda,
          heuristica: Callable) -> Optional[list]:
    """A*: expande por menor f(n) = g(n) + h(n).  heuristica(estado, problema)."""
    inicio = problema.estado_inicial()
    contador = itertools.count()          # desempate estable (FIFO)
    frontera = [(heuristica(inicio, problema), next(contador), 0, inicio)]
    mejor_g = {inicio: 0}
    padres = {inicio: None}
    expandidos = set()
    while frontera:
        _f, _, g, estado = heapq.heappop(frontera)
        if estado in expandidos:
            continue
        if problema.es_objetivo(estado):
            return _camino(padres, estado)
        expandidos.add(estado)
        for accion, sig, coste in problema.expandir(estado):
            g2 = g + coste
            if sig not in expandidos and g2 < mejor_g.get(sig, float("inf")):
                mejor_g[sig] = g2
                padres[sig] = (estado, accion)
                heapq.heappush(frontera, (g2 + heuristica(sig, problema),
                                          next(contador), g2, sig))
    return None
