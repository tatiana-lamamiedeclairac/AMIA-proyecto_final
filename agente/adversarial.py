"""
agente/adversarial.py — PARTE 2b: «la serpiente despierta».

Algoritmos de búsqueda adversarial para decidir la jugada del ARQUEÓLOGO en un
EstadoHuida (engine/huida.py).  Los tres devuelven la MEJOR ACCIÓN del
arqueólogo en *estado* (que siempre es un estado en el que mueve él).

  profundidad  número de jugadas del ARQUEÓLOGO que se miran hacia delante
               (cada una seguida de la respuesta de la serpiente).  Al llegar a
               profundidad 0, o a un estado terminal, se valora el estado:
               utilidad() si es terminal, evaluar(estado) si no.
  evaluar      función de evaluación evaluar(estado) -> número (más alto =
               mejor para el arqueólogo).

  * minimax     la serpiente es un adversario ÓPTIMO (minimiza).
  * alfabeta    igual que minimax, con poda alfa-beta: misma decisión, menos nodos.
  * expectimax  la serpiente es AZAR, con las probabilidades de
                estado.distribucion_serpiente().

Importante: recorred las acciones en el orden de estado.acciones() y, si hay
empate, quedaos con la PRIMERA de valor máximo (así minimax y alfa-beta
deciden lo mismo).  La serpiente puede tener una única «acción» None (descansa).
"""

from __future__ import annotations

from typing import Callable

from engine.huida import ARQUEOLOGO, EstadoHuida, distancia

INF = float("inf")


def minimax(estado: EstadoHuida, profundidad: int, evaluar: Callable):
    """Mejor acción del arqueólogo suponiendo una serpiente óptima."""
    raise NotImplementedError("TODO Parte 2b: minimax")


def alfabeta(estado: EstadoHuida, profundidad: int, evaluar: Callable):
    """Como minimax, pero podando ramas que no pueden cambiar la decisión."""
    raise NotImplementedError("TODO Parte 2b: alfabeta")


def expectimax(estado: EstadoHuida, profundidad: int, evaluar: Callable):
    """Mejor acción del arqueólogo suponiendo una serpiente estocástica."""
    raise NotImplementedError("TODO Parte 2b: expectimax")


def funcion_evaluacion(estado: EstadoHuida) -> float:
    """Valora un estado NO terminal desde el punto de vista del arqueólogo
    (más alto = mejor).  Ideas: distancia a la salida, distancia a la serpiente,
    si está aturdida, si conservamos la antorcha…  distancia(mundo, a, b) da la
    longitud del camino más corto sin pisar fosos."""
    raise NotImplementedError("TODO Parte 2b: funcion_evaluacion")
