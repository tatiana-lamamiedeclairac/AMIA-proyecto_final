"""
engine/referencia.py — agentes de referencia (PROPORCIONADOS).

Todos los agentes heredan de engine.juego.Agente e implementan
actuar(obs) -> Accion (o None para abandonar).  La observación (Observacion)
contiene: posicion, percepto, rescatada, antorcha, tamano, escombros y paso.

  * AgenteAleatorio   — elige movimientos al azar (muere casi siempre).
  * AgenteExplorador  — basado en modelo, SIN lógica formal: recuerda lo que ha
                        visto y solo pisa celdas que una regla sencilla
                        garantiza seguras.  Es la referencia que vuestro
                        AgenteLogico (Parte 3) debe superar.

Este fichero es parte del MOTOR: no debes modificarlo.
"""

from __future__ import annotations

import random
from typing import Optional

from engine.juego import MOVIMIENTOS, Accion, Agente, Observacion, accion_hacia, destino
from engine.mundo import vecinos


class AgenteAleatorio(Agente):
    """Elige una acción de movimiento al azar."""

    def __init__(self, semilla: Optional[int] = None) -> None:
        self.rng = random.Random(semilla)

    def actuar(self, obs: Observacion) -> Accion:
        return self.rng.choice(list(MOVIMIENTOS))


# ---------------------------------------------------------------------------
# Utilidad
# ---------------------------------------------------------------------------

def movimientos_sin_pared(obs: Observacion) -> list[Accion]:
    """Movimientos que no chocan contra una pared, según el percepto."""
    p = obs.percepto
    bloqueado = {
        Accion.ARRIBA: p.pared_arriba,
        Accion.ABAJO: p.pared_abajo,
        Accion.IZQUIERDA: p.pared_izquierda,
        Accion.DERECHA: p.pared_derecha,
    }
    return [a for a in MOVIMIENTOS if not bloqueado[a]]


# ---------------------------------------------------------------------------
# Agente basado en modelo (exploración en profundidad «online»)
# ---------------------------------------------------------------------------

class AgenteExplorador(Agente):
    """
    Agente basado en modelo, sin base de conocimiento lógica.

    Modelo interno:
      * visitadas — celdas pisadas.
      * seguras   — regla conservadora: una celda es segura si se ha visitado o
                    es vecina de una celda visitada SIN corriente ni siseo.
      * pila      — camino recorrido, para poder retroceder (DFS online).

    Estrategia:
      1. Mientras no tenga a la Dra. Vega, explora en profundidad las celdas
         seguras no visitadas; si no quedan vecinas, retrocede.
      2. Cuando la rescata, empieza una nueva exploración en profundidad en la
         que prueba SALIR en cada celda con luz que no haya probado aún.
      3. Si ya no puede hacer nada más, abandona (None).
    """

    def __init__(self) -> None:
        self.visitadas: set = set()
        self.seguras: set = set()
        self.pila: list = []
        self.fase = "buscar"
        self.vistas_fase: set = set()
        self.salidas_probadas: set = set()

    def actuar(self, obs: Observacion) -> Optional[Accion]:
        pos, p = obs.posicion, obs.percepto
        if pos not in self.visitadas:
            self.visitadas.add(pos)
            self.seguras.add(pos)
            if not p.corriente and not p.siseo:
                self.seguras.update(vecinos(pos, obs.tamano))

        if obs.rescatada and self.fase == "buscar":
            self.fase = "salir"
            self.vistas_fase = set()
            self.pila = []

        if self.fase == "salir" and p.luz and pos not in self.salidas_probadas:
            self.salidas_probadas.add(pos)
            return Accion.SALIR

        vistas = self.visitadas if self.fase == "buscar" else self.vistas_fase
        vistas.add(pos)
        if not self.pila or self.pila[-1] != pos:
            self.pila.append(pos)

        for n in vecinos(pos, obs.tamano):
            if n in self.seguras and n not in vistas:
                return accion_hacia(pos, n)

        self.pila.pop()                     # callejón sin salida: retroceder
        if self.pila:
            return accion_hacia(pos, self.pila[-1])
        return None
