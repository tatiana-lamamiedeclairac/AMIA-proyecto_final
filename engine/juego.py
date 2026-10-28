"""
engine/juego.py — dinámica del juego: acciones, percepciones y bucle de partida.

Acciones (enum Accion):
    ARRIBA, ABAJO, IZQUIERDA, DERECHA            moverse a una celda adyacente
    LANZAR_ARRIBA, ..., LANZAR_DERECHA           lanzar la antorcha (un solo uso)
                                                  a la celda adyacente en esa dirección
    SALIR                                         abandonar el templo (solo funciona
                                                  en la celda de salida)

Costes:  moverse cuesta lo que indique la celda de destino (1, o 3 si tiene
escombros); chocar contra una pared, lanzar la antorcha o SALIR cuestan 1.

Percepción (clase Percepto), en el orden del enunciado:
    [corriente, siseo, luz, pared↑, pared↓, pared←, pared→, chillido]

    corriente : hay un foso en alguna celda adyacente.
    siseo     : la serpiente (si sigue ahí) está en una celda adyacente.
    luz       : la salida está en la celda actual o en una adyacente.
    pared_*   : hay una pared del templo en esa dirección (nunca en un templo toroidal).
    chillido  : la antorcha que se acaba de lanzar ha ahuyentado a la serpiente.

Este fichero es parte del MOTOR: no debes modificarlo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from engine.mundo import DESPLAZAMIENTOS, Celda, Mundo


# ---------------------------------------------------------------------------
# Acciones
# ---------------------------------------------------------------------------

class Accion(Enum):
    ARRIBA = "arriba"
    ABAJO = "abajo"
    IZQUIERDA = "izquierda"
    DERECHA = "derecha"
    LANZAR_ARRIBA = "lanzar_arriba"
    LANZAR_ABAJO = "lanzar_abajo"
    LANZAR_IZQUIERDA = "lanzar_izquierda"
    LANZAR_DERECHA = "lanzar_derecha"
    SALIR = "salir"

    def __repr__(self) -> str:
        return f"Accion.{self.name}"


MOVIMIENTOS: dict[Accion, tuple[int, int]] = {
    Accion.ARRIBA: DESPLAZAMIENTOS["arriba"],
    Accion.ABAJO: DESPLAZAMIENTOS["abajo"],
    Accion.IZQUIERDA: DESPLAZAMIENTOS["izquierda"],
    Accion.DERECHA: DESPLAZAMIENTOS["derecha"],
}

LANZAMIENTOS: dict[Accion, tuple[int, int]] = {
    Accion.LANZAR_ARRIBA: DESPLAZAMIENTOS["arriba"],
    Accion.LANZAR_ABAJO: DESPLAZAMIENTOS["abajo"],
    Accion.LANZAR_IZQUIERDA: DESPLAZAMIENTOS["izquierda"],
    Accion.LANZAR_DERECHA: DESPLAZAMIENTOS["derecha"],
}


def destino(celda: Celda, accion: Accion) -> Celda:
    """Celda adyacente a *celda* en la dirección de *accion* (movimiento o lanzamiento)."""
    df, dc = MOVIMIENTOS.get(accion) or LANZAMIENTOS[accion]
    return (celda[0] + df, celda[1] + dc)


def accion_hacia(origen: Celda, vecina: Celda, lanzar: bool = False) -> Accion:
    """Acción que mueve (o lanza la antorcha) de *origen* a la celda adyacente *vecina*."""
    delta = (vecina[0] - origen[0], vecina[1] - origen[1])
    tabla = LANZAMIENTOS if lanzar else MOVIMIENTOS
    for accion, d in tabla.items():
        if d == delta:
            return accion
    raise ValueError(f"{vecina} no es adyacente a {origen}.")


# ---------------------------------------------------------------------------
# Percepción y observación
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Percepto:
    corriente: bool = False
    siseo: bool = False
    luz: bool = False
    pared_arriba: bool = False
    pared_abajo: bool = False
    pared_izquierda: bool = False
    pared_derecha: bool = False
    chillido: bool = False

    def como_lista(self) -> list[bool]:
        """[corriente, siseo, luz, pared↑, pared↓, pared←, pared→, chillido]"""
        return [self.corriente, self.siseo, self.luz, self.pared_arriba,
                self.pared_abajo, self.pared_izquierda, self.pared_derecha,
                self.chillido]

    def __repr__(self) -> str:
        nombres = ["corriente", "siseo", "luz", "pared↑", "pared↓", "pared←",
                   "pared→", "chillido"]
        activos = [n for n, v in zip(nombres, self.como_lista()) if v]
        return f"Percepto({', '.join(activos) if activos else 'nada'})"


@dataclass(frozen=True)
class Observacion:
    """Todo lo que el agente sabe tras cada paso (no incluye el mapa oculto)."""
    posicion: Celda
    percepto: Percepto
    rescatada: bool          # ¿van ya con nosotros TODOS los perdidos (la Dra. Vega)?
    antorcha: bool           # ¿conservamos la antorcha?
    tamano: int              # el templo es tamano × tamano
    escombros: frozenset     # el plano antiguo SÍ muestra los escombros
    paso: int = 0
    pendientes: int = 0      # perdidos que quedan por rescatar
    n_fosos: int = 3         # el plano indica cuántos fosos hay


# ---------------------------------------------------------------------------
# Resultado de una partida
# ---------------------------------------------------------------------------

@dataclass
class Resultado:
    exito: bool              # salió del templo con todos los perdidos
    muerto: bool
    motivo: str              # 'exito', 'foso', 'serpiente', 'sin_vega', 'abandono', 'limite'
    coste: int
    pasos: int
    rescatada: bool
    acciones: list = field(default_factory=list)

    @property
    def puntuacion(self) -> int:
        return (1000 if self.exito else 0) - (1000 if self.muerto else 0) - self.coste


# ---------------------------------------------------------------------------
# Estado dinámico de una partida
# ---------------------------------------------------------------------------

class Juego:
    """Simulador del templo.  El agente solo ve Observaciones, nunca el Mundo."""

    def __init__(self, mundo: Mundo, max_pasos: int = 500) -> None:
        self.mundo = mundo
        self.max_pasos = max_pasos
        self.posicion: Celda = mundo.inicio
        self.rescatados: set = set()
        self.antorcha = True
        self.serpiente_presente = True
        self.chillido = False
        self.coste = 0
        self.pasos = 0
        self.terminado = False
        self.exito = False
        self.muerto = False
        self.motivo = ""
        self.visitadas: set = {mundo.inicio}
        self.acciones: list = []

    @property
    def rescatada(self) -> bool:
        """¿Se ha rescatado ya a todos los perdidos?"""
        return self.rescatados == set(self.mundo.perdidos)

    # ------------------------------------------------------------------ percepción
    def percepto(self) -> Percepto:
        m, p = self.mundo, self.posicion
        vec = m.vecinos(p)
        f, c = p
        return Percepto(
            corriente=any(v in m.fosos for v in vec),
            siseo=self.serpiente_presente and m.serpiente in vec,
            luz=(m.salida == p or m.salida in vec),
            pared_arriba=(f == 1 and not m.toroidal),
            pared_abajo=(f == m.tamano and not m.toroidal),
            pared_izquierda=(c == 1 and not m.toroidal),
            pared_derecha=(c == m.tamano and not m.toroidal),
            chillido=self.chillido,
        )

    def observacion(self) -> Observacion:
        return Observacion(self.posicion, self.percepto(), self.rescatada,
                           self.antorcha, self.mundo.tamano, self.mundo.escombros,
                           self.pasos, len(self.mundo.perdidos) - len(self.rescatados),
                           len(self.mundo.fosos))

    # ------------------------------------------------------------------ dinámica
    def ejecutar(self, accion: Optional[Accion]) -> Observacion:
        """Aplica *accion* y devuelve la nueva observación.  None = abandonar."""
        if self.terminado:
            raise RuntimeError("La partida ya ha terminado.")
        self.chillido = False
        self.pasos += 1
        self.acciones.append(accion)
        m = self.mundo

        if accion is None:
            self._terminar(False, "abandono")
        elif not isinstance(accion, Accion):
            raise TypeError(f"El agente devolvió {accion!r}, que no es una Accion.")
        elif accion in MOVIMIENTOS:
            nueva = m.envolver(destino(self.posicion, accion))
            if not m.dentro(nueva):
                self.coste += 1                     # choca contra la pared
            else:
                self.posicion = nueva
                self.coste += m.coste(nueva)
                self.visitadas.add(nueva)
                if nueva in m.fosos:
                    self.muerto = True
                    self._terminar(False, "foso")
                elif self.serpiente_presente and nueva == m.serpiente:
                    self.muerto = True
                    self._terminar(False, "serpiente")
                elif nueva in m.perdidos:
                    self.rescatados.add(nueva)
        elif accion in LANZAMIENTOS:
            self.coste += 1
            if self.antorcha:
                self.antorcha = False
                objetivo = m.envolver(destino(self.posicion, accion))
                if self.serpiente_presente and objetivo == m.serpiente:
                    self.serpiente_presente = False
                    self.chillido = True
        elif accion is Accion.SALIR:
            self.coste += 1
            if self.posicion == m.salida:
                if self.rescatada:
                    self._terminar(True, "exito")
                else:
                    self._terminar(False, "sin_vega")

        if not self.terminado and self.pasos >= self.max_pasos:
            self._terminar(False, "limite")
        return self.observacion()

    def _terminar(self, exito: bool, motivo: str) -> None:
        self.terminado = True
        self.exito = exito
        self.motivo = motivo

    def resultado(self) -> Resultado:
        return Resultado(self.exito, self.muerto, self.motivo, self.coste,
                         self.pasos, self.rescatada, list(self.acciones))


# ---------------------------------------------------------------------------
# Bucle de partida
# ---------------------------------------------------------------------------

class Agente:
    """Interfaz común de todos los agentes."""

    def actuar(self, obs: Observacion) -> Optional[Accion]:
        """Recibe la observación actual y devuelve la acción a ejecutar
        (o None para abandonar la partida)."""
        raise NotImplementedError


def ejecutar_partida(mundo: Mundo, agente: Agente, max_pasos: int = 500,
                     display=None) -> Resultado:
    """Juega una partida completa de *agente* en *mundo* y devuelve el Resultado.

    *display* (opcional) es un objeto con métodos inicializar(juego),
    actualizar(juego) y final(juego) — p. ej. engine.gui.VisorTk o
    engine.texto.VisorTexto.
    """
    juego = Juego(mundo, max_pasos)
    obs = juego.observacion()
    if display is not None:
        display.inicializar(juego)
    while not juego.terminado:
        accion = agente.actuar(obs)
        obs = juego.ejecutar(accion)
        if display is not None:
            display.actualizar(juego)
    if display is not None:
        display.final(juego)
    return juego.resultado()
