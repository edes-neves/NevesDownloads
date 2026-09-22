# -*- mode: python ; coding: utf-8 -*-
"""
Especificacao do PyInstaller para o Neves Downloads.

Gera um executavel unico (onefile) com o aplicativo e suas dependencias.

Uso (a partir da raiz do projeto):
    pyinstaller packaging/NevesDownloads.spec

Para gerar todos os arquivos separados (modo onedir, util para AppImage):
    pyinstaller packaging/NevesDownloads.spec -- --onedir
"""

import os
import shutil
import sys
from pathlib import Path

# Deteccao de modo (onefile padrao; --onedir via arg extra).
MODE_ONEDIR = "--onedir" in sys.argv
if MODE_ONEDIR:
    sys.argv.remove("--onedir")

# Diretorio raiz do projeto.
project_root = Path(SPECPATH).resolve()
if not (project_root / "main.py").exists():
    project_root = Path(".").resolve()

APP_NAME = "NevesDownloads"
APP_VERSION = "1.0.0"

# ── Assets ──
assets_dir = project_root / "assets"
datas = []
if assets_dir.exists():
    datas.append((str(assets_dir), "assets"))

# ── FFmpeg ──
# Inclui o ffmpeg junto do executável quando disponível no PATH da máquina
# de build (relê ffmpeg.exe no Windows), dispensando instalação separada.
ffmpeg_bin = shutil.which("ffmpeg")
binaries = []
if ffmpeg_bin:
    binaries.append((ffmpeg_bin, "."))

icon_path = assets_dir / "Icone.png"
icon = str(icon_path) if icon_path.exists() else None


def collect_ytdlp():
    """Coleta dados e submodulos do yt-dlp de forma robusta."""
    from PyInstaller.utils.hooks import collect_submodules, collect_data_files

    ydl_data = collect_data_files("yt_dlp")
    ydl_sub = collect_submodules("yt_dlp")
    return ydl_data, ydl_sub


_ydl_datas, _ydl_hidden = collect_ytdlp()

hiddenimports = [
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "pystray",
] + _ydl_hidden

datas += _ydl_datas

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter.test", "unittest", "pydoc"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

if MODE_ONEDIR:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        icon=icon,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        icon=icon,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

if MODE_ONEDIR:
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )
