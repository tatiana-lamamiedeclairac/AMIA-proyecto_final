# El templo perdido — Proyecto final

**Agentes y Métodos de IA (AMIA) — Máster Universitario en Inteligencia Artificial Aplicada (MUIAAp)**
Universidad Pontificia Comillas · ICAI

Un arqueólogo entra en un templo de 6×6 salas en busca de la **Dra. Vega**, su
compañera desaparecida. En el templo hay fosos de pinchos, una serpiente gigante
dormida y una salida que nadie ha marcado en el mapa. Vuestro agente tiene que
encontrar a la Dra. Vega, salir con ella y no morir por el camino… ni cuando la
serpiente se despierte y os persiga. Y al final, dos arqueólogos con roles
distintos tendrán que repartirse el rescate de todo el equipo perdido.

El enunciado completo está en el PDF que acompaña a este repositorio.

## Cómo trabajar

Se trabaja por parejas, cada una en su propio repositorio **privado** creado a
partir de esta plantilla, y **el entregable es ese repositorio**: se corrige la
carpeta `agente/` de la rama `main`.

> **No hagáis *Fork*.** Un fork de un repositorio público es público y no se
> puede hacer privado: cualquiera podría copiar vuestro código.

1. Uno de los dos pulsa **Use this template → Create a new repository** en
   GitHub, elige como visibilidad **Private** y crea el repositorio. Después, en
   *Settings → Collaborators*, añade al otro miembro de la pareja y al profesor
   (el usuario de GitHub que se indicará en clase).
2. Cada uno clona el repositorio de la pareja y trabaja en él:

   ```bash
   git clone https://github.com/<usuario>/<repositorio>.git
   ```

3. Solo se modifica `agente/`. El motor (`engine/`) y los tests (`tests/`) se
   corrigen sobre una copia limpia.

La **defensa oral** es el **2 de diciembre de 2026**.

---

## Estructura

```
templo-perdido/
├── templo.py          ← programa principal (jugar / ver a los agentes)
├── evaluar.py         ← estadísticas sobre muchas partidas
├── agente/            ← VUESTRO CÓDIGO (solo se modifican estos ficheros)
│   ├── problema.py        Parte 2a ProblemaRescate, ProblemaRuta
│   ├── heuristicas.py     Parte 2a heuristica_rescate, heuristica_ruta
│   ├── adversarial.py     Parte 2b minimax, alfabeta, expectimax, funcion_evaluacion
│   ├── templo.lp          Parte 3  el conocimiento del templo en ASP (clingo)
│   ├── agente_logico.py   Parte 3  AgenteLogico.decidir
│   ├── expedicion.lp      Parte 4  los repartos válidos de la expedición en ASP
│   └── coordinador.py     Parte 4  plan_individual, coste_individual, elegir_reparto
├── engine/            ← motor (NO modificar)
│   ├── mundo.py           mapa, generador de templos aleatorios
│   ├── juego.py           Accion, Percepto, Observacion, Juego, ejecutar_partida
│   ├── busqueda_base.py   ProblemaBusqueda (interfaz), ProblemaGrafo
│   ├── busqueda.py        bfs, dfs, ucs, astar (ya los programasteis en pathFinding)
│   ├── huida.py           la serpiente despierta: EstadoHuida, serpientes, jugar_huida
│   ├── referencia.py      AgenteExplorador (el agente a superar)
│   ├── asp.py             ConocimientoASP: hechos observados + templo.lp → clingo
│   ├── expedicion.py      Parte 4: roles, repartos_validos (clingo), simulación, egoístas
│   ├── gui.py, texto.py   visualización
├── mapas/             ← templos de ejemplo (formato texto)
├── tests/             ← autograder (NO modificar)
└── assets/            ← sprites pixel-art (Kenney, CC0)
```

## Instalación

```bash
uv venv                            # crea .venv (instalar uv: https://docs.astral.sh/uv/)
source .venv/bin/activate          # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
# Linux, si la GUI no arranca:  sudo apt install python3-tk
```

## Uso

```bash
python templo.py                                    # jugar con el teclado (templo aleatorio)
python templo.py --semilla 42                       # templo aleatorio reproducible
python templo.py --mapa ejemplo_enunciado           # templo de la carpeta mapas/
python templo.py --modo explorador                  # agente de referencia
python templo.py --modo busqueda --algoritmo ucs    # Parte 2a (bfs | dfs | ucs | astar)
python templo.py --modo busqueda --perdidos 3       # Parte 2a, expedición con 3 perdidos
python templo.py --modo busqueda --mapa toroidal --toroidal   # Parte 2a, templo toroidal
python templo.py --modo huida --algoritmo alfabeta --profundidad 3     # Parte 2b
python templo.py --modo huida --algoritmo expectimax --serpiente estocastica
python templo.py --modo huida --algoritmo manual    # Parte 2b: huyes tú (flechas y espacio)
python templo.py --modo logico                      # Parte 3
python templo.py --modo logico --texto              # cualquier modo sin GUI
python templo.py --modo expedicion                  # Parte 4: dos arqueólogos (clingo + A*)
python templo.py --modo expedicion --egoistas       # Parte 4: los mismos, sin coordinarse
python templo.py --modo expedicion --mapa expedicion_roles
python -m clingo agente/expedicion.lp mapas/expedicion_roles.lp 0   # ver los repartos
```

Controles del modo manual:

| Tecla | Acción |
|---|---|
| ← ↑ ↓ → / WASD | moverse |
| espacio + flecha | lanzar la antorcha en esa dirección |
| X | SALIR (solo funciona en la salida) |
| V | mostrar/ocultar las deducciones de vuestro `AgenteLogico` |
| R / N / Esc | reiniciar / templo nuevo / cerrar |

## Autograder

```bash
pytest                 # todo
pytest -m parte2a      # solo una parte (parte2a, parte2b, parte3, parte4)
python evaluar.py --busqueda --perdidos 3
python evaluar.py --busqueda --perdidos 3 --toroidal
python evaluar.py --huida --serpiente estocastica
python evaluar.py --agente logico --partidas 200
python evaluar.py --expedicion --partidas 100
```

Al final, `pytest` imprime la puntuación por partes. Los tests públicos **no**
son la nota final: también se evalúan la calidad del código y la **defensa oral** del 2 de diciembre de 2026
(individual y obligatoria para los dos miembros de la pareja).

---

Sprites: [Kenney «Tiny Dungeon»](https://kenney.nl/assets/tiny-dungeon) (CC0).
