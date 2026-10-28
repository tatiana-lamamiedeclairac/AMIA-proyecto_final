"""
engine/asp.py — conexión entre el agente y vuestro programa ASP (clingo).

ConocimientoASP guarda lo que el agente ha observado como HECHOS ASP, lo junta
con vuestro programa (agente/templo.lp) y le pregunta a clingo:

  * cautas()  átomos ciertos en TODOS los modelos  → lo que se puede DEDUCIR
              (es la consecuencia lógica: KB ⊨ átomo)
  * bravas()  átomos ciertos en ALGÚN modelo       → lo que es POSIBLE

Uso típico (ya está hecho en AgenteLogico):

    kb = ConocimientoASP()                  # lee agente/templo.lp
    kb.observar(obs, ultima_accion)         # tras cada paso
    kb.seguras()                            # celdas con segura(F,C) cauto
    ("foso", (1, 3)) in kb.cautas()         # ¿se deduce que hay foso en (1,3)?

Hechos que se añaden (ver la cabecera de agente/templo.lp):
    tamano/1, num_fosos/1, visitada/2, percibe/3, no_percibe/3, antorcha/3,
    huida/0, no_es_salida/2

Este fichero es parte del MOTOR: no debes modificarlo.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from engine.juego import LANZAMIENTOS, Accion, Observacion, destino
from engine.mundo import Celda, vecinos

try:
    import clingo
except ImportError as e:  # pragma: no cover
    raise ImportError("Falta clingo: pip install clingo") from e

RUTA_PROGRAMA = Path(__file__).resolve().parent.parent / "agente" / "templo.lp"
PERCEPCIONES = ("corriente", "siseo", "luz")


class ProgramaInconsistente(Exception):
    """El programa ASP, con los hechos observados, no tiene ningún modelo."""


class ConocimientoASP:

    def __init__(self, ruta_programa: Optional[Path] = None) -> None:
        ruta = Path(ruta_programa) if ruta_programa else RUTA_PROGRAMA
        self.programa = ruta.read_text(encoding="utf-8")
        self.hechos: list[str] = []
        self.tamano: Optional[int] = None
        self.visitadas: set = set()
        self.serpiente_huida = False
        self.antorcha = True
        self._pos: Optional[Celda] = None
        self._cache: dict = {}
        self.llamadas = 0

    # ------------------------------------------------------------------ hechos
    def anadir(self, hecho: str) -> None:
        """Añade un hecho ASP (sin el punto final), p. ej. 'visitada(2,3)'."""
        self.hechos.append(hecho + ".")
        self._cache.clear()

    def observar(self, obs: Observacion, ultima_accion: Optional[Accion] = None) -> None:
        """Traduce la observación (y el resultado de la última acción) a hechos."""
        if self.tamano is None:
            self.tamano = obs.tamano
            self.anadir(f"tamano({obs.tamano})")
            self.anadir(f"num_fosos({obs.n_fosos})")
        anterior, self._pos = self._pos, obs.posicion
        p = obs.percepto

        if ultima_accion in LANZAMIENTOS and self.antorcha and not self.serpiente_huida:
            f, c = destino(anterior, ultima_accion)
            if 1 <= f <= self.tamano and 1 <= c <= self.tamano:
                self.anadir(f"antorcha({f},{c},{'si' if p.chillido else 'no'})")
                if p.chillido:
                    self.serpiente_huida = True
                    self.anadir("huida")
        if ultima_accion is Accion.SALIR:
            self.anadir(f"no_es_salida({obs.posicion[0]},{obs.posicion[1]})")
        self.antorcha = obs.antorcha

        if obs.posicion not in self.visitadas:
            self.visitadas.add(obs.posicion)
            f, c = obs.posicion
            self.anadir(f"visitada({f},{c})")
            valores = {"corriente": p.corriente, "luz": p.luz}
            if not self.serpiente_huida:          # tras huir, el siseo ya no informa
                valores["siseo"] = p.siseo
            for nombre, valor in valores.items():
                self.anadir(f"{'percibe' if valor else 'no_percibe'}({nombre},{f},{c})")

    # ------------------------------------------------------------------ consultas
    def _consecuencias(self, modo: str) -> set:
        if modo in self._cache:
            return self._cache[modo]
        self.llamadas += 1
        ctl = clingo.Control([f"--enum-mode={modo}", "0", "--warn=none"])
        ctl.add("base", [], self.programa + "\n" + "\n".join(self.hechos))
        ctl.ground([("base", [])])
        ultimo = None
        with ctl.solve(yield_=True) as manejador:
            for modelo in manejador:
                ultimo = modelo.symbols(shown=True)
        if ultimo is None:
            raise ProgramaInconsistente(
                "templo.lp no tiene ningún modelo con lo observado: revisad las reglas.")
        atomos = {(s.name, tuple(a.number for a in s.arguments)) for s in ultimo}
        self._cache[modo] = atomos
        return atomos

    def cautas(self) -> set:
        """{(predicado, (F, C)), ...} ciertos en TODOS los modelos."""
        return self._consecuencias("cautious")

    def bravas(self) -> set:
        """{(predicado, (F, C)), ...} ciertos en ALGÚN modelo."""
        return self._consecuencias("brave")

    def seguras(self) -> set:
        """Celdas que se DEDUCE que no tienen peligro."""
        return {args for pred, args in self.cautas() if pred == "segura"}

    def es_segura(self, celda: Celda) -> bool:
        return ("segura", tuple(celda)) in self.cautas()

    def deducciones(self) -> dict:
        """Etiquetas para la GUI sobre las celdas visitadas y su frontera:
        '✓' segura · 'F!'/'F?' foso deducido/posible · 'S!'/'S?' · 'E!'/'E?'."""
        out: dict = {}
        if self.tamano is None:
            return out
        cautas, bravas = self.cautas(), self.bravas()
        luces = {v for v in self.visitadas if f"percibe(luz,{v[0]},{v[1]})." in self.hechos}
        cerca_luz = {n for v in luces for n in [v, *vecinos(v, self.tamano)]}
        frontera = {n for v in self.visitadas for n in vecinos(v, self.tamano)}
        for c in self.visitadas | frontera:
            et = []
            if ("segura", c) in cautas:
                et.append("✓")
            else:
                peligros = [("foso", "F")] + ([] if self.serpiente_huida else [("serpiente", "S")])
                for pred, letra in peligros:
                    if (pred, c) in cautas:
                        et.append(letra + "!")
                    elif (pred, c) in bravas:
                        et.append(letra + "?")
            if ("salida", c) in cautas:
                et.append("E!")
            elif c in cerca_luz and ("salida", c) in bravas:
                et.append("E?")
            out[c] = et
        return out
