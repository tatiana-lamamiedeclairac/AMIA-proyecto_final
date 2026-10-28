"""
agente/problema.py — PARTE 2a: formulación de los problemas de búsqueda.

Los algoritmos (bfs, dfs, ucs, astar) ya están hechos en engine/busqueda.py:
vuestro trabajo es FORMULAR bien los problemas.

ProblemaRescate  — el mapa completo es CONOCIDO.  Hay que encontrar la secuencia
                   de acciones de menor coste que rescata a TODOS los perdidos
                   (mundo.perdidos: la Dra. Vega y, en las expediciones, sus
                   ayudantes) y sale del templo (el plan debe TERMINAR con
                   Accion.SALIR, que solo tiene éxito con todos rescatados).  El
                   diseño del ESTADO es parte del ejercicio: debe recoger todo
                   lo que cambia durante la partida y afecta a lo que se puede
                   hacer después.  Los estados deben ser hashables (tuplas).

ProblemaRuta     — ir desde una celda hasta cualquiera de un conjunto de celdas
                   objetivo pisando solo celdas permitidas.  Lo usará el agente
                   lógico de la Parte 3 para desplazarse por las celdas seguras.

Costes (los mismos que el motor): moverse cuesta el coste de la celda de destino
(1, o 3 con escombros); lanzar la antorcha y SALIR cuestan 1.

Útiles del motor: Mundo (mundo.dentro, mundo.coste, mundo.es_mortal,
mundo.fosos, mundo.serpiente, mundo.perdidos, mundo.salida, mundo.inicio),
MOVIMIENTOS, LANZAMIENTOS y destino(celda, accion).

Templo TOROIDAL (mundo.toroidal): no hay paredes, y quien sale por un borde
aparece por el opuesto.  destino() no lo sabe: mundo.envolver(celda) convierte
la celda resultante en la equivalente dentro de la rejilla (en un templo normal
la deja igual).
"""

from __future__ import annotations

from engine.busqueda_base import ProblemaBusqueda
from engine.juego import LANZAMIENTOS, MOVIMIENTOS, Accion, destino
from engine.mundo import COSTE_ESCOMBROS, COSTE_NORMAL, Celda, Mundo


class ProblemaRescate(ProblemaBusqueda):
    """
    TODO Parte 2a: documentad aquí vuestra representación del estado.
    """

    def __init__(self, mundo: Mundo) -> None:
        self.mundo = mundo

    def estado_inicial(self):
        raise NotImplementedError("TODO Parte 2a: ProblemaRescate.estado_inicial")

    def es_objetivo(self, estado) -> bool:
        raise NotImplementedError("TODO Parte 2a: ProblemaRescate.es_objetivo")

    def sucesores(self, estado):
        """Lista de (accion, estado_siguiente, coste).  No generéis acciones que
        maten al arqueólogo."""
        raise NotImplementedError("TODO Parte 2a: ProblemaRescate.sucesores")


class ProblemaRuta(ProblemaBusqueda):
    """
    Ir de *inicio* a cualquier celda de *objetivos* moviéndose solo por celdas
    de *permitidas* (el inicio y los objetivos se consideran permitidos).
    El estado es la celda actual; las acciones, movimientos; el coste, el de
    la celda de destino según *escombros*.
    """

    def __init__(self, inicio: Celda, objetivos, permitidas, escombros=frozenset()) -> None:
        self.inicio = inicio
        self.objetivos = set(objetivos)
        self.permitidas = set(permitidas) | self.objetivos | {inicio}
        self.escombros = escombros

    def estado_inicial(self):
        raise NotImplementedError("TODO Parte 2a: ProblemaRuta.estado_inicial")

    def es_objetivo(self, estado) -> bool:
        raise NotImplementedError("TODO Parte 2a: ProblemaRuta.es_objetivo")

    def sucesores(self, estado):
        raise NotImplementedError("TODO Parte 2a: ProblemaRuta.sucesores")
