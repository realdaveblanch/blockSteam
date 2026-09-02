"""Bloqueador de conexiones por ejecutable, sin reglas de Firewall de Windows."""
from __future__ import annotations

import ctypes
import json
import os
import queue
import sys
import threading
import time
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

import psutil
import pydivert

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    Window = TkinterDnD.Tk
    DND = True
except ImportError:
    Window, DND = tk.Tk, False

DATA = Path(os.environ.get("APPDATA", str(Path.home()))) / "BloqueadorConexiones"
CONFIG = DATA / "lista.json"


def canonical(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(os.path.normpath(str(path))))


def admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate() -> None:
    program = sys.executable
    args = "" if getattr(sys, "frozen", False) else f'"{Path(__file__).resolve()}"'
    if ctypes.windll.shell32.ShellExecuteW(None, "runas", program, args, None, 1) <= 32:
        raise OSError("No se pudo solicitar elevación.")


def load() -> tuple[bool, list[dict[str, object]]]:
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
        return bool(data.get("global", False)), [x for x in data.get("items", []) if isinstance(x, dict)]
    except (OSError, ValueError, json.JSONDecodeError):
        return False, []


def save(global_mode: bool, items: list[dict[str, object]]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps({"global": global_mode, "items": items}, ensure_ascii=False, indent=2), encoding="utf-8")


class DivertGuard:
    """Bloquea eventos connect de los PID indicados y mantiene los .exe vivos."""
    def __init__(self, paths: set[str], events: queue.Queue[str]) -> None:
        self.paths, self.events = paths, events
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.handle: pydivert.WinDivert | None = None
        self.pids: set[int] = set()
        self.worker = threading.Thread(target=self._receive, daemon=True)
        self.scanner = threading.Thread(target=self._scan, daemon=True)

    def start(self) -> None:
        self.scanner.start()
        self.worker.start()

    def close(self) -> None:
        self.stop.set()
        self._close_handle()

    def _active_pids(self) -> set[int]:
        result: set[int] = set()
        for proc in psutil.process_iter(("pid", "exe")):
            try:
                if proc.info["exe"] and canonical(proc.info["exe"]) in self.paths:
                    result.add(proc.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return result

    def _scan(self) -> None:
        while not self.stop.wait(0.20):
            current = self._active_pids()
            if current != self.pids:
                self.pids = current
                self._close_handle()  # fuerza a recrear el filtro con los PID actuales

    def _close_handle(self) -> None:
        with self.lock:
            if self.handle:
                try:
                    self.handle.close()
                except OSError:
                    pass
                self.handle = None

    def _receive(self) -> None:
        self.events.put("Vigilancia activa: las conexiones se deniegan sin cerrar los programas.")
        while not self.stop.is_set():
            pids = self.pids
            if not pids:
                self.stop.wait(0.10)
                continue
            # SOCKET permite filtrar connect por PID antes de que haya tráfico IP.
            condition = " or ".join(f"processId == {pid}" for pid in sorted(pids))
            filter_text = f"event == CONNECT and !loopback and ({condition})"
            try:
                handle = pydivert.WinDivert(filter_text, layer=pydivert.Layer.SOCKET,
                                             flags=pydivert.Flag.RECV_ONLY)
                handle.open()
                with self.lock:
                    self.handle = handle
                while not self.stop.is_set() and handle == self.handle:
                    handle.recv()
                    self.events.put("Conexión saliente denegada.")
            except OSError as error:
                if not self.stop.is_set():
                    self.events.put(f"Error del filtro de red: {error}")
                    self.stop.wait(1)
            finally:
                self._close_handle()


class App(Window):
    def __init__(self) -> None:
        super().__init__()
        self.title("Bloqueador de conexiones")
        self.geometry("800x540")
        self.minsize(700, 460)
        self.global_mode, self.items = load()
        self.global_var = tk.BooleanVar(value=self.global_mode)
        self.status = tk.StringVar(value="Vigilancia detenida")
        self.events: queue.Queue[str] = queue.Queue()
        self.guard: DivertGuard | None = None
        self.build()
        self.refresh()
        self.after(200, self.poll_events)
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

    def build(self) -> None:
        self.configure(padx=18, pady=16)
        ttk.Label(self, text="Bloqueador de conexiones", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Label(self, text="Bloquea el intento de conexión saliente del ejecutable; el proceso no se cierra. No crea reglas en el Firewall de Windows ni modifica ESET.", wraplength=760).grid(row=1, column=0, columnspan=4, sticky="w", pady=(5, 12))
        ttk.Checkbutton(self, text="Modo global: bloquear todos los ejecutables de la lista", variable=self.global_var, command=self.persist).grid(row=2, column=0, columnspan=4, sticky="w", pady=(0, 8))
        self.tree = ttk.Treeview(self, columns=("name", "path", "enabled"), show="headings", height=12)
        for key, title, width in (("name", "Programa", 150), ("path", "Ruta", 510), ("enabled", "Individual", 90)):
            self.tree.heading(key, text=title); self.tree.column(key, width=width, stretch=(key == "path"))
        self.tree.grid(row=3, column=0, columnspan=3, sticky="nsew")
        bar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview); bar.grid(row=3, column=3, sticky="ns"); self.tree.configure(yscrollcommand=bar.set)
        self.drop = ttk.Label(self, text="Suelta aquí archivos .exe o pulsa Añadir…", anchor="center", padding=9, relief="groove")
        self.drop.grid(row=4, column=0, columnspan=4, sticky="ew", pady=9)
        if DND:
            self.drop.drop_target_register(DND_FILES); self.drop.dnd_bind("<<Drop>>", self.on_drop)
        ttk.Button(self, text="Añadir…", command=self.choose).grid(row=5, column=0, sticky="w")
        ttk.Button(self, text="Activar/desactivar", command=self.toggle).grid(row=5, column=1, sticky="w", padx=8)
        ttk.Button(self, text="Quitar", command=self.remove).grid(row=5, column=2, sticky="e")
        ttk.Separator(self).grid(row=6, column=0, columnspan=4, sticky="ew", pady=14)
        self.start = ttk.Button(self, text="Iniciar bloqueo", command=self.start_guard); self.start.grid(row=7, column=0, sticky="w")
        ttk.Button(self, text="Detener", command=self.stop_guard).grid(row=7, column=1, sticky="w", padx=8)
        ttk.Label(self, textvariable=self.status, font=("Segoe UI", 10, "bold")).grid(row=7, column=2, columnspan=2, sticky="e")
        self.log = tk.Text(self, height=6, state="disabled", font=("Consolas", 9)); self.log.grid(row=8, column=0, columnspan=4, sticky="nsew", pady=(14, 0))
        self.columnconfigure(2, weight=1); self.rowconfigure(3, weight=1)

    def choose(self) -> None:
        self.add(filedialog.askopenfilenames(filetypes=[("Ejecutables", "*.exe")]))

    def on_drop(self, event: object) -> None:
        self.add(self.tk.splitlist(event.data))  # type: ignore[attr-defined]

    def add(self, values: object) -> None:
        known = {canonical(str(x.get("path", ""))) for x in self.items}
        for value in values:  # type: ignore[union-attr]
            path = Path(str(value))
            if path.suffix.lower() == ".exe" and path.is_file() and canonical(path) not in known:
                self.items.append({"path": str(path.resolve()), "enabled": True}); known.add(canonical(path))
        self.persist()

    def selected(self) -> int | None:
        chosen = self.tree.selection()
        return int(chosen[0]) if chosen else None

    def toggle(self) -> None:
        index = self.selected()
        if index is not None:
            self.items[index]["enabled"] = not bool(self.items[index].get("enabled", True)); self.persist()

    def remove(self) -> None:
        index = self.selected()
        if index is not None:
            del self.items[index]; self.persist()

    def persist(self) -> None:
        self.global_mode = self.global_var.get(); save(self.global_mode, self.items); self.refresh()

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for index, item in enumerate(self.items):
            path = str(item.get("path", "")); state = "Sí" if item.get("enabled", True) else "No"
            self.tree.insert("", "end", iid=str(index), values=(Path(path).name, path, state))

    def paths(self) -> set[str]:
        chosen = self.items if self.global_var.get() else [x for x in self.items if x.get("enabled", True)]
        return {canonical(str(x["path"])) for x in chosen if x.get("path")}

    def start_guard(self) -> None:
        paths = self.paths()
        if not paths:
            messagebox.showwarning("Sin ejecutables", "Añade y activa al menos un .exe."); return
        self.guard = DivertGuard(paths, self.events); self.guard.start(); self.start.configure(state="disabled")

    def stop_guard(self) -> None:
        if self.guard: self.guard.close(); self.guard = None
        self.start.configure(state="normal"); self.status.set("Vigilancia detenida")

    def poll_events(self) -> None:
        while not self.events.empty():
            message = self.events.get_nowait(); self.status.set(message)
            self.log.configure(state="normal"); self.log.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n"); self.log.see("end"); self.log.configure(state="disabled")
        self.after(200, self.poll_events)

    def quit_app(self) -> None:
        self.stop_guard(); self.destroy()


def main() -> None:
    if not admin():
        try: elevate()
        except OSError as error: messagebox.showerror("Permisos de administrador", str(error))
        return
    App().mainloop()


if __name__ == "__main__": main()
