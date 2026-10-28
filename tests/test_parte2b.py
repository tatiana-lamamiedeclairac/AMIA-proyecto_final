"""Parte 2b — La serpiente despierta (agente/adversarial.py)."""

import pytest

from engine.huida import (EstadoHuida, SerpienteEstocastica, SerpienteVoraz, estado_inicial,
                          jugar_huida)
from engine.juego import Accion
from engine.mundo import Mundo, generar_mundo

pytestmark = pytest.mark.parte2b

# Templos en los que huir directo a la salida acaba en las fauces de la serpiente voraz.
DIFICILES = [0, 2, 11, 13, 14, 15, 17, 19, 20, 21, 22, 29, 34, 35, 36, 37, 40, 42, 46, 50,
             52, 63, 76, 77, 79, 85, 87, 88, 94, 95, 96, 105, 110, 112, 113, 116, 119, 122,
             125, 126]

MINI = Mundo.desde_texto("""
EV..
....
..F.
..S.
""")


def evaluar_neutro(estado):
    return 0


def algoritmos():
    from agente.adversarial import alfabeta, expectimax, minimax
    return {"minimax": minimax, "alfabeta": alfabeta, "expectimax": expectimax}


# ---------------------------------------------------------------- casos de juguete
def test_gana_si_puede():
    """[5 pts] Si la salida está al lado, los tres algoritmos van hacia ella."""
    estado = EstadoHuida(MINI, arqueologo=(1, 2), serpiente=(4, 3))
    for nombre, alg in algoritmos().items():
        assert alg(estado, 1, evaluar_neutro) is Accion.IZQUIERDA, nombre


def test_no_se_suicida():
    """[5 pts] Nunca entra en la celda de la serpiente."""
    estado = EstadoHuida(MINI, arqueologo=(3, 2), serpiente=(4, 2), antorcha=False)
    for nombre, alg in algoritmos().items():
        for prof in (1, 2):
            assert alg(estado, prof, evaluar_neutro) is not Accion.ABAJO, nombre


# ---------------------------------------------------------------- alfa-beta
def test_alfabeta_misma_decision():
    """[6 pts] Alfa-beta elige la misma acción que minimax (recorred las acciones en el
    orden de estado.acciones() y quedaos con la PRIMERA de valor máximo)."""
    from agente.adversarial import alfabeta, funcion_evaluacion, minimax
    for semilla in DIFICILES[:12]:
        e = estado_inicial(generar_mundo(semilla))
        assert minimax(e, 3, funcion_evaluacion) == alfabeta(e, 3, funcion_evaluacion), semilla


def test_alfabeta_poda():
    """[6 pts] Alfa-beta genera como mucho el 60 % de los nodos de minimax."""
    from agente.adversarial import alfabeta, funcion_evaluacion, minimax
    n_mm = n_ab = 0
    for semilla in DIFICILES[:12]:
        e = estado_inicial(generar_mundo(semilla))
        EstadoHuida.nodos = 0
        minimax(e, 3, funcion_evaluacion)
        n_mm += EstadoHuida.nodos
        EstadoHuida.nodos = 0
        alfabeta(e, 3, funcion_evaluacion)
        n_ab += EstadoHuida.nodos
    assert n_ab <= 0.6 * n_mm, f"alfa-beta {n_ab} nodos, minimax {n_mm}"


# ---------------------------------------------------------------- partidas
def test_escapa_de_la_voraz():
    """[10 pts] Con alfa-beta (profundidad 3) y vuestra función de evaluación, escapa de la
    serpiente voraz en al menos el 80 % de los templos donde huir directo fracasa."""
    from agente.adversarial import alfabeta, funcion_evaluacion
    escapes = sum(jugar_huida(generar_mundo(s), lambda e: alfabeta(e, 3, funcion_evaluacion),
                              SerpienteVoraz()).escapa for s in DIFICILES)
    assert escapes >= 0.8 * len(DIFICILES), f"escapa en {escapes}/{len(DIFICILES)}"


def test_expectimax_estocastica():
    """[8 pts] Con expectimax (profundidad 2) escapa de la serpiente estocástica en al
    menos el 80 % de las partidas."""
    from agente.adversarial import expectimax, funcion_evaluacion
    partidas = escapes = 0
    for s in DIFICILES[:25]:
        for k in range(2):
            r = jugar_huida(generar_mundo(s), lambda e: expectimax(e, 2, funcion_evaluacion),
                            SerpienteEstocastica(1000 * s + k))
            partidas += 1
            escapes += r.escapa
    assert escapes >= 0.8 * partidas, f"escapa en {escapes}/{partidas}"
