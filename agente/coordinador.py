"""
agente/coordinador.py — PARTE 4: elegir el mejor reparto de la expedición.

clingo (agente/expedicion.lp) ya ha generado TODOS los repartos válidos.  Cada
reparto es un dict {arqueólogo: frozenset de celdas de sus perdidos}, p. ej.

    {"indy": frozenset({(2, 5), (4, 3)}), "lara": frozenset({(2, 6), (6, 2), (5, 1)})}

Aquí se decide cuál conviene: cada arqueólogo planifica su parte con A* (el
ProblemaRescate de la Parte 2a, limitado a SUS perdidos) y la expedición
termina cuando sale el último, así que el mejor reparto es el de menor
MAKESPAN = max(coste de cada arqueólogo).

Pista: dataclasses.replace(mundo, perdidos=...) crea una copia del templo con
otros perdidos, sin modificar el original.  Como el mismo grupo de perdidos
aparece en varios repartos, puede compensar guardar los resultados
(functools.lru_cache: Mundo y frozenset se pueden usar como claves).
"""

from __future__ import annotations

from dataclasses import replace

from agente.heuristicas import heuristica_rescate
from agente.problema import ProblemaRescate
from engine.busqueda import astar
from engine.mundo import Mundo


def plan_individual(mundo: Mundo, perdidos: frozenset) -> list:
    """Plan óptimo (lista de acciones, terminada en SALIR) de un arqueólogo que
    entra solo al templo y rescata exactamente a *perdidos*."""
    raise NotImplementedError("TODO Parte 4: plan_individual")


def coste_individual(mundo: Mundo, perdidos: frozenset) -> float:
    """Coste de ese plan (float('inf') si no hay plan posible).
    Pista: ProblemaBusqueda.coste_plan(plan)."""
    raise NotImplementedError("TODO Parte 4: coste_individual")


def elegir_reparto(mundo: Mundo, repartos: list) -> dict:
    """De entre *repartos* (los modelos de clingo), el de MENOR makespan."""
    raise NotImplementedError("TODO Parte 4: elegir_reparto")
