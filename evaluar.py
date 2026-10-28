"""
evaluar.py — juega muchas partidas sin GUI y resume los resultados.

    python evaluar.py --busqueda --partidas 50                 # Parte 2a: BFS/DFS/UCS/A*
    python evaluar.py --busqueda --perdidos 3                  # Parte 2a: expediciones
    python evaluar.py --busqueda --perdidos 3 --toroidal       # Parte 2a: templos toroidales
    python evaluar.py --huida --partidas 50                    # Parte 2b: algoritmos y profundidades
    python evaluar.py --huida --serpiente estocastica
    python evaluar.py --agente logico --partidas 200           # Parte 3
    python evaluar.py --agente explorador --partidas 200       # referencia
    python evaluar.py --expedicion --partidas 100              # Parte 4: coordinados vs egoístas
"""

from __future__ import annotations

import argparse
import time
from collections import Counter

from engine.juego import Juego, ejecutar_partida
from engine.mundo import generar_mundo


def evaluar_agente(nombre: str, partidas: int, desde: int) -> None:
    if nombre == "explorador":
        from engine.referencia import AgenteExplorador as crear
    else:
        from agente.agente_logico import AgenteLogico as crear
    motivos, costes = Counter(), []
    t0 = time.perf_counter()
    for s in range(desde, desde + partidas):
        r = ejecutar_partida(generar_mundo(s), crear())
        motivos[r.motivo] += 1
        if r.exito:
            costes.append(r.coste)
    dt = time.perf_counter() - t0
    print(f"Agente {nombre}: {partidas} partidas (semillas {desde}–{desde + partidas - 1})")
    print(f"  éxito: {motivos['exito']} ({100 * motivos['exito'] / partidas:.1f} %)")
    print(f"  muertes: foso {motivos['foso']}, serpiente {motivos['serpiente']}")
    print(f"  otros: {dict((k, v) for k, v in motivos.items() if k not in ('exito', 'foso', 'serpiente'))}")
    if costes:
        print(f"  coste medio de las partidas ganadas: {sum(costes) / len(costes):.1f}")
    print(f"  tiempo: {dt:.2f} s ({1000 * dt / partidas:.1f} ms/partida)")


def comparar_busqueda(partidas: int, desde: int, perdidos: int, toroidal: bool = False) -> None:
    from agente.heuristicas import heuristica_rescate
    from agente.problema import ProblemaRescate
    from engine.busqueda import astar, bfs, dfs, ucs
    algoritmos = {"BFS": bfs, "DFS": dfs, "UCS": ucs,
                  "A*": lambda p: astar(p, heuristica_rescate)}
    print(f"{perdidos} perdido(s), {partidas} templos{' toroidales' if toroidal else ''}")
    print(f"{'algoritmo':>9} {'coste medio':>12} {'nodos medios':>13} {'ms medios':>10}")
    for nombre, alg in algoritmos.items():
        coste = nodos = tiempo = 0.0
        for s in range(desde, desde + partidas):
            mundo = generar_mundo(s, n_perdidos=perdidos, toroidal=toroidal)
            p = ProblemaRescate(mundo)
            t0 = time.perf_counter()
            plan = alg(p)
            tiempo += time.perf_counter() - t0
            juego = Juego(mundo)
            for a in plan:
                juego.ejecutar(a)
            assert juego.exito, f"{nombre} devolvió un plan que no rescata (semilla {s})"
            coste += juego.coste
            nodos += p.nodos_expandidos
        n = partidas
        print(f"{nombre:>9} {coste / n:12.2f} {nodos / n:13.1f} {1000 * tiempo / n:10.2f}")


def comparar_huida(partidas: int, desde: int, serpiente: str) -> None:
    from agente import adversarial as adv
    from engine.huida import (EstadoHuida, SerpienteEstocastica, SerpienteVoraz, huir_directo,
                              jugar_huida)
    politicas = [("directo", None, None)]
    for nombre in ("minimax", "alfabeta", "expectimax"):
        for prof in (1, 2, 3):
            politicas.append((nombre, getattr(adv, nombre), prof))
    print(f"Serpiente {serpiente}, {partidas} templos")
    print(f"{'política':>16} {'escapa':>7} {'atrapado':>9} {'utilidad':>9} {'nodos/jugada':>13} {'s':>6}")
    for nombre, alg, prof in politicas:
        escapa = atrapado = jugadas = 0
        utilidad = 0.0
        EstadoHuida.nodos = 0
        t0 = time.perf_counter()
        for s in range(desde, desde + partidas):
            decidir = huir_directo if alg is None else (
                lambda e, alg=alg, prof=prof: alg(e, prof, adv.funcion_evaluacion))
            rival = SerpienteVoraz() if serpiente == "voraz" else SerpienteEstocastica(s)
            r = jugar_huida(generar_mundo(s), decidir, rival)
            escapa += r.escapa
            atrapado += r.atrapado
            utilidad += r.utilidad
            jugadas += len(r.acciones)
        etiqueta = nombre if prof is None else f"{nombre} p={prof}"
        print(f"{etiqueta:>16} {escapa:7d} {atrapado:9d} {utilidad / partidas:9.1f} "
              f"{EstadoHuida.nodos / max(1, jugadas):13.1f} {time.perf_counter() - t0:6.2f}")


def comparar_expedicion(partidas: int, desde: int, capacidad: int) -> None:
    from engine.expedicion import (PoliticaEgoista, ejecutar_expedicion, generar_expedicion,
                                   jugar_coordinada)
    filas = {"coordinados": [], "egoístas": []}
    n_repartos = 0
    t0 = time.perf_counter()
    for s in range(desde, desde + partidas):
        mundo = generar_expedicion(s)
        repartos, _, r = jugar_coordinada(mundo, capacidad)
        n_repartos += len(repartos)
        filas["coordinados"].append(r)
        filas["egoístas"].append(ejecutar_expedicion(mundo, PoliticaEgoista(), capacidad))
    print(f"Expediciones: {partidas} templos (semillas {desde}–{desde + partidas - 1}), "
          f"capacidad {capacidad}, {n_repartos / partidas:.1f} repartos válidos de media")
    print(f"{'equipo':>12} {'éxito':>6} {'sin rescatar':>13} {'muertes':>8} "
          f"{'makespan (éxitos)':>18} {'coste total':>12}")
    for nombre, rs in filas.items():
        ok = [r for r in rs if r.exito]
        print(f"{nombre:>12} {len(ok):6d} {sum(r.motivo == 'sin_rescatar' for r in rs):13d} "
              f"{sum(r.motivo == 'muerte' for r in rs):8d} "
              f"{sum(r.makespan for r in ok) / max(1, len(ok)):18.2f} "
              f"{sum(sum(r.costes.values()) for r in ok) / max(1, len(ok)):12.2f}")
    print(f"  tiempo: {time.perf_counter() - t0:.2f} s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agente", default="logico", choices=["explorador", "logico"])
    ap.add_argument("--partidas", type=int, default=100)
    ap.add_argument("--desde", type=int, default=0, help="primera semilla")
    ap.add_argument("--busqueda", action="store_true", help="comparar algoritmos (Parte 2a)")
    ap.add_argument("--perdidos", type=int, default=1, help="perdidos por templo (Parte 2a)")
    ap.add_argument("--toroidal", action="store_true", help="templos toroidales (Parte 2a)")
    ap.add_argument("--huida", action="store_true", help="comparar algoritmos (Parte 2b)")
    ap.add_argument("--serpiente", default="voraz", choices=["voraz", "estocastica"])
    ap.add_argument("--expedicion", action="store_true", help="coordinados vs egoístas (Parte 4)")
    ap.add_argument("--capacidad", type=int, default=3, help="perdidos por arqueólogo (Parte 4)")
    a = ap.parse_args()
    if a.expedicion:
        comparar_expedicion(a.partidas, a.desde, a.capacidad)
    elif a.busqueda:
        comparar_busqueda(a.partidas, a.desde, a.perdidos, a.toroidal)
    elif a.huida:
        comparar_huida(a.partidas, a.desde, a.serpiente)
    else:
        evaluar_agente(a.agente, a.partidas, a.desde)
