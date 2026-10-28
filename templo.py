"""
templo.py — programa principal de «El templo perdido» (AMIA — MUIAAp).

Ejemplos:
    python templo.py                                  # jugar (modo manual) en un templo aleatorio
    python templo.py --modo manual --semilla 7        # jugar en el templo nº 7
    python templo.py --modo explorador                # agente de referencia (basado en modelo)
    python templo.py --modo busqueda --algoritmo astar   # Parte 2a: plan óptimo con el mapa revelado
    python templo.py --modo busqueda --perdidos 3     # Parte 2a: expedición con tres perdidos
    python templo.py --modo busqueda --toroidal       # Parte 2a: templo toroidal (sin paredes)
    python templo.py --modo huida --algoritmo alfabeta --profundidad 3   # Parte 2b
    python templo.py --modo huida --algoritmo expectimax --serpiente estocastica
    python templo.py --modo huida --algoritmo manual  # Parte 2b: huyes tú con el teclado
    python templo.py --modo logico                    # Parte 3: agente lógico autónomo
    python templo.py --modo logico --texto            # igual, en la terminal (sin GUI)
    python templo.py --modo expedicion                # Parte 4: dos arqueólogos (clingo + A*)
    python templo.py --modo expedicion --egoistas     # Parte 4: los mismos, sin coordinarse
    python templo.py --modo expedicion --mapa expedicion_roles
    python templo.py --mapa ejemplo_enunciado         # usar un mapa de la carpeta mapas/
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from dataclasses import replace

from engine.juego import Agente, ejecutar_partida
from engine.mundo import Mundo, generar_mundo


class AgentePlan(Agente):
    """Ejecuta una lista de acciones calculada de antemano."""

    def __init__(self, plan) -> None:
        self.plan = list(plan)

    def actuar(self, obs):
        return self.plan.pop(0) if self.plan else None


BUSQUEDA = ["bfs", "dfs", "ucs", "astar"]
ADVERSARIOS = ["minimax", "alfabeta", "expectimax", "directo", "manual"]


def _algoritmo(nombre: str):
    from engine.busqueda import astar, bfs, dfs, ucs
    from agente.heuristicas import heuristica_rescate
    return {"bfs": bfs, "dfs": dfs, "ucs": ucs,
            "astar": lambda p: astar(p, heuristica_rescate)}[nombre]


def _politica_huida(nombre: str, profundidad: int):
    from engine.huida import huir_directo
    if nombre == "directo":
        return huir_directo
    from agente import adversarial
    alg = getattr(adversarial, nombre)
    return lambda estado: alg(estado, profundidad, adversarial.funcion_evaluacion)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="El templo perdido — AMIA (MUIAAp)")
    ap.add_argument("--modo", default="manual",
                    choices=["manual", "explorador", "busqueda", "huida", "logico", "expedicion"])
    ap.add_argument("--semilla", type=int, default=None, help="semilla del templo aleatorio")
    ap.add_argument("--mapa", default=None, help="mapa de mapas/ (en lugar de uno aleatorio)")
    ap.add_argument("--perdidos", type=int, default=1, help="exploradores perdidos (Parte 2a)")
    ap.add_argument("--algoritmo", default=None, choices=BUSQUEDA + ADVERSARIOS,
                    help="busqueda: bfs|dfs|ucs|astar (astar) · huida: minimax|alfabeta|"
                         "expectimax|directo|manual (alfabeta)")
    ap.add_argument("--profundidad", type=int, default=3, help="profundidad (Parte 2b)")
    ap.add_argument("--serpiente", default="voraz", choices=["voraz", "estocastica"])
    ap.add_argument("--capacidad", type=int, default=3, help="perdidos por arqueólogo (Parte 4)")
    ap.add_argument("--egoistas", action="store_true", help="Parte 4 sin coordinación")
    ap.add_argument("--texto", action="store_true", help="mostrar en la terminal, sin GUI")
    ap.add_argument("--velocidad", type=float, default=0.3, help="segundos entre pasos")
    ap.add_argument("--toroidal", action="store_true",
                    help="templo toroidal: los bordes se comunican (Parte 2a; modos manual y busqueda)")
    args = ap.parse_args(argv)
    if args.toroidal and args.modo not in ("manual", "busqueda"):
        ap.error("--toroidal solo existe en los modos manual y busqueda (Parte 2a)")

    semilla = args.semilla if args.semilla is not None else random.randrange(10**6)
    if args.modo == "huida" and args.semilla is None and not args.mapa:
        # templo en el que huir directo a la salida NO funciona (más interesante)
        from engine.huida import SerpienteVoraz, huir_directo, jugar_huida
        while not jugar_huida(generar_mundo(semilla), huir_directo, SerpienteVoraz()).atrapado:
            semilla = random.randrange(10**6)

    def crear_mundo(nuevo: bool = False) -> Mundo:
        nonlocal semilla
        if args.mapa:
            return replace(Mundo.cargar(args.mapa), toroidal=args.toroidal)
        if nuevo:
            semilla = random.randrange(10**6)
        if args.modo == "expedicion":
            from engine.expedicion import generar_expedicion
            return generar_expedicion(semilla)
        return generar_mundo(semilla, n_perdidos=args.perdidos, toroidal=args.toroidal)

    mundo = crear_mundo()
    if not args.mapa:
        print(f"Templo aleatorio, semilla {semilla}")

    if args.modo == "manual":
        from agente.agente_logico import AgenteLogico
        from engine.gui import jugar_manual
        jugar_manual(crear_mundo, AgenteLogico)
        return 0

    if args.modo == "huida":
        from engine.huida import SerpienteEstocastica, SerpienteVoraz, jugar_huida
        nombre = args.algoritmo or "alfabeta"
        if nombre not in ADVERSARIOS:
            ap.error(f"en el modo huida, --algoritmo debe ser uno de {ADVERSARIOS}")
        nueva_serpiente = SerpienteVoraz if args.serpiente == "voraz" else SerpienteEstocastica
        if nombre == "manual":
            if args.texto:
                ap.error("la huida manual necesita la GUI (sin --texto)")
            from engine.gui import jugar_huida_manual
            from engine.huida import huir_directo

            def crear_mundo_huida(nuevo: bool = False) -> Mundo:
                # templo nuevo: como al arrancar, uno en el que huir en línea recta fracasa
                while nuevo and not args.mapa:
                    m = crear_mundo(True)
                    if jugar_huida(m, huir_directo, SerpienteVoraz()).atrapado:
                        return m
                return crear_mundo()

            jugar_huida_manual(crear_mundo_huida, nueva_serpiente)
            return 0
        serpiente = nueva_serpiente()
        display = _display(args, None, True)
        r = jugar_huida(mundo, _politica_huida(nombre, args.profundidad), serpiente, display)
        estado = "ESCAPA" if r.escapa else "ATRAPADO" if r.atrapado else "empate (60 turnos)"
        print(f"Huida ({nombre}, serpiente {args.serpiente}): {estado} en {r.turnos} turnos")
        return 0

    if args.modo == "expedicion":
        return _expedicion(args, mundo)

    asesor, revelar = None, False
    if args.modo == "explorador":
        from engine.referencia import AgenteExplorador
        agente = AgenteExplorador()
    elif args.modo == "logico":
        from agente.agente_logico import AgenteLogico
        agente = asesor = AgenteLogico()
    else:  # busqueda
        from agente.problema import ProblemaRescate
        problema = ProblemaRescate(mundo)
        t0 = time.perf_counter()
        nombre = args.algoritmo or "astar"
        if nombre not in BUSQUEDA:
            ap.error(f"en el modo busqueda, --algoritmo debe ser uno de {BUSQUEDA}")
        plan = _algoritmo(nombre)(problema)
        dt = time.perf_counter() - t0
        if plan is None:
            print("No hay solución.")
            return 1
        print(f"{nombre.upper()}: {len(plan)} acciones, coste {problema.coste_plan(plan)}, "
              f"{problema.nodos_expandidos} nodos expandidos, {dt * 1000:.1f} ms")
        print("Plan:", [a.name for a in plan])
        agente, revelar = AgentePlan(plan), True

    display = _display(args, asesor, revelar)
    r = ejecutar_partida(mundo, agente, display=display)
    print(f"Resultado: {r.motivo} · coste {r.coste} · pasos {r.pasos} · puntuación {r.puntuacion}")
    return 0


def _expedicion(args, mundo) -> int:
    from engine.expedicion import (PoliticaEgoista, ejecutar_expedicion, ids_perdidos,
                                   jugar_coordinada)
    if args.texto:
        from engine.texto import VisorExpedicionTexto
        display = VisorExpedicionTexto()
    else:
        from engine.gui import VisorExpedicionTk
        display = VisorExpedicionTk(args.velocidad, "modo expedición" +
                                    (" (egoístas)" if args.egoistas else ""))
    print("Perdidos:", ", ".join(f"{pid}={c}" + (" herido" if c in mundo.heridos else
                                                 " atrapado" if c in mundo.atrapados else "")
                                 for pid, c in ids_perdidos(mundo).items()))
    if args.egoistas:
        r = ejecutar_expedicion(mundo, PoliticaEgoista(), args.capacidad, display)
    else:
        from agente.coordinador import coste_individual
        repartos, reparto, r = jugar_coordinada(mundo, args.capacidad, display)
        print(f"clingo: {len(repartos)} repartos válidos")
        for rep in repartos:
            costes = {n: coste_individual(mundo, p) for n, p in rep.items()}
            marca = "  ← elegido" if rep == reparto else ""
            print("  " + " · ".join(f"{n} {sorted(p)} ({costes[n]:g})" for n, p in rep.items())
                  + f"  makespan {max(costes.values()):g}{marca}")
    print(f"Resultado: {r.motivo} · makespan {r.makespan} · costes {r.costes}"
          + (f" · sin rescatar {sorted(r.sin_rescatar)}" if r.sin_rescatar else ""))
    return 0


def _display(args, asesor, revelar):
    if args.texto:
        from engine.texto import VisorTexto
        return VisorTexto(pausa=0, revelar=revelar)
    from engine.gui import VisorTk
    return VisorTk(args.velocidad, asesor=asesor, revelar=revelar, titulo=f"modo {args.modo}")


if __name__ == "__main__":
    sys.exit(main())
