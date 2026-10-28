"""
agente/heuristicas.py — PARTE 2a: heurísticas para A*.

Una heurística es una función heuristica(estado, problema) -> número que estima
el coste que falta hasta un objetivo.  Para que A* devuelva la solución óptima
debe ser ADMISIBLE: nunca sobrestimar el coste real.  En la defensa se pedirá
justificar por qué lo es (y si además es consistente).

Cuidado con las EXPEDICIONES (varios perdidos): el orden en que se rescata a
cada uno importa, y una heurística que solo mire la salida o el perdido más
cercano expande demasiados nodos (los tests exigen ≤ 30 % de los de UCS).

Y con los templos TOROIDALES (mundo.toroidal): ¿sigue siendo admisible la
distancia que uséis si se puede cruzar de un borde al opuesto?
"""

from __future__ import annotations

from engine.mundo import manhattan


def heuristica_rescate(estado, problema) -> float:
    """Heurística para ProblemaRescate (problema.mundo da acceso al mapa)."""
    raise NotImplementedError("TODO Parte 2a: heuristica_rescate")


def heuristica_ruta(estado, problema) -> float:
    """Heurística para ProblemaRuta (problema.objetivos es un conjunto de celdas)."""
    raise NotImplementedError("TODO Parte 2a: heuristica_ruta")
