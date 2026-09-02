$ErrorActionPreference = 'Stop'

py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name BloqueadorConexiones --collect-all pydivert --collect-all tkinterdnd2 steam_blocker.py
Write-Host "Listo: $PWD\dist\BloqueadorConexiones.exe"
