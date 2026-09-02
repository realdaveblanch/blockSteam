# Bloqueador de conexiones

Aplicación con interfaz gráfica para bloquear conexiones salientes de ejecutables concretos sin crear ni modificar reglas del Firewall de Windows ni cambiar ajustes de ESET.

## Cómo funciona

La aplicación usa WinDivert mediante `pydivert`: intercepta la operación de socket `connect` del PID que corresponde a cada `.exe` vigilado y la descarta. El proceso sigue abierto; simplemente recibe un error de conexión. El filtro se actualiza mientras la vigilancia está activa para incluir procesos que se abran después.

Se necesita ejecutar como administrador, porque Windows exige privilegios para instalar y abrir el controlador de filtrado. `pydivert` incluye la DLL y controlador WinDivert de 64 bits; ESET puede solicitar confirmación al ver su carga. No se usa `netsh`, no se altera el Firewall de Windows y no se cambian reglas persistentes del sistema.

## Uso

1. Ejecuta la aplicación como administrador.
2. Arrastra ejecutables `.exe` a la zona de la ventana, o usa **Añadir…**.
3. Con *Modo global* activado se bloquean todos los de la lista. Al desactivarlo, solo se bloquean los marcados como *Sí* en la columna *Individual*.
4. Pulsa **Iniciar bloqueo**. **Detener** quita inmediatamente el filtro y restaura la conectividad.

La lista se guarda en `%APPDATA%\\BloqueadorConexiones\\lista.json`.

## Compilar

```powershell
python -m pip install -r requirements.txt
.\\build_exe.ps1
```

El resultado estará en `dist\\BloqueadorConexiones.exe`.
