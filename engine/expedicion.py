"""
engine/expedicion.py — PARTE 4: «la expedición» (multiagente).

El equipo de la Dra. Vega (varios perdidos) está repartido por el templo y
entran a buscarlo DOS arqueólogos.  El mapa es CONOCIDO (como en la Parte 2a).
Cada arqueólogo lleva un equipo distinto, que es su ROL:

    indy  — botiquín: es el único que puede rescatar a un perdido HERIDO ('H')
    lara  — pico:     es la única que puede liberar a un perdido ATRAPADO ('X')

Los perdidos normales ('V') los puede rescatar cualquiera.  Además, cada
arqueólogo puede sacar como mucho a CAPACIDAD perdidos.

La coordinación tiene tres pasos:

  1. clingo (agente/expedicion.lp) genera TODOS los repartos válidos de
     perdidos entre arqueólogos: repartos_validos(mundo).
  2. Python (agente/coordinador.py) calcula con A* lo que tardaría cada
     arqueólogo con su parte y elige el reparto que antes termina.
  3. El motor ejecuta los dos planes a la vez: ejecutar_expedicion(...).

Simulación (eventos discretos): el reloj de cada arqueólogo es su coste
acumulado y siempre actúa el que va más retrasado (empate: indy primero).  Así,
si los dos van a por el mismo perdido, se lo lleva el que llega antes.  Un
arqueólogo solo rescata a un perdido si su política lo QUIERE (en un plan
coordinado, solo a los suyos), si su equipo se lo permite y si le queda
capacidad.  La expedición termina cuando el ÚLTIMO arqueólogo sale; esa
duración (el coste del más lento) es el MAKESPAN.

Hechos ASP que añade el motor (ver agente/expedicion.lp):
    arqueologo(indy). arqueologo(lara).
    equipo(indy,botiquin). equipo(lara,pico).
    perdido(p1). ...            (numerados por filas: p1 es el de más arriba)
    herido(P). atrapado(P).
    capacidad(K).

Este fichero es parte del MOTOR: no debes modificarlo.
"""

from __future__ import annotations

import heapq
import random
from collections import deque
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional

from engine.asp import ProgramaInconsistente
from engine.juego import LANZAMIENTOS, MOVIMIENTOS, Accion, accion_hacia, destino
from engine.mundo import Celda, Mundo, generar_mundo

try:
    import clingo
except ImportError as e:  # pragma: no cover
    raise ImportError("Falta clingo: pip install clingo") from e

ARQUEOLOGOS = ("indy", "lara")
EQUIPO = {"indy": "botiquin", "lara": "pico"}
CAPACIDAD = 3
RUTA_PROGRAMA = Path(__file__).resolve().parent.parent / "agente" / "expedicion.lp"


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

def puede_rescatar(nombre: str, mundo: Mundo, celda: Celda) -> bool:
    """¿El equipo de *nombre* le permite rescatar al perdido de *celda*?"""
    if celda in mundo.heridos and EQUIPO[nombre] != "botiquin":
        return False
    if celda in mundo.atrapados and EQUIPO[nombre] != "pico":
        return False
    return True


# ---------------------------------------------------------------------------
# Paso 1: clingo genera los repartos válidos
# ---------------------------------------------------------------------------

def ids_perdidos(mundo: Mundo) -> dict[str, Celda]:
    """{'p1': celda, 'p2': celda, ...}, numerados por filas y luego columnas."""
    return {f"p{i}": c for i, c in enumerate(sorted(mundo.perdidos), start=1)}


def hechos_expedicion(mundo: Mundo, capacidad: int = CAPACIDAD) -> list[str]:
    """Hechos ASP que describen la expedición (los añade el motor)."""
    hechos = [f"arqueologo({n})." for n in ARQUEOLOGOS]
    hechos += [f"equipo({n},{e})." for n, e in EQUIPO.items()]
    for pid, celda in ids_perdidos(mundo).items():
        hechos.append(f"perdido({pid}).")
        if celda in mundo.heridos:
            hechos.append(f"herido({pid}).")
        if celda in mundo.atrapados:
            hechos.append(f"atrapado({pid}).")
    hechos.append(f"capacidad({capacidad}).")
    return hechos


def modelos_asp(programa: str, hechos: list[str]) -> list[set]:
    """TODOS los answer sets de *programa* + *hechos*, como conjuntos de
    átomos visibles (#show) en forma (predicado, (arg1, arg2, ...))."""
    ctl = clingo.Control(["0", "--warn=none"])
    ctl.add("base", [], programa + "\n" + "\n".join(hechos))
    ctl.ground([("base", [])])
    modelos = []
    with ctl.solve(yield_=True) as manejador:
        for modelo in manejador:
            modelos.append({(s.name, tuple(str(a) for a in s.arguments))
                            for s in modelo.symbols(shown=True)})
    return modelos


def repartos_validos(mundo: Mundo, capacidad: int = CAPACIDAD,
                     ruta_programa: Optional[Path] = None) -> list[dict]:
    """
    Pregunta a clingo por todos los repartos válidos.  Cada reparto es un dict
    {arqueólogo: frozenset de celdas de los perdidos que rescata}.

    Lanza ProgramaInconsistente si no hay ninguno (nadie puede organizar la
    expedición con esas reglas).
    """
    ruta = Path(ruta_programa) if ruta_programa else RUTA_PROGRAMA
    ids = ids_perdidos(mundo)
    modelos = modelos_asp(ruta.read_text(encoding="utf-8"), hechos_expedicion(mundo, capacidad))
    if not modelos:
        raise ProgramaInconsistente(
            "expedicion.lp no tiene ningún modelo: no hay ningún reparto válido.")
    repartos = []
    for modelo in modelos:
        reparto = {n: set() for n in ARQUEOLOGOS}
        for pred, args in modelo:
            if pred == "rescata" and len(args) == 2 and args[0] in reparto and args[1] in ids:
                reparto[args[0]].add(ids[args[1]])
        repartos.append({n: frozenset(s) for n, s in reparto.items()})
    repartos.sort(key=lambda r: [sorted(r[n]) for n in ARQUEOLOGOS])
    return repartos


# ---------------------------------------------------------------------------
# Generador de expediciones
# ---------------------------------------------------------------------------

def _alcanzables(mundo: Mundo) -> set:
    """Celdas alcanzables desde la entrada sin pisar fosos ni la serpiente."""
    vistos, cola = {mundo.inicio}, deque([mundo.inicio])
    while cola:
        c = cola.popleft()
        for v in mundo.vecinos(c):
            if v not in vistos and not mundo.es_mortal(v):
                vistos.add(v)
                cola.append(v)
    return vistos


def generar_expedicion(semilla: int | None = None, n_perdidos: int = 5,
                       n_heridos: int = 1, n_atrapados: int = 1) -> Mundo:
    """
    Templo aleatorio para la Parte 4: *n_perdidos* perdidos, de los que
    *n_heridos* están heridos y *n_atrapados* atrapados (bajo escombros).
    Todos los perdidos y la salida son alcanzables sin pisar fosos ni la
    serpiente.  La misma semilla produce siempre la misma expedición.
    """
    rng = random.Random(semilla)
    for _ in range(1000):
        base = generar_mundo(rng.randrange(10**9), n_perdidos=n_perdidos, resoluble=False)
        if not (base.perdidos | {base.salida}) <= _alcanzables(base):
            continue
        orden = sorted(base.perdidos)
        rng.shuffle(orden)
        heridos = frozenset(orden[:n_heridos])
        atrapados = frozenset(orden[n_heridos:n_heridos + n_atrapados])
        return replace(base, heridos=heridos, atrapados=atrapados,
                       escombros=base.escombros | atrapados)
    raise RuntimeError("No se ha podido generar la expedición.")


# ---------------------------------------------------------------------------
# Simulación
# ---------------------------------------------------------------------------

@dataclass
class EstadoExpedicion:
    """Lo que ve el display durante la simulación."""

    mundo: Mundo
    capacidad: int
    posiciones: dict = field(default_factory=dict)
    costes: dict = field(default_factory=dict)
    rescatados: dict = field(default_factory=dict)    # nombre -> set de celdas
    antorchas: dict = field(default_factory=dict)
    fuera: set = field(default_factory=set)
    muertos: set = field(default_factory=set)
    rendidos: set = field(default_factory=set)
    serpiente_presente: bool = True
    pasos: int = 0
    ultimo: Optional[tuple] = None                    # (nombre, accion)
    reparto: Optional[dict] = None                    # solo con coordinación

    def pendientes(self) -> set:
        rescatados = set().union(*self.rescatados.values())
        return set(self.mundo.perdidos) - rescatados

    def activos(self) -> list[str]:
        return [n for n in ARQUEOLOGOS
                if n not in self.fuera and n not in self.muertos and n not in self.rendidos]


@dataclass
class ResultadoExpedicion:
    exito: bool
    motivo: str          # 'exito' | 'muerte' | 'sin_rescatar' | 'abandono' | 'limite'
    costes: dict
    rescatados: dict
    sin_rescatar: set
    muertos: set
    pasos: int

    @property
    def makespan(self) -> int:
        """Duración de la expedición: el coste del arqueólogo más lento."""
        return max(self.costes.values())


class PoliticaPlan:
    """Cada arqueólogo ejecuta su plan, calculado de antemano, y solo rescata a
    los perdidos que le asigna el reparto."""

    def __init__(self, planes: dict, reparto: dict) -> None:
        self.planes = {n: list(p or []) for n, p in planes.items()}
        self.reparto = reparto

    def quiere(self, nombre: str, celda: Celda) -> bool:
        return celda in self.reparto.get(nombre, ())

    def decidir(self, estado: EstadoExpedicion, nombre: str) -> Optional[Accion]:
        plan = self.planes.get(nombre)
        return plan.pop(0) if plan else None


class PoliticaEgoista:
    """
    Agentes SIN coordinación (referencia): cada arqueólogo va a por el perdido
    pendiente más cercano que su equipo le permite rescatar, sin saber nada de
    lo que hace el otro, y rescata a cualquiera que se encuentre por el camino.
    Cuando ya no puede rescatar a nadie más (o va lleno), se va a la salida.
    No usa la antorcha.
    """

    def quiere(self, nombre: str, celda: Celda) -> bool:
        return True

    def decidir(self, estado: EstadoExpedicion, nombre: str) -> Optional[Accion]:
        m, pos = estado.mundo, estado.posiciones[nombre]
        objetivos = set()
        if len(estado.rescatados[nombre]) < estado.capacidad:
            objetivos = {c for c in estado.pendientes() if puede_rescatar(nombre, m, c)}
        camino = _camino_mas_barato(m, pos, objetivos, estado.serpiente_presente) if objetivos else None
        if camino is None:                       # nada más que hacer: a la salida
            if pos == m.salida:
                return Accion.SALIR
            camino = _camino_mas_barato(m, pos, {m.salida}, estado.serpiente_presente)
            if camino is None:
                return None
        return accion_hacia(pos, camino[1])


def _camino_mas_barato(mundo: Mundo, origen: Celda, objetivos: set,
                       serpiente_presente: bool) -> Optional[list]:
    """Dijkstra: camino de menor coste de *origen* al objetivo más cercano."""
    frontera = [(0, origen)]
    padres, coste = {origen: None}, {origen: 0}
    while frontera:
        g, c = heapq.heappop(frontera)
        if g > coste[c]:
            continue
        if c in objetivos:
            camino = [c]
            while padres[camino[-1]] is not None:
                camino.append(padres[camino[-1]])
            return camino[::-1]
        for v in mundo.vecinos(c):
            if mundo.es_mortal(v, serpiente_presente):
                continue
            g2 = g + mundo.coste(v)
            if g2 < coste.get(v, float("inf")):
                coste[v], padres[v] = g2, c
                heapq.heappush(frontera, (g2, v))
    return None


def ejecutar_expedicion(mundo: Mundo, politica, capacidad: int = CAPACIDAD,
                        display=None, max_pasos: int = 400,
                        reparto: Optional[dict] = None) -> ResultadoExpedicion:
    """Simula la expedición con *politica* (PoliticaPlan o PoliticaEgoista)."""
    e = EstadoExpedicion(mundo, capacidad, reparto=reparto)
    for n in ARQUEOLOGOS:
        e.posiciones[n], e.costes[n], e.rescatados[n], e.antorchas[n] = mundo.inicio, 0, set(), True
    if display:
        display.inicializar(e)
    while e.activos() and e.pasos < max_pasos:
        nombre = min(e.activos(), key=lambda n: (e.costes[n], ARQUEOLOGOS.index(n)))
        accion = politica.decidir(e, nombre)
        e.pasos += 1
        e.ultimo = (nombre, accion)
        if accion is None:
            e.rendidos.add(nombre)
        else:
            _aplicar(e, nombre, accion, politica)
        if display:
            display.actualizar(e)

    sin_rescatar = e.pendientes()
    if e.muertos:
        motivo = "muerte"
    elif e.activos():
        motivo = "limite"
    elif e.rendidos:
        motivo = "abandono"
    elif sin_rescatar:
        motivo = "sin_rescatar"
    else:
        motivo = "exito"
    r = ResultadoExpedicion(motivo == "exito", motivo, dict(e.costes),
                            {n: set(s) for n, s in e.rescatados.items()},
                            sin_rescatar, set(e.muertos), e.pasos)
    if display:
        display.final(e, r)
    return r


def _aplicar(e: EstadoExpedicion, nombre: str, accion: Accion, politica) -> None:
    m, pos = e.mundo, e.posiciones[nombre]
    if accion in MOVIMIENTOS:
        sig = destino(pos, accion)
        if not m.dentro(sig):
            e.costes[nombre] += 1                 # choca con la pared
            return
        e.posiciones[nombre] = sig
        e.costes[nombre] += m.coste(sig)
        if m.es_mortal(sig, e.serpiente_presente):
            e.muertos.add(nombre)
        elif (sig in e.pendientes() and politica.quiere(nombre, sig)
              and puede_rescatar(nombre, m, sig)
              and len(e.rescatados[nombre]) < e.capacidad):
            e.rescatados[nombre].add(sig)
    elif accion in LANZAMIENTOS:
        e.costes[nombre] += 1
        if e.antorchas[nombre]:
            e.antorchas[nombre] = False
            if destino(pos, accion) == m.serpiente:
                e.serpiente_presente = False
    elif accion is Accion.SALIR:
        e.costes[nombre] += 1
        if pos == m.salida:
            e.fuera.add(nombre)


# ---------------------------------------------------------------------------
# Todo junto: la expedición coordinada (usa vuestro agente/coordinador.py)
# ---------------------------------------------------------------------------

def jugar_coordinada(mundo: Mundo, capacidad: int = CAPACIDAD, display=None):
    """Clingo → coordinador → simulación.  Devuelve (repartos, reparto, resultado)."""
    from agente.coordinador import elegir_reparto, plan_individual
    repartos = repartos_validos(mundo, capacidad)
    reparto = elegir_reparto(mundo, repartos)
    planes = {n: plan_individual(mundo, reparto[n]) for n in ARQUEOLOGOS}
    resultado = ejecutar_expedicion(mundo, PoliticaPlan(planes, reparto), capacidad,
                                    display, reparto=reparto)
    return repartos, reparto, resultado
