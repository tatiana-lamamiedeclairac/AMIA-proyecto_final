"""
agente/agente_logico.py — PARTE 3: agente basado en conocimiento (ASP).

El conocimiento del templo está en agente/templo.lp.  El motor
(engine/asp.py, ConocimientoASP) convierte lo observado en hechos y pregunta a
clingo qué se puede deducir.  En cada paso:

  1. observar(obs, ultima_accion)  → kb.observar(...)          [PROPORCIONADO]
  2. decidir()                     → [TODO] elegir la acción SIN arriesgar nunca,
                                     desplazándose con A* (engine.busqueda) y
                                     ProblemaRuta solo por celdas seguras.

El mismo agente sirve de «asesor» en el modo manual: la GUI llama a observar()
con la acción que ha tecleado el jugador y muestra deducciones().
"""

from __future__ import annotations

from typing import Optional

from engine.asp import ConocimientoASP
from engine.busqueda import astar
from engine.juego import Accion, Agente, Observacion, accion_hacia
from engine.mundo import Celda, manhattan, vecinos

from agente.heuristicas import heuristica_ruta
from agente.problema import ProblemaRuta


class AgenteLogico(Agente):

    def __init__(self, usar_antorcha: bool = True) -> None:
        self.kb = ConocimientoASP()
        self.usar_antorcha = usar_antorcha
        self.pos: Optional[Celda] = None
        self.tamano: Optional[int] = None
        self.escombros: frozenset = frozenset()
        self.rescatada = False
        self.antorcha = True
        self._ultima: Optional[Accion] = None

    # ===================================================================== [PROPORCIONADO]
    def actuar(self, obs: Observacion) -> Optional[Accion]:
        self.observar(obs, self._ultima)
        self._ultima = self.decidir()
        return self._ultima

    def observar(self, obs: Observacion, ultima_accion: Optional[Accion] = None) -> None:
        self.kb.observar(obs, ultima_accion)
        self.pos, self.tamano, self.escombros = obs.posicion, obs.tamano, obs.escombros
        self.rescatada, self.antorcha = obs.rescatada, obs.antorcha

    @property
    def visitadas(self) -> set:
        return self.kb.visitadas

    def frontera(self) -> set:
        """Celdas no visitadas adyacentes a alguna visitada."""
        return {n for v in self.visitadas for n in vecinos(v, self.tamano)} - self.visitadas

    def celdas_seguras(self) -> set:
        """Celdas visitadas o de la frontera que se DEDUCE que son seguras."""
        return self.kb.seguras() & (self.visitadas | self.frontera())

    def deducciones(self) -> dict:
        return self.kb.deducciones()

    def _ruta(self, objetivos, seguras) -> Optional[Accion]:
        """Primera acción del camino más barato hasta alguno de los *objetivos*
        pisando solo *seguras* (None si no hay camino)."""
        if not objetivos:
            return None
        plan = astar(ProblemaRuta(self.pos, objetivos, seguras, self.escombros), heuristica_ruta)
        return plan[0] if plan else None

    # ===================================================================== decidir
    def decidir(self) -> Optional[Accion]:
        """
        Elige la siguiente acción SIN arriesgarse nunca.  Tenéis a mano:

          self.celdas_seguras()     celdas visitadas/frontera que se DEDUCEN seguras
          self.kb.cautas()          {(predicado, (F, C))} ciertos en TODOS los modelos
          self.kb.bravas()          {(predicado, (F, C))} ciertos en ALGÚN modelo
          self._ruta(objetivos, seguras)  primera acción del camino por celdas seguras
          self.pos, self.rescatada, self.antorcha, self.visitadas, self.frontera()

        Una estrategia posible:
          1. Con la Dra. Vega: si se deduce dónde está la salida, ir y SALIR; si
             no, probar SALIR en las celdas seguras donde la salida es posible.
          2. Si no, ir a la celda segura no visitada más cercana.
          3. Si no queda ninguna, usar la antorcha contra una celda bloqueada
             solo por la serpiente (accion_hacia(pos, celda, lanzar=True)).
          4. Si nada de lo anterior es posible, abandonar (None).
        """
        raise NotImplementedError("TODO Parte 3: AgenteLogico.decidir")
