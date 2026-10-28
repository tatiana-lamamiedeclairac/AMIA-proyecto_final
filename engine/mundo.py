"""
engine/mundo.py — el mapa (estático) del templo perdido.

El templo es una rejilla de n×n salas (n = 6 por defecto).  Las celdas se
identifican como (fila, columna), ambas empezando en 1; la fila 1 es la de
arriba y la columna 1 la de la izquierda.  El arqueólogo entra siempre por la
celda (1, 1).

Elementos del mapa (cada uno en una celda distinta):
  * 3 fosos de pinchos   ('F')  — muerte segura al entrar.
  * 1 serpiente gigante  ('S')  — dormida; muerte si se entra en su celda.
  * 1 salida al exterior ('E')  — hay que estar en ella para ejecutar SALIR.
  * la Dra. Vega         ('V')  — se rescata al pisar su celda.  En algunos mapas
                                   (Parte 2a) hay VARIOS exploradores perdidos
                                   ('V' repetida) y hay que rescatarlos a todos.
  * escombros            ('*')  — celda transitable pero cuesta 3 (en vez de 1).
  * Parte 4 (la expedición): un perdido HERIDO ('H') o ATRAPADO bajo escombros
    ('X').  Ambos cuentan como perdidos; la celda de un atrapado tiene además
    escombros.  Solo importan en la Parte 4, donde cada arqueólogo puede
    rescatar a unos u otros según su equipo (engine/expedicion.py).

Formato de texto de un mapa (una línea por fila, un carácter por celda):

    A.....
    ..F...
    .*..S.
    ...*..
    .F..V.
    ..F..E

'A' marca la entrada (solo informativa: siempre debe ser (1, 1)) y '.' una
celda libre.  Las líneas que empiezan por ';' son comentarios.

Templo TOROIDAL (variante de la Parte 2a, Mundo.toroidal = True): no hay
paredes; quien sale por un borde aparece por el opuesto, p. ej. ir a la
izquierda desde (3, 1) lleva a (3, n).  Mundo.envolver(celda) hace ese ajuste.

Este fichero es parte del MOTOR: no debes modificarlo.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

Celda = tuple[int, int]

# Orden canónico de las direcciones: arriba, abajo, izquierda, derecha.
DESPLAZAMIENTOS: dict[str, tuple[int, int]] = {
    "arriba": (-1, 0),
    "abajo": (1, 0),
    "izquierda": (0, -1),
    "derecha": (0, 1),
}

COSTE_NORMAL = 1
COSTE_ESCOMBROS = 3

_DIR_MAPAS = Path(__file__).resolve().parent.parent / "mapas"


@dataclass(frozen=True)
class Mundo:
    """Disposición completa (y oculta para el agente) de un templo."""

    tamano: int
    fosos: frozenset
    serpiente: Celda
    perdidos: frozenset      # exploradores que rescatar (la Dra. Vega y, a veces, más)
    salida: Celda
    escombros: frozenset = field(default_factory=frozenset)
    inicio: Celda = (1, 1)
    heridos: frozenset = field(default_factory=frozenset)     # Parte 4 ('H')
    atrapados: frozenset = field(default_factory=frozenset)   # Parte 4 ('X')
    toroidal: bool = False   # variante de la Parte 2a: los bordes se comunican

    @property
    def vega(self) -> Celda:
        """Celda de la Dra. Vega cuando es la única perdida (Partes 2b y 3)."""
        if len(self.perdidos) != 1:
            raise ValueError("Este templo tiene varios perdidos: usa mundo.perdidos.")
        return next(iter(self.perdidos))

    # ------------------------------------------------------------------ geometría
    def dentro(self, celda: Celda) -> bool:
        f, c = celda
        return 1 <= f <= self.tamano and 1 <= c <= self.tamano

    def envolver(self, celda: Celda) -> Celda:
        """En un templo toroidal, la celda equivalente dentro de la rejilla
        (p. ej. (3, 0) -> (3, n)); en uno normal, la misma celda."""
        if not self.toroidal:
            return celda
        n = self.tamano
        return ((celda[0] - 1) % n + 1, (celda[1] - 1) % n + 1)

    def vecinos(self, celda: Celda) -> list[Celda]:
        """Celdas adyacentes (distancia Manhattan 1) dentro del templo."""
        return vecinos(celda, self.tamano, self.toroidal)

    def celdas(self) -> list[Celda]:
        return todas_las_celdas(self.tamano)

    def coste(self, celda: Celda) -> int:
        """Coste de ENTRAR en *celda* (1 normal, 3 si tiene escombros)."""
        return COSTE_ESCOMBROS if celda in self.escombros else COSTE_NORMAL

    def es_mortal(self, celda: Celda, serpiente_presente: bool = True) -> bool:
        return celda in self.fosos or (serpiente_presente and celda == self.serpiente)

    # ------------------------------------------------------------------ texto
    @classmethod
    def desde_texto(cls, texto: str) -> "Mundo":
        filas = [ln.strip() for ln in texto.strip().splitlines()
                 if ln.strip() and not ln.strip().startswith(";")]
        n = len(filas)
        if any(len(f) != n for f in filas):
            raise ValueError("El mapa debe ser cuadrado (n filas de n caracteres).")
        fosos, escombros, perdidos, heridos, atrapados = set(), set(), set(), set(), set()
        serpiente = salida = None
        for i, fila in enumerate(filas, start=1):
            for j, ch in enumerate(fila, start=1):
                celda = (i, j)
                if ch == "F":
                    fosos.add(celda)
                elif ch == "S":
                    serpiente = celda
                elif ch == "V":
                    perdidos.add(celda)
                elif ch == "H":
                    perdidos.add(celda)
                    heridos.add(celda)
                elif ch == "X":
                    perdidos.add(celda)
                    atrapados.add(celda)
                    escombros.add(celda)
                elif ch == "E":
                    salida = celda
                elif ch == "*":
                    escombros.add(celda)
                elif ch in ".A":
                    pass
                else:
                    raise ValueError(f"Carácter desconocido {ch!r} en {celda}.")
        if serpiente is None or salida is None or not perdidos:
            raise ValueError("El mapa necesita una serpiente (S), al menos una V y una salida (E).")
        return cls(n, frozenset(fosos), serpiente, frozenset(perdidos), salida,
                   frozenset(escombros), heridos=frozenset(heridos),
                   atrapados=frozenset(atrapados))

    @classmethod
    def cargar(cls, nombre: str) -> "Mundo":
        """Carga un mapa de la carpeta mapas/ (con o sin extensión .txt) o una ruta."""
        ruta = Path(nombre)
        if not ruta.exists():
            ruta = _DIR_MAPAS / (nombre if nombre.endswith(".txt") else nombre + ".txt")
        return cls.desde_texto(ruta.read_text(encoding="utf-8"))

    def a_texto(self) -> str:
        filas = []
        for i in range(1, self.tamano + 1):
            fila = ""
            for j in range(1, self.tamano + 1):
                celda = (i, j)
                if celda in self.fosos:
                    fila += "F"
                elif celda == self.serpiente:
                    fila += "S"
                elif celda in self.heridos:
                    fila += "H"
                elif celda in self.atrapados:
                    fila += "X"
                elif celda in self.perdidos:
                    fila += "V"
                elif celda == self.salida:
                    fila += "E"
                elif celda in self.escombros:
                    fila += "*"
                elif celda == self.inicio:
                    fila += "A"
                else:
                    fila += "."
            filas.append(fila)
        return "\n".join(filas)


# ---------------------------------------------------------------------------
# Utilidades de geometría (también útiles para el agente)
# ---------------------------------------------------------------------------

def vecinos(celda: Celda, tamano: int, toroidal: bool = False) -> list[Celda]:
    f, c = celda
    out = []
    for df, dc in DESPLAZAMIENTOS.values():
        nf, nc = f + df, c + dc
        if toroidal:
            nf, nc = (nf - 1) % tamano + 1, (nc - 1) % tamano + 1
        if 1 <= nf <= tamano and 1 <= nc <= tamano and (nf, nc) not in out:
            out.append((nf, nc))
    return out


def todas_las_celdas(tamano: int) -> list[Celda]:
    return [(f, c) for f in range(1, tamano + 1) for c in range(1, tamano + 1)]


def manhattan(a: Celda, b: Celda) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ---------------------------------------------------------------------------
# Generación aleatoria
# ---------------------------------------------------------------------------

def generar_mundo(semilla: int | None = None, tamano: int = 6, n_fosos: int = 3,
                  n_escombros: int = 4, resoluble: bool = True, n_perdidos: int = 1,
                  max_intentos: int = 20000, toroidal: bool = False) -> Mundo:
    """
    Genera un templo aleatorio de *tamano*×*tamano*.

    Reglas:
      * El arqueólogo entra por (1, 1).  Ni esa celda ni sus vecinas contienen
        fosos ni la serpiente (así nunca se empieza «a ciegas»).
      * Fosos, serpiente, perdidos y salida ocupan celdas distintas, ninguna
        de ellas la (1, 1).  Los escombros solo aparecen en celdas libres.
      * Si *resoluble* es True, el templo admite una solución puramente lógica:
        un explorador que solo pisa celdas DEMOSTRABLEMENTE seguras (sin usar
        la antorcha) puede llegar a todos los perdidos y a la salida.

    Con *toroidal* los bordes se comunican (variante de la Parte 2a), también
    para la zona inicial y la comprobación de resolubilidad.

    La misma semilla produce siempre el mismo templo.
    """
    rng = random.Random(semilla)
    inicio = (1, 1)
    celdas = todas_las_celdas(tamano)
    zona_inicial = {inicio, *vecinos(inicio, tamano, toroidal)}
    for _ in range(max_intentos):
        peligros_posibles = [c for c in celdas if c not in zona_inicial]
        elegidas = rng.sample(peligros_posibles, n_fosos + 1)
        fosos, serpiente = frozenset(elegidas[:n_fosos]), elegidas[n_fosos]
        libres = [c for c in celdas if c != inicio and c not in fosos and c != serpiente]
        elegidos = rng.sample(libres, n_perdidos + 1)
        perdidos, salida = frozenset(elegidos[:-1]), elegidos[-1]
        resto = [c for c in libres if c not in perdidos and c != salida]
        escombros = frozenset(rng.sample(resto, min(n_escombros, len(resto))))
        mundo = Mundo(tamano, fosos, serpiente, perdidos, salida, escombros, inicio,
                      toroidal=toroidal)
        if not resoluble or es_resoluble_por_logica(mundo):
            return mundo
    raise RuntimeError("No se ha podido generar un templo resoluble.")


# ---------------------------------------------------------------------------
# ¿Es el templo resoluble solo con lógica?
# ---------------------------------------------------------------------------

def es_resoluble_por_logica(mundo: Mundo) -> bool:
    """
    Simula a un explorador lógico perfecto que no usa la antorcha: en cada ronda
    visita todas las celdas que se pueden DEMOSTRAR seguras con lo percibido
    hasta entonces.  El templo es resoluble si los perdidos y la salida acaban
    dentro de la zona visitada.
    """
    visitadas: set = set()
    seguras = {mundo.inicio}
    while True:
        nuevas = seguras - visitadas
        if not nuevas:
            break
        visitadas |= nuevas
        seguras = celdas_demostrablemente_seguras(mundo, visitadas)
    return mundo.perdidos <= visitadas and mundo.salida in visitadas


def celdas_demostrablemente_seguras(mundo: Mundo, visitadas: set) -> set:
    """
    Celdas que la lógica demuestra libres de foso y de serpiente a partir de las
    percepciones recogidas en *visitadas* (serpiente única y dormida).

      * Fosos: una celda no visitada solo puede demostrarse libre de foso si es
        vecina de una celda visitada SIN corriente de aire.
      * Serpiente: como hay exactamente una, sus posiciones posibles son las
        celdas no visitadas vecinas de TODAS las celdas con siseo y de ninguna
        celda visitada sin siseo.  El resto están libres de serpiente.
    """
    corriente = {v: any(n in mundo.fosos for n in mundo.vecinos(v)) for v in visitadas}
    siseo = {v: mundo.serpiente in mundo.vecinos(v) for v in visitadas}

    sin_foso = set(visitadas)
    for v in visitadas:
        if not corriente[v]:
            sin_foso.update(mundo.vecinos(v))

    posibles_serpiente = {
        c for c in mundo.celdas()
        if c not in visitadas
        and all((c in mundo.vecinos(v)) == siseo[v] for v in visitadas)
    }
    return (sin_foso - posibles_serpiente) | visitadas
