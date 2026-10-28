"""
engine/texto.py — visualización en modo texto (terminal), sin GUI.

Parte 4 (VisorExpedicionTexto):  I / L  indy / lara   H herido   X atrapado

Leyenda:  @ arqueólogo   F foso   S serpiente   V Dra. Vega   E salida
          * escombros    · celda visitada      ? celda sin explorar   . celda libre (mapa revelado)

Este fichero es parte del MOTOR: no debes modificarlo.
"""

from __future__ import annotations

import time

from engine.juego import Juego


def dibujar(juego: Juego, revelar: bool = False) -> str:
    m = juego.mundo
    lineas = ["    " + " ".join(f"{c}" for c in range(1, m.tamano + 1))]
    for f in range(1, m.tamano + 1):
        fila = []
        for c in range(1, m.tamano + 1):
            celda = (f, c)
            visible = revelar or celda in juego.visitadas
            if celda == juego.posicion:
                ch = "@"
            elif visible and celda in m.fosos:
                ch = "F"
            elif visible and celda == m.serpiente and juego.serpiente_presente:
                ch = "S"
            elif visible and celda in m.perdidos and celda not in juego.rescatados:
                ch = "V"
            elif visible and celda == m.salida:
                ch = "E"
            elif celda in m.escombros:
                ch = "*"
            elif celda in juego.visitadas:
                ch = "·"
            else:
                ch = "." if revelar else "?"
            fila.append(ch)
        lineas.append(f"{f:>2}  " + " ".join(fila))
    p = juego.percepto()
    lineas.append(f"paso {juego.pasos}  coste {juego.coste}  "
                  f"rescatados: {len(juego.rescatados)}/{len(m.perdidos)}  "
                  f"antorcha: {'sí' if juego.antorcha else 'no'}  {p}")
    return "\n".join(lineas)


class VisorTexto:
    """Display para ejecutar_partida que imprime el templo en la terminal."""

    def __init__(self, pausa: float = 0.0, revelar: bool = False) -> None:
        self.pausa = pausa
        self.revelar = revelar

    def inicializar(self, juego: Juego) -> None:
        print(dibujar(juego, self.revelar), end="\n\n")

    def actualizar(self, juego: Juego) -> None:
        print(f"> {juego.acciones[-1]}")
        print(dibujar(juego, self.revelar), end="\n\n")
        if self.pausa:
            time.sleep(self.pausa)

    def final(self, juego: Juego) -> None:
        print(dibujar(juego, revelar=True))
        print(f"FIN: {juego.motivo}  (coste {juego.coste}, pasos {juego.pasos})")


# ---------------------------------------------------------------------------
# Parte 4: la expedición
# ---------------------------------------------------------------------------

def dibujar_expedicion(e) -> str:
    m = e.mundo
    pendientes = e.pendientes()
    activos = {pos: nombre[0].upper() for nombre, pos in e.posiciones.items()
               if nombre not in e.fuera}
    lineas = ["    " + " ".join(f"{c}" for c in range(1, m.tamano + 1))]
    for f in range(1, m.tamano + 1):
        fila = []
        for c in range(1, m.tamano + 1):
            celda = (f, c)
            if celda in activos:
                ch = activos[celda]
            elif celda in m.fosos:
                ch = "F"
            elif celda == m.serpiente and e.serpiente_presente:
                ch = "S"
            elif celda in pendientes:
                ch = "H" if celda in m.heridos else "X" if celda in m.atrapados else "V"
            elif celda == m.salida:
                ch = "E"
            elif celda in m.escombros:
                ch = "*"
            else:
                ch = "."
            fila.append(ch)
        lineas.append(f"{f:>2}  " + " ".join(fila))
    lineas.append("  ".join(f"{n}: coste {e.costes[n]}, {len(e.rescatados[n])} rescatados"
                            + (" (fuera)" if n in e.fuera else "") for n in e.posiciones))
    return "\n".join(lineas)


class VisorExpedicionTexto:
    """Display para engine.expedicion.ejecutar_expedicion en la terminal."""

    def __init__(self, pausa: float = 0.0) -> None:
        self.pausa = pausa

    def inicializar(self, e) -> None:
        print(dibujar_expedicion(e), end="\n\n")

    def actualizar(self, e) -> None:
        nombre, accion = e.ultimo
        print(f"> {nombre}: {accion.name if accion else 'se rinde'}")
        print(dibujar_expedicion(e), end="\n\n")
        if self.pausa:
            time.sleep(self.pausa)

    def final(self, e, r) -> None:
        print(f"FIN: {r.motivo}  (makespan {r.makespan}, costes {r.costes})")
