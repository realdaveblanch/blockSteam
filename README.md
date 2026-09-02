# Connection Blocker

> A Windows desktop application that blocks outbound connection attempts from selected executables—without creating Windows Firewall rules and without terminating the process.

[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D4?logo=windows)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Developer:** [realdaveblanch](https://github.com/realdaveblanch)
**Language:** English below · Español más abajo

---

## English

### What it does

Connection Blocker lets you create a local list of `.exe` files and deny their outbound connection attempts while leaving their processes running. Add executables by drag and drop or with the file picker, then choose one of two modes:

| Mode | Behaviour |
| --- | --- |
| **Global mode** | Blocks connections for every executable in the list. |
| **Per-app mode** | Blocks only entries individually marked as enabled. |

The list is stored locally at `%APPDATA%\BloqueadorConexiones\lista.json` and is never uploaded.

### How it works

The application uses the [WinDivert](https://reqrypt.org/windivert.html) driver through `pydivert`. It intercepts the Windows socket `connect` event for the selected executable's active process ID and discards it. The executable remains running and receives a connection failure instead.

This project does **not** use `netsh`, create or edit Windows Firewall rules, change ESET settings, or kill monitored processes. Administrator rights are required because Windows requires them to load the packet-filtering driver. Security software, including ESET, may ask you to approve the driver the first time it is used.

> [!IMPORTANT]
> The filter is active only while Connection Blocker is running and **Iniciar bloqueo / Start blocking** is active. Stop the guard or close the app to restore normal connectivity immediately.

### Features

- Drag-and-drop `.exe` files directly into the UI.
- Add, remove, and individually enable or disable executable entries.
- Global and per-application blocking modes.
- Live in-app event log.
- Persistent local configuration.
- Single-file Windows executable build.
- No Windows Firewall rule management.

### Quick start

1. Download or build `BloqueadorConexiones.exe`.
2. Right-click it and select **Run as administrator**.
3. Drag one or more `.exe` files into the drop area, or select **Añadir… / Add…**.
4. Pick your blocking mode.
5. Select **Iniciar bloqueo / Start blocking**.
6. Keep the application open for as long as you want the rule to apply.

### Adding Steam executables

The default Steam installation folder is:

```text
C:\Program Files (x86)\Steam
```

Open that folder in Explorer and drag the desired executable onto Connection Blocker. The following executables were found in the root Steam folder on this machine:

| Executable | Suggested use |
| --- | --- |
| `steam.exe` | Main Steam client. Add this first when you want to block Steam's own network activity. |
| `gameoverlayui64.exe` | Steam Overlay. Add it if the overlay is also making connections you want blocked. |
| `streaming_client.exe` | Steam Remote Play / streaming client. Add only if you want to block Remote Play connections. |
| `steamerrorreporter.exe`, `steamerrorreporter64.exe` | Optional crash/error reporting components. |
| `steamsysinfo.exe` | Optional system-information helper. |

Avoid adding maintenance tools such as `uninstall.exe` unless you specifically need to test them. Steam can launch additional helper executables from subfolders; if an individual feature still connects, find the responsible `.exe` in Task Manager and add that exact file too.

### Build from source

Prerequisites:

- Windows 10 or Windows 11
- Python 3.10 or newer, with the `py` launcher available
- Administrator rights when running the blocker

```powershell
git clone https://github.com/blanchtrap/blockSteam.git
cd blockSteam
py -m pip install -r requirements.txt
py steam_blocker.py
```

Create a standalone executable:

```powershell
.\build_exe.ps1
```

The output is `dist\BloqueadorConexiones.exe`. Generated output is ignored by Git and should be attached to GitHub Releases, not committed.

### Project structure

```text
steam_blocker.py   # Tkinter UI and the WinDivert-based guard
requirements.txt   # Python dependencies
build_exe.ps1      # PyInstaller build script
CONTRIBUTING.md    # Contribution guidelines
SECURITY.md        # Vulnerability-reporting policy
LICENSE            # MIT license
```

### Contributing and security

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Report security issues privately as described in [SECURITY.md](SECURITY.md).

---

## Español

### Qué hace

Connection Blocker es una aplicación de escritorio para Windows que permite crear una lista local de ejecutables `.exe` y bloquear sus intentos de conexión saliente sin cerrar el proceso.

| Modo | Comportamiento |
| --- | --- |
| **Modo global** | Bloquea las conexiones de todos los ejecutables de la lista. |
| **Modo individual** | Solo bloquea los elementos activados de forma individual. |

La lista se guarda únicamente en `%APPDATA%\BloqueadorConexiones\lista.json`; no se sube a Internet.

### Funcionamiento

La aplicación usa el controlador [WinDivert](https://reqrypt.org/windivert.html) a través de `pydivert`. Intercepta el evento de socket `connect` del PID activo de cada ejecutable seleccionado y lo descarta. El programa continúa abierto, pero recibe un error de conexión.

No usa `netsh`, no crea ni modifica reglas del Firewall de Windows, no cambia ajustes de ESET y no finaliza procesos. Necesita permisos de administrador porque Windows los exige para cargar el controlador de filtrado. ESET puede pedir confirmación la primera vez: revísala y permite únicamente el componente asociado a la aplicación de confianza.

> [!IMPORTANT]
> El bloqueo solo está activo mientras la aplicación siga abierta y hayas pulsado **Iniciar bloqueo**. Pulsa **Detener** o cierra la aplicación para restaurar la conectividad.

### Uso rápido

1. Ejecuta `BloqueadorConexiones.exe` como administrador.
2. Arrastra ejecutables `.exe` a la zona indicada, o pulsa **Añadir…**.
3. Elige modo global o individual.
4. Pulsa **Iniciar bloqueo**.
5. Mantén la aplicación abierta mientras quieras conservar el bloqueo.

### Añadir ejecutables de Steam

La carpeta predeterminada de Steam es:

```text
C:\Program Files (x86)\Steam
```

Abre esa ruta en el Explorador y arrastra el `.exe` que quieras a la aplicación. En la raíz de esa carpeta se han encontrado estos ejecutables:

| Ejecutable | Cuándo añadirlo |
| --- | --- |
| `steam.exe` | Cliente principal de Steam; es el primer ejecutable que conviene añadir. |
| `gameoverlayui64.exe` | Overlay de Steam, si también quieres impedir sus conexiones. |
| `streaming_client.exe` | Remote Play / streaming de Steam. |
| `steamerrorreporter.exe`, `steamerrorreporter64.exe` | Componentes opcionales de informes de errores. |
| `steamsysinfo.exe` | Ayudante opcional de información del sistema. |

No hace falta añadir `uninstall.exe` ni otras utilidades de mantenimiento. Steam puede abrir ejecutables auxiliares en subcarpetas; si una función concreta sigue conectándose, localiza su proceso en el Administrador de tareas y añade ese `.exe` exacto.

### Compilar desde el código fuente

```powershell
py -m pip install -r requirements.txt
.\build_exe.ps1
```

El ejecutable generado estará en `dist\BloqueadorConexiones.exe`. No subas `build/`, `dist/` ni configuraciones locales al repositorio.

### Licencia

Este proyecto está bajo la [licencia MIT](LICENSE). Copyright © 2026 realdaveblanch.
