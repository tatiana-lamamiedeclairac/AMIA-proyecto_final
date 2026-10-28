"""
engine/gui.py — interfaz gráfica (tkinter) de «El templo perdido».

  * VisorTk       — display para ejecutar_partida (ver jugar a un agente).
  * jugar_manual  — juegas tú con el teclado; si hay un asesor (vuestro
                    AgenteLogico) se muestran sus deducciones en cada celda.
  * VisorExpedicionTk — display de la Parte 4 (dos arqueólogos).
  * jugar_huida_manual — la huida de la Parte 2b, jugada por ti con el teclado.

Sprites: Kenney «Tiny Dungeon» (CC0), en assets/sprites/.  Si Pillow no está
instalado se usan gráficos simples.

Controles del modo manual:
  ← ↑ ↓ → / WASD   moverse
  espacio + flecha lanzar la antorcha en esa dirección
  X                SALIR (solo funciona en la salida)
  V                mostrar/ocultar deducciones
  R                reiniciar el mismo templo · N templo nuevo · Esc salir

Este fichero es parte del MOTOR: no debes modificarlo.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Optional

from engine.juego import Accion, Juego

try:
    from PIL import Image, ImageEnhance, ImageTk
    _PIL = True
except ImportError:          # pragma: no cover
    _PIL = False

CELDA = 72
PANEL = 300
C_FONDO = "#15161b"
C_ACENTO = "#FBB800"          # amarillo Comillas
C_TEXTO = "#f2f2f2"
C_SUAVE = "#9aa0ad"
C_NIEBLA = "#2a2620"
C_SUELO = "#c9a26b"
C_PARED = "#4b4f5c"

_TILES = {"pared": 40, "suelo": 48, "escombros": 24, "foso": 41, "salida": 45,
          "heroe": 88, "vega": 99, "serpiente": 123, "botiquin": 131}
_VARIANTES = {"heroe2": "heroe"}       # heroe2 = heroe con los colores cambiados
_DIR_SPRITES = Path(__file__).resolve().parent.parent / "assets" / "sprites"

_COLOR_ETIQUETA = {"✓": "#3ddc84", "F?": "#ff9f43", "F!": "#ff4d4d",
                   "S?": "#c7f464", "S!": "#7bed9f", "E?": "#ffe066", "E!": C_ACENTO}


class _Sprites:
    def __init__(self) -> None:
        self._cache: dict = {}

    def get(self, nombre: str, tam: int, oscuro: bool = False):
        if not _PIL:
            return None
        clave = (nombre, tam, oscuro)
        if clave in self._cache:
            return self._cache[clave]
        ruta = _DIR_SPRITES / f"tile_{_TILES[_VARIANTES.get(nombre, nombre)]:04d}.png"
        if not ruta.exists():
            return None
        img = Image.open(ruta).convert("RGBA").resize((tam, tam), Image.NEAREST)
        if nombre in _VARIANTES:
            r, g, b, a = img.split()
            img = Image.merge("RGBA", (b, g, r, a))
        if oscuro:
            fondo = Image.new("RGB", img.size, (20, 18, 16))
            fondo.paste(img, mask=img.split()[3])
            img = ImageEnhance.Brightness(fondo).enhance(0.28)
        foto = ImageTk.PhotoImage(img)
        self._cache[clave] = foto
        return foto


# ---------------------------------------------------------------------------
# Dibujo del tablero
# ---------------------------------------------------------------------------

class _Tablero:
    def __init__(self, root, tamano: int, titulo: str) -> None:
        import tkinter as tk
        self.n = tamano
        self.sprites = _Sprites()
        self.mostrar_deducciones = True
        lado = (tamano + 2) * CELDA
        root.title(f"El templo perdido · AMIA — MUIAAp · {titulo}")
        root.configure(bg=C_FONDO)
        self.canvas = tk.Canvas(root, width=lado, height=lado, bg=C_FONDO,
                                highlightthickness=0)
        self.canvas.grid(row=0, column=0)
        panel = tk.Frame(root, bg=C_FONDO, width=PANEL, height=lado)
        panel.grid(row=0, column=1, sticky="n")
        panel.grid_propagate(False)
        tk.Frame(panel, bg=C_ACENTO, height=6, width=PANEL).pack(fill="x", pady=(0, 10))
        tk.Label(panel, text="EL TEMPLO PERDIDO", fg=C_ACENTO, bg=C_FONDO,
                 font=("Helvetica", 16, "bold")).pack(anchor="w", padx=14)
        tk.Label(panel, text=titulo, fg=C_SUAVE, bg=C_FONDO,
                 font=("Helvetica", 11, "italic")).pack(anchor="w", padx=14, pady=(0, 8))
        self.etiquetas = {}
        for clave in ("paso", "coste", "vega", "antorcha", "percepto", "estado"):
            lbl = tk.Label(panel, text="", fg=C_TEXTO, bg=C_FONDO, justify="left",
                           font=("Helvetica", 12), wraplength=PANEL - 28)
            lbl.pack(anchor="w", padx=14, pady=2)
            self.etiquetas[clave] = lbl
        self.ayuda = tk.Label(panel, text="", fg=C_SUAVE, bg=C_FONDO, justify="left",
                              font=("Helvetica", 10))
        self.ayuda.pack(anchor="w", padx=14, pady=(12, 0))

    def _xy(self, celda):
        f, c = celda
        return c * CELDA, f * CELDA

    def _img(self, nombre, x, y, margen=0, oscuro=False):
        img = self.sprites.get(nombre, CELDA - 2 * margen, oscuro)
        if img is not None:
            self.canvas.create_image(x + margen, y + margen, image=img, anchor="nw")
            return True
        return False

    def dibujar(self, juego: Juego, revelar: bool = False,
                deducciones: Optional[dict] = None) -> None:
        cv, m = self.canvas, juego.mundo
        cv.delete("all")
        n = self.n
        for i in range(n + 2):                       # muro exterior
            for j in range(n + 2):
                if i in (0, n + 1) or j in (0, n + 1):
                    x, y = j * CELDA, i * CELDA
                    if not self._img("pared", x, y):
                        cv.create_rectangle(x, y, x + CELDA, y + CELDA, fill=C_PARED, outline="")
        for celda in m.celdas():
            x, y = self._xy(celda)
            visible = revelar or celda in juego.visitadas
            base = "escombros" if celda in m.escombros else "suelo"
            if not self._img(base, x, y, oscuro=not visible):
                cv.create_rectangle(x, y, x + CELDA, y + CELDA,
                                    fill=C_SUELO if visible else C_NIEBLA, outline="#000")
            if celda in m.escombros and not _PIL:
                cv.create_text(x + CELDA - 12, y + 12, text="*", fill="#5a3b1c",
                               font=("Helvetica", 16, "bold"))
            if visible:
                if celda in m.fosos and not self._img("foso", x, y, 4):
                    cv.create_rectangle(x + 8, y + 8, x + CELDA - 8, y + CELDA - 8, fill="#222")
                if celda == m.salida and not self._img("salida", x, y, 4):
                    cv.create_text(x + CELDA / 2, y + CELDA / 2, text="SALIDA", fill=C_ACENTO)
                if celda == m.serpiente and juego.serpiente_presente:
                    if not self._img("serpiente", x, y, 6):
                        cv.create_text(x + CELDA / 2, y + CELDA / 2, text="S", fill="#7bed9f",
                                       font=("Helvetica", 26, "bold"))
                if celda in m.perdidos and celda not in juego.rescatados:
                    if not self._img("vega", x, y, 6):
                        cv.create_text(x + CELDA / 2, y + CELDA / 2, text="V", fill="#e056fd",
                                       font=("Helvetica", 26, "bold"))
            if celda in juego.visitadas:              # percepciones de la celda
                p = _percepto_en(juego, celda)
                glifos = [(g, col) for g, col, act in (("≈", "#4dabf7", p[0]),
                                                       ("§", "#69db7c", p[1]),
                                                       ("☀", "#ffd43b", p[2])) if act]
                for k, (g, col) in enumerate(glifos):
                    cv.create_text(x + 11 + 18 * k, y + 11, text=g, fill=col,
                                   font=("Helvetica", 14, "bold"))
            if self.mostrar_deducciones and deducciones and celda in deducciones:
                texto = " ".join(deducciones[celda])
                if texto:
                    col = _COLOR_ETIQUETA.get(deducciones[celda][0], C_TEXTO)
                    cv.create_rectangle(x + 2, y + CELDA - 20, x + CELDA - 2, y + CELDA - 2,
                                        fill="#000000", stipple="gray50", outline="")
                    cv.create_text(x + CELDA / 2, y + CELDA - 11, text=texto, fill=col,
                                   font=("Helvetica", 11, "bold"))
        x, y = self._xy(juego.posicion)               # arqueólogo
        if not self._img("heroe", x, y, 6):
            cv.create_oval(x + 16, y + 16, x + CELDA - 16, y + CELDA - 16, fill="#37c0f6")
        if juego.rescatados:
            if not self._img_mini("vega", x + CELDA - 30, y + 2):
                cv.create_text(x + CELDA - 12, y + 12, text="V", fill="#e056fd")

    def _img_mini(self, nombre, x, y):
        img = self.sprites.get(nombre, 28)
        if img is None:
            return False
        self.canvas.create_image(x, y, image=img, anchor="nw")
        return True

    def panel(self, juego: Juego, estado: str = "") -> None:
        p = juego.percepto()
        e = self.etiquetas
        e["paso"].config(text=f"Paso: {juego.pasos}")
        e["coste"].config(text=f"Coste acumulado: {juego.coste}")
        n = len(juego.mundo.perdidos)
        if n == 1:
            texto = f"Dra. Vega: {'rescatada ✔' if juego.rescatada else 'sin encontrar'}"
        else:
            texto = f"Rescatados: {len(juego.rescatados)}/{n}" + (" ✔" if juego.rescatada else "")
        e["vega"].config(text=texto)
        e["antorcha"].config(text=f"Antorcha: {'disponible' if juego.antorcha else 'usada'}")
        e["percepto"].config(text=f"Percepto: {p.como_lista()}\n{p}")
        if not estado:
            estado = {"exito": "¡MISIÓN CUMPLIDA!", "foso": "Muerte: foso de pinchos",
                      "serpiente": "Muerte: la serpiente", "sin_vega": "Salió sin rescatar a todos",
                      "abandono": "El agente se rinde", "limite": "Límite de pasos"
                      }.get(juego.motivo, "explorando…")
        e["estado"].config(text=f"Estado: {estado}",
                           fg=C_ACENTO if juego.exito else C_TEXTO)


def _percepto_en(juego: Juego, celda):
    m = juego.mundo
    vec = m.vecinos(celda)
    return (any(v in m.fosos for v in vec),
            juego.serpiente_presente and m.serpiente in vec,
            m.salida == celda or m.salida in vec)


_LEYENDA = ("Leyenda: ≈ corriente · § siseo · ☀ luz\n"
            "✓ segura · F? F! foso · S? S! serpiente\nE? E! salida")


# ---------------------------------------------------------------------------
# Visor para ejecutar_partida
# ---------------------------------------------------------------------------

class VisorTk:
    """Display gráfico para engine.juego.ejecutar_partida."""

    def __init__(self, velocidad: float = 0.3, asesor=None, revelar: bool = False,
                 titulo: str = "") -> None:
        self.velocidad = velocidad
        self.asesor = asesor
        self.revelar = revelar
        self.titulo = titulo
        self.root = None
        self.tablero = None

    def inicializar(self, juego: Juego) -> None:
        import tkinter as tk
        self.root = tk.Tk()
        self.tablero = _Tablero(self.root, juego.mundo.tamano, self.titulo)
        self.tablero.ayuda.config(text=_LEYENDA + "\n\nCierra la ventana al terminar.")
        self._pintar(juego)

    def actualizar(self, juego: Juego) -> None:
        self._pintar(juego)
        if self.velocidad > 0:
            fin = time.time() + self.velocidad
            while time.time() < fin:
                self.root.update()
                time.sleep(0.01)

    def final(self, juego: Juego) -> None:
        self._pintar(juego, revelar=True)
        self.root.mainloop()

    def _pintar(self, juego: Juego, revelar: bool = False) -> None:
        ded = _deducciones_seguras(self.asesor)
        self.tablero.dibujar(juego, revelar or self.revelar, ded)
        self.tablero.panel(juego)
        self.root.update_idletasks()
        self.root.update()


def _deducciones_seguras(asesor) -> Optional[dict]:
    if asesor is None:
        return None
    try:
        return asesor.deducciones()
    except Exception:            # agente sin implementar o templo.lp con errores
        return None


# ---------------------------------------------------------------------------
# Parte 4: la expedición (dos arqueólogos)
# ---------------------------------------------------------------------------

_SPRITE_ARQ = {"indy": "heroe", "lara": "heroe2"}
_COLOR_ARQ = {"indy": "#f6a637", "lara": "#37c0f6"}     # como sus sprites
_LEYENDA_EXPEDICION = ("Leyenda:\n✚ herido: solo indy (botiquín)\n"
                       "⛏ atrapado: solo lara (pico)\nV cualquiera\n"
                       "I / L  indy / lara (y a quién le toca)")


class VisorExpedicionTk:
    """Display gráfico para engine.expedicion.ejecutar_expedicion."""

    def __init__(self, velocidad: float = 0.3, titulo: str = "") -> None:
        self.velocidad = velocidad
        self.titulo = titulo
        self.root = None
        self.tablero = None

    def inicializar(self, estado) -> None:
        import tkinter as tk
        self.root = tk.Tk()
        self.tablero = _Tablero(self.root, estado.mundo.tamano, self.titulo)
        self.tablero.ayuda.config(text=_LEYENDA_EXPEDICION + "\n\nCierra la ventana al terminar.")
        self._pintar(estado)

    def actualizar(self, estado) -> None:
        self._pintar(estado)
        if self.velocidad > 0:
            fin = time.time() + self.velocidad
            while time.time() < fin:
                self.root.update()
                time.sleep(0.01)

    def final(self, estado, resultado) -> None:
        texto = {"exito": "¡EXPEDICIÓN CUMPLIDA!", "muerte": "Ha muerto un arqueólogo",
                 "sin_rescatar": f"Quedan {len(resultado.sin_rescatar)} perdidos dentro",
                 "abandono": "Un arqueólogo se rinde", "limite": "Límite de pasos"
                 }[resultado.motivo]
        self._pintar(estado, f"{texto}\nmakespan: {resultado.makespan}")
        self.root.mainloop()

    def _pintar(self, e, estado: str = "") -> None:
        t, cv, m = self.tablero, self.tablero.canvas, e.mundo
        cv.delete("all")
        n = m.tamano
        for i in range(n + 2):
            for j in range(n + 2):
                if i in (0, n + 1) or j in (0, n + 1):
                    x, y = j * CELDA, i * CELDA
                    if not t._img("pared", x, y):
                        cv.create_rectangle(x, y, x + CELDA, y + CELDA, fill=C_PARED, outline="")
        pendientes = e.pendientes()
        dueno = {c: nombre for nombre, cs in (e.reparto or {}).items() for c in cs}
        for celda in m.celdas():
            x, y = t._xy(celda)
            if not t._img("escombros" if celda in m.escombros else "suelo", x, y):
                cv.create_rectangle(x, y, x + CELDA, y + CELDA, fill=C_SUELO, outline="#000")
            if celda in m.fosos and not t._img("foso", x, y, 4):
                cv.create_rectangle(x + 8, y + 8, x + CELDA - 8, y + CELDA - 8, fill="#222")
            if celda == m.salida and not t._img("salida", x, y, 4):
                cv.create_text(x + CELDA / 2, y + CELDA / 2, text="SALIDA", fill=C_ACENTO)
            if celda == m.serpiente and e.serpiente_presente and not t._img("serpiente", x, y, 6):
                cv.create_text(x + CELDA / 2, y + CELDA / 2, text="S", fill="#7bed9f",
                               font=("Helvetica", 26, "bold"))
            if celda in pendientes:
                if not t._img("vega", x, y, 10):
                    cv.create_text(x + CELDA / 2, y + CELDA / 2, text="V", fill="#e056fd",
                                   font=("Helvetica", 26, "bold"))
                if celda in m.heridos:
                    cv.create_text(x + 12, y + 12, text="✚", fill="#ff4d4d",
                                   font=("Helvetica", 16, "bold"))
                if celda in m.atrapados:
                    cv.create_text(x + 12, y + 12, text="⛏", fill="#ffffff",
                                   font=("Helvetica", 15, "bold"))
                if celda in dueno:
                    nombre = dueno[celda]
                    cv.create_oval(x + CELDA - 22, y + 2, x + CELDA - 2, y + 22,
                                   fill="#15161b", outline=_COLOR_ARQ[nombre], width=2)
                    cv.create_text(x + CELDA - 12, y + 12, text=nombre[0].upper(),
                                   fill=_COLOR_ARQ[nombre], font=("Helvetica", 12, "bold"))
        for k, nombre in enumerate(e.posiciones):
            if nombre in e.fuera:
                continue
            x, y = t._xy(e.posiciones[nombre])
            dx = -10 if k == 0 else 10
            if not t._img(_SPRITE_ARQ[nombre], x + dx, y, 8):
                cv.create_oval(x + dx + 18, y + 18, x + dx + CELDA - 18, y + CELDA - 18,
                               fill=_COLOR_ARQ[nombre])
            if nombre in e.muertos:
                cv.create_text(x + CELDA / 2, y + CELDA / 2, text="✖", fill="#ff4d4d",
                               font=("Helvetica", 30, "bold"))
        et = t.etiquetas
        et["paso"].config(text=f"Paso: {e.pasos}")
        et["coste"].config(text="  ·  ".join(f"{nombre}: {c}" for nombre, c in e.costes.items()))
        et["vega"].config(text=f"Rescatados: {len(m.perdidos) - len(pendientes)}/{len(m.perdidos)}"
                               f"  (capacidad {e.capacidad} cada uno)")
        lineas = []
        for nombre in e.posiciones:
            situacion = ("fuera ✔" if nombre in e.fuera else "muerto" if nombre in e.muertos
                         else "se rinde" if nombre in e.rendidos else "dentro")
            lineas.append(f"{nombre}: {len(e.rescatados[nombre])} rescatados · {situacion}")
        et["antorcha"].config(text="\n".join(lineas))
        if e.reparto:
            reparto = "\n".join(f"{nombre} → {sorted(cs)}" for nombre, cs in e.reparto.items())
            et["percepto"].config(text=f"Reparto (clingo + A*):\n{reparto}")
        else:
            et["percepto"].config(text="Sin coordinación (egoístas)")
        if e.ultimo and not estado:
            estado = f"{e.ultimo[0]}: {e.ultimo[1].name if e.ultimo[1] else 'se rinde'}"
        et["estado"].config(text=f"Estado: {estado}", fg=C_ACENTO if "CUMPLIDA" in estado else C_TEXTO)
        self.root.update_idletasks()
        self.root.update()


# ---------------------------------------------------------------------------
# Modo manual
# ---------------------------------------------------------------------------

_TECLA_DIR = {"Up": "ARRIBA", "Down": "ABAJO", "Left": "IZQUIERDA", "Right": "DERECHA",
              "w": "ARRIBA", "s": "ABAJO", "a": "IZQUIERDA", "d": "DERECHA"}


def jugar_manual(crear_mundo: Callable, crear_asesor: Optional[Callable] = None) -> None:
    """Juega con el teclado.  *crear_mundo(nuevo: bool)* devuelve un Mundo;
    *crear_asesor()* (opcional) devuelve un agente con observar()/deducciones()."""
    import tkinter as tk

    estado = {"lanzar": False}

    def nueva_partida(nuevo: bool) -> None:
        estado["juego"] = Juego(crear_mundo(nuevo))
        estado["asesor"] = None
        # templo.lp supone paredes: en un templo toroidal sus deducciones serían falsas
        if crear_asesor is not None and not estado["juego"].mundo.toroidal:
            try:
                asesor = crear_asesor()
                asesor.observar(estado["juego"].observacion(), None)
                estado["asesor"] = asesor
            except Exception as e:
                print(f"Sin deducciones: {e}")
                estado["asesor"] = None

    nueva_partida(False)
    root = tk.Tk()
    tablero = _Tablero(root, estado["juego"].mundo.tamano, "modo manual")
    tablero.ayuda.config(text=("Controles:\n← ↑ ↓ → / WASD  moverse\n"
                               "espacio + flecha  lanzar antorcha\n"
                               "X  salir del templo\nV  deducciones on/off\n"
                               "R  reiniciar · N  templo nuevo · Esc  salir\n\n" + _LEYENDA))

    def pintar() -> None:
        j = estado["juego"]
        aviso = "elige dirección para lanzar…" if estado["lanzar"] else ""
        if estado["asesor"] is None and crear_asesor is not None:
            if j.mundo.toroidal:
                aviso = aviso or "(sin deducciones en el templo toroidal)"
            else:
                aviso = aviso or "(sin deducciones: revisad templo.lp)"
        tablero.dibujar(j, revelar=j.terminado, deducciones=_deducciones_seguras(estado["asesor"]))
        tablero.panel(j, aviso if not j.terminado else "")

    def jugar(accion: Accion) -> None:
        j = estado["juego"]
        if j.terminado:
            return
        obs = j.ejecutar(accion)
        if estado["asesor"] is not None and not j.terminado:
            try:
                estado["asesor"].observar(obs, accion)
            except Exception as e:
                print(f"Sin deducciones: {e}")
                estado["asesor"] = None
        pintar()

    def tecla(ev) -> None:
        k = ev.keysym
        if k == "Escape":
            root.destroy()
        elif k in ("r", "R", "n", "N"):
            nueva_partida(k in ("n", "N"))
            estado["lanzar"] = False
            pintar()
        elif k in ("v", "V"):
            tablero.mostrar_deducciones = not tablero.mostrar_deducciones
            pintar()
        elif k == "space":
            estado["lanzar"] = not estado["lanzar"]
            pintar()
        elif k in ("x", "X"):
            jugar(Accion.SALIR)
        elif k in _TECLA_DIR:
            nombre = _TECLA_DIR[k]
            if estado["lanzar"]:
                estado["lanzar"] = False
                jugar(Accion[f"LANZAR_{nombre}"])
            else:
                jugar(Accion[nombre])

    root.bind("<Key>", tecla)
    pintar()
    root.mainloop()


# ---------------------------------------------------------------------------
# Parte 2b: la huida, jugada a mano
# ---------------------------------------------------------------------------

def jugar_huida_manual(crear_mundo: Callable, crear_serpiente: Callable) -> None:
    """Juega tú la persecución de la Parte 2b con el teclado.  *crear_mundo(nuevo)*
    devuelve un Mundo; *crear_serpiente()*, la serpiente (voraz o estocástica),
    que mueve sola después de cada jugada tuya."""
    import tkinter as tk

    from engine.huida import ARQUEOLOGO, MAX_TURNOS, VistaHuida, estado_inicial

    partida = {"lanzar": False, "esperando": False, "aviso": ""}

    def nueva_partida(nuevo: bool) -> None:
        partida.update(estado=estado_inicial(crear_mundo(nuevo)), serpiente=crear_serpiente(),
                       lanzar=False, esperando=False, aviso="", acciones=[])

    nueva_partida(False)
    root = tk.Tk()
    tablero = _Tablero(root, partida["estado"].mundo.tamano, "huida manual (Parte 2b)")
    tablero.ayuda.config(text=("Controles:\n← ↑ ↓ → / WASD  moverse\n"
                               "espacio + flecha  lanzar antorcha\n"
                               "R  reiniciar · N  templo nuevo · Esc  salir\n\n"
                               "Llega a la salida sin que te atrape.\n"
                               "La serpiente descansa en sus turnos 3, 6, 9…\n"
                               "La antorcha (un uso) la aturde 3 turnos si\n"
                               "está a tu lado en esa dirección.\n\n" + _LEYENDA))

    def pintar() -> None:
        e = partida["estado"]
        vista = VistaHuida(e, partida["acciones"])
        if e.es_terminal():
            texto = (f"¡ESCAPAS en {e.turno} turnos!" if e.escapa()
                     else "te ha atrapado la serpiente" if e.atrapado()
                     else f"empate: {MAX_TURNOS} turnos")
        else:
            lineas = [f"turno {e.turno}/{MAX_TURNOS}"]
            if e.aturdida:
                lineas.append(f"serpiente aturdida ({e.aturdida} turnos)")
            elif e.serpiente_descansa():
                lineas.append("la serpiente descansa este turno")
            if partida["lanzar"]:
                lineas.append("elige dirección para lanzar…")
            if partida["aviso"]:
                lineas.append(partida["aviso"])
            texto = "\n".join(lineas)
        tablero.dibujar(vista, revelar=True)
        tablero.panel(vista, texto)

    def mueve_serpiente() -> None:
        e = partida["estado"]
        if not e.es_terminal() and e.jugador() != ARQUEOLOGO:
            partida["estado"] = e.sucesor(partida["serpiente"].elegir(e))
        partida["esperando"] = False
        pintar()

    def jugar(accion: Accion) -> None:
        e = partida["estado"]
        if e.es_terminal() or partida["esperando"]:
            return
        if accion not in e.acciones():
            partida["aviso"] = ("la antorcha solo sirve con la serpiente al lado"
                                if accion.name.startswith("LANZAR") else "por ahí no se puede ir")
            pintar()
            return
        partida["aviso"] = ""
        partida["acciones"].append(accion)
        partida["estado"] = e.sucesor(accion)
        partida["esperando"] = True
        pintar()
        root.after(250, mueve_serpiente)

    def tecla(ev) -> None:
        k = ev.keysym
        if k == "Escape":
            root.destroy()
        elif k in ("r", "R", "n", "N"):
            nueva_partida(k in ("n", "N"))
            pintar()
        elif k == "space":
            partida["lanzar"] = not partida["lanzar"]
            partida["aviso"] = ""
            pintar()
        elif k in _TECLA_DIR:
            nombre = _TECLA_DIR[k]
            if partida["lanzar"]:
                partida["lanzar"] = False
                jugar(Accion[f"LANZAR_{nombre}"])
            else:
                jugar(Accion[nombre])

    root.bind("<Key>", tecla)
    pintar()
    root.mainloop()
