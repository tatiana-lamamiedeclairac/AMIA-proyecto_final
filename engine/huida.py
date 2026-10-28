"""
engine/huida.py — PARTE 2b: «la serpiente despierta» (búsqueda adversarial).

Al rescatar a la Dra. Vega, la serpiente se despierta y persigue al arqueólogo
hasta la salida.  El mapa es CONOCIDO (como en la Parte 2a) y se juega por
turnos: primero mueve el arqueólogo y después la serpiente.

Reglas:
  * Empieza en la celda de la Dra. Vega (ya rescatada); la serpiente, en la suya.
  * El arqueólogo GANA al llegar a la salida y PIERDE si coincide en una celda
    con la serpiente (porque entra él o porque entra ella).
  * Nadie puede pisar un foso.  Los escombros no influyen en esta parte.
  * La serpiente es algo más lenta: descansa (no se mueve) en sus turnos 3, 6, 9…
  * Antorcha (un solo uso): LANZAR_* hacia la serpiente cuando está ADYACENTE en
    esa dirección la deja aturdida 3 turnos (no se mueve).
  * Si pasan 60 turnos sin que nadie gane, la partida acaba en empate.
  * Utilidad (para el arqueólogo): +1000 − turnos si escapa, −1000 si lo
    atrapan, 0 si hay empate.

Para vuestros algoritmos (agente/adversarial.py), un EstadoHuida ofrece:

    estado.jugador()           'arqueologo' o 'serpiente' (quién mueve ahora)
    estado.acciones()          acciones legales del jugador que mueve
                               (para la serpiente, [None] si le toca descansar)
    estado.sucesor(accion)     nuevo estado (no modifica el actual)
    estado.es_terminal()       ¿ha acabado la partida?
    estado.utilidad()          valor de un estado terminal para el arqueólogo
    estado.distribucion_serpiente()
                               [(accion, probabilidad), ...] según el modelo de la
                               serpiente estocástica (para expectimax)
    distancia(mundo, a, b)     longitud del camino más corto de a a b sin pisar
                               fosos (útil para la función de evaluación)

EstadoHuida.nodos cuenta cuántos sucesores se han generado (para comparar
minimax con alfa-beta).

Este fichero es parte del MOTOR: no debes modificarlo.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field, replace
from functools import lru_cache
from typing import Callable, Optional

from engine.juego import LANZAMIENTOS, MOVIMIENTOS, Accion, Percepto, destino
from engine.mundo import Celda, Mundo

MAX_TURNOS = 60
TURNOS_ATURDIDA = 3
DESCANSO_CADA = 3            # la serpiente descansa en sus turnos 3, 6, 9…
PROB_VORAZ = 0.7             # serpiente estocástica: 70 % voraz, 30 % al azar
ARQUEOLOGO, SERPIENTE = "arqueologo", "serpiente"


# ---------------------------------------------------------------------------
# Distancias sin pisar fosos
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _distancias_desde(mundo: Mundo, origen: Celda) -> dict:
    dist = {origen: 0}
    cola = deque([origen])
    while cola:
        c = cola.popleft()
        for v in mundo.vecinos(c):
            if v not in dist and v not in mundo.fosos:
                dist[v] = dist[c] + 1
                cola.append(v)
    return dist


def distancia(mundo: Mundo, a: Celda, b: Celda) -> float:
    """Pasos del camino más corto de *a* a *b* sin pisar fosos (inf si no hay)."""
    return _distancias_desde(mundo, b).get(a, float("inf"))


# ---------------------------------------------------------------------------
# Estado del juego
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EstadoHuida:
    mundo: Mundo
    arqueologo: Celda
    serpiente: Celda
    antorcha: bool = True
    aturdida: int = 0          # turnos que le quedan a la serpiente aturdida
    turno: int = 0             # jugadas completas (arqueólogo + serpiente)
    mueve: str = ARQUEOLOGO

    nodos = 0                  # contador global de sucesores generados

    # ------------------------------------------------------------------ consultas
    def jugador(self) -> str:
        return self.mueve

    def escapa(self) -> bool:
        return self.arqueologo == self.mundo.salida and self.arqueologo != self.serpiente

    def atrapado(self) -> bool:
        return self.arqueologo == self.serpiente

    def es_terminal(self) -> bool:
        return self.atrapado() or self.escapa() or self.turno >= MAX_TURNOS

    def utilidad(self) -> float:
        if self.atrapado():
            return -1000
        if self.escapa():
            return 1000 - self.turno
        return 0

    def serpiente_descansa(self) -> bool:
        return self.aturdida > 0 or (self.turno + 1) % DESCANSO_CADA == 0

    # ------------------------------------------------------------------ acciones
    def acciones(self) -> list:
        if self.es_terminal():
            return []
        m = self.mundo
        if self.mueve == ARQUEOLOGO:
            out = [a for a in MOVIMIENTOS
                   if m.dentro(destino(self.arqueologo, a))
                   and destino(self.arqueologo, a) not in m.fosos]
            if self.antorcha:
                out += [a for a in LANZAMIENTOS
                        if destino(self.arqueologo, a) == self.serpiente]
            return out
        if self.serpiente_descansa():
            return [None]
        return [a for a in MOVIMIENTOS
                if m.dentro(destino(self.serpiente, a))
                and destino(self.serpiente, a) not in m.fosos]

    def sucesor(self, accion) -> "EstadoHuida":
        if accion not in self.acciones():
            raise ValueError(f"Acción ilegal para {self.mueve}: {accion!r}")
        EstadoHuida.nodos += 1
        if self.mueve == ARQUEOLOGO:
            if accion in LANZAMIENTOS:
                return replace(self, antorcha=False, aturdida=TURNOS_ATURDIDA, mueve=SERPIENTE)
            return replace(self, arqueologo=destino(self.arqueologo, accion), mueve=SERPIENTE)
        if accion is None:
            return replace(self, aturdida=max(0, self.aturdida - 1),
                           turno=self.turno + 1, mueve=ARQUEOLOGO)
        return replace(self, serpiente=destino(self.serpiente, accion),
                       turno=self.turno + 1, mueve=ARQUEOLOGO)

    # ------------------------------------------------------------------ modelo de la serpiente
    def accion_voraz(self):
        """Paso de la serpiente que más la acerca al arqueólogo (desempate fijo)."""
        acciones = self.acciones()
        if acciones == [None]:
            return None
        return min(acciones, key=lambda a: distancia(self.mundo, destino(self.serpiente, a),
                                                      self.arqueologo))

    def distribucion_serpiente(self) -> list:
        """[(accion, prob)] de la serpiente estocástica: 70 % la acción voraz y
        30 % repartido por igual entre todas sus acciones legales."""
        acciones = self.acciones()
        if acciones == [None]:
            return [(None, 1.0)]
        voraz = self.accion_voraz()
        azar = (1 - PROB_VORAZ) / len(acciones)
        return [(a, azar + (PROB_VORAZ if a == voraz else 0.0)) for a in acciones]


def estado_inicial(mundo: Mundo) -> EstadoHuida:
    """La persecución empieza en la celda de la Dra. Vega."""
    return EstadoHuida(mundo, mundo.vega, mundo.serpiente)


# ---------------------------------------------------------------------------
# Serpientes y agente de referencia
# ---------------------------------------------------------------------------

class SerpienteVoraz:
    """Siempre da el paso que más la acerca al arqueólogo."""

    def elegir(self, estado: EstadoHuida):
        return estado.accion_voraz()


class SerpienteEstocastica:
    """Con probabilidad 0.7 actúa como la voraz; si no, se mueve al azar.
    Es exactamente el modelo de EstadoHuida.distribucion_serpiente()."""

    def __init__(self, semilla: Optional[int] = None) -> None:
        self.rng = random.Random(semilla)

    def elegir(self, estado: EstadoHuida):
        acciones, pesos = zip(*estado.distribucion_serpiente())
        return self.rng.choices(acciones, weights=pesos)[0]


def huir_directo(estado: EstadoHuida):
    """Referencia ingenua: camino más corto a la salida, ignorando a la serpiente."""
    m = estado.mundo
    movs = [a for a in estado.acciones() if a in MOVIMIENTOS]
    return min(movs, key=lambda a: distancia(m, destino(estado.arqueologo, a), m.salida))


# ---------------------------------------------------------------------------
# Partida
# ---------------------------------------------------------------------------

@dataclass
class ResultadoHuida:
    escapa: bool
    atrapado: bool
    turnos: int
    acciones: list = field(default_factory=list)

    @property
    def utilidad(self) -> float:
        return 1000 - self.turnos if self.escapa else (-1000 if self.atrapado else 0)


def jugar_huida(mundo: Mundo, decidir: Callable, serpiente=None, display=None,
                estado: Optional[EstadoHuida] = None) -> ResultadoHuida:
    """Juega una persecución.  *decidir(estado) -> accion* es la política del
    arqueólogo; *serpiente* tiene un método elegir(estado) (por defecto, voraz)."""
    serpiente = serpiente or SerpienteVoraz()
    estado = estado or estado_inicial(mundo)
    acciones = []
    if display is not None:
        display.inicializar(VistaHuida(estado))
    while not estado.es_terminal():
        if estado.jugador() == ARQUEOLOGO:
            accion = decidir(estado)
            if accion not in estado.acciones():
                raise ValueError(f"El arqueólogo eligió una acción ilegal: {accion!r}")
            acciones.append(accion)
        else:
            accion = serpiente.elegir(estado)
        estado = estado.sucesor(accion)
        if display is not None and estado.jugador() == ARQUEOLOGO:
            display.actualizar(VistaHuida(estado, acciones))
    if display is not None:
        display.final(VistaHuida(estado, acciones))
    return ResultadoHuida(estado.escapa(), estado.atrapado(), estado.turno, acciones)


# ---------------------------------------------------------------------------
# Adaptador para reutilizar los visores (gui.VisorTk, texto.VisorTexto)
# ---------------------------------------------------------------------------

class VistaHuida:
    """Presenta un EstadoHuida con la interfaz que esperan los visores."""

    def __init__(self, estado: EstadoHuida, acciones: Optional[list] = None) -> None:
        self.mundo = replace(estado.mundo, serpiente=estado.serpiente)
        self.posicion = estado.arqueologo
        self.visitadas = set(estado.mundo.celdas())
        self.rescatados = set(estado.mundo.perdidos)
        self.rescatada = True
        self.serpiente_presente = True
        self.antorcha = estado.antorcha
        self.pasos = estado.turno
        self.coste = estado.turno
        self.acciones = acciones or []
        self.terminado = estado.es_terminal()
        self.exito = estado.escapa()
        self.motivo = ("exito" if estado.escapa() else "serpiente" if estado.atrapado()
                       else "limite" if estado.es_terminal() else "")
        self.aturdida = estado.aturdida

    def percepto(self) -> Percepto:
        return Percepto()
