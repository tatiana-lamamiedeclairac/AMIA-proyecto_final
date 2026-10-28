"""
engine/busqueda_base.py — interfaz común de los problemas de búsqueda.

Todo problema de búsqueda (los vuestros de agente/problema.py y el grafo de
ejemplo de los tests) hereda de ProblemaBusqueda e implementa:

    estado_inicial()          -> estado
    es_objetivo(estado)       -> bool
    sucesores(estado)         -> lista de (accion, estado_siguiente, coste)

Los estados deben ser HASHABLES (tuplas, frozensets, enteros, cadenas...) para
poder guardarlos en conjuntos y diccionarios.

Los algoritmos de búsqueda NO deben llamar a sucesores() directamente sino a
expandir(), que hace lo mismo y además cuenta los nodos expandidos.  Así se
pueden comparar algoritmos y heurísticas.

Este fichero es parte del MOTOR: no debes modificarlo.
"""

from __future__ import annotations

from typing import Any, Hashable, Iterable, Optional


class ProblemaBusqueda:
    """Clase base abstracta de un problema de búsqueda."""

    nodos_expandidos: int = 0

    def estado_inicial(self) -> Hashable:
        raise NotImplementedError

    def es_objetivo(self, estado: Hashable) -> bool:
        raise NotImplementedError

    def sucesores(self, estado: Hashable) -> list[tuple[Any, Hashable, float]]:
        raise NotImplementedError

    # -- proporcionado ---------------------------------------------------------
    def expandir(self, estado: Hashable) -> list[tuple[Any, Hashable, float]]:
        """Devuelve sucesores(estado) y suma 1 al contador de nodos expandidos."""
        self.nodos_expandidos += 1
        return self.sucesores(estado)

    def reiniciar_contador(self) -> None:
        self.nodos_expandidos = 0

    def coste_plan(self, plan: Iterable) -> Optional[float]:
        """Coste de ejecutar *plan* desde el estado inicial (None si no es válido
        o no termina en un estado objetivo).  No cuenta como expansión."""
        estado, total = self.estado_inicial(), 0
        for accion in plan:
            for a, s, c in self.sucesores(estado):
                if a == accion:
                    estado, total = s, total + c
                    break
            else:
                return None
        return total if self.es_objetivo(estado) else None


class ProblemaGrafo(ProblemaBusqueda):
    """
    Problema de búsqueda sobre un grafo dirigido explícito (útil para probar
    los algoritmos).  Las acciones son el nombre del nodo destino.

        g = ProblemaGrafo({"S": {"A": 1, "B": 4}, "A": {"G": 5}, "B": {"G": 1}},
                          inicio="S", objetivo="G")
    """

    def __init__(self, aristas: dict, inicio: Hashable, objetivo: Hashable,
                 h: Optional[dict] = None) -> None:
        self.aristas = aristas
        self.inicio = inicio
        self.objetivo = objetivo
        self.h = h or {}

    def estado_inicial(self) -> Hashable:
        return self.inicio

    def es_objetivo(self, estado: Hashable) -> bool:
        return estado == self.objetivo

    def sucesores(self, estado: Hashable) -> list[tuple[Any, Hashable, float]]:
        # orden alfabético para que el comportamiento sea reproducible
        return [(dest, dest, coste)
                for dest, coste in sorted(self.aristas.get(estado, {}).items())]

    def heuristica(self, estado: Hashable, problema: "ProblemaGrafo" = None) -> float:
        return self.h.get(estado, 0)
