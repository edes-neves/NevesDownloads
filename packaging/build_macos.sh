#!/usr/bin/env bash
# =============================================================================
# Neves Downloads - Script de build para macOS (.app e .dmg opcional).
#
# Gera um aplicativo .app empacotado e, se `create-dmg` estiver disponível,
# também um instalador .dmg.
#
# Uso:
#   ./packaging/build_macos.sh                 # gera .app em dist/
#   ./packaging/build_macos.sh --dmg           # gera também .dmg
#
# Pré-requisitos:
#   - macOS com Python 3.11+
#   - PyInstaller instalado (pip install pyinstaller)
#   - (opcional) create-dmg: brew install create-dmg
# =============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

APP_NAME="NevesDownloads"
APP_DISPLAY="Neves Downloads"
APP_VERSION="$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml","rb"))["project"]["version"])' 2>/dev/null || echo "1.0.0")"

BUILD_DMG=false
for arg in "$@"; do
    case "$arg" in
        --dmg) BUILD_DMG=true ;;
        --help|-h)
            echo "Uso: $0 [--dmg]"
            echo "  --dmg   Gera também um volume .dmg de instalação"
            exit 0
            ;;
        *)
            echo "Argumento desconhecido: $arg" >&2
            exit 1
            ;;
    esac
done

# ── Python ────────────────────────────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERRO: python3 não encontrado." >&2
    exit 1
fi

if ! python3 -c "import PyInstaller" >/dev/null 2>&1; then
    echo "PyInstaller não encontrado. Instalando..."
    python3 -m pip install pyinstaller
fi

# ── Build ─────────────────────────────────────────────────────────────────────
echo "=== Construindo ${APP_DISPLAY} v${APP_VERSION} para macOS ==="
rm -rf build dist
python3 -m PyInstaller --noconfirm --clean packaging/NevesDownloads.spec -- --onedir

OSA_APP="dist/${APP_NAME}.app"
if [ ! -d "$OSA_APP" ]; then
    # PyInstaller gera a pasta em dist/NevesDownloads (onedir). Montamos o .app.
    if [ -d "dist/${APP_NAME}" ]; then
        echo "Empacotando .app a partir do onedir..."
        mkdir -p "dist/${APP_NAME}.app/Contents/MacOS"
        mkdir -p "dist/${APP_NAME}.app/Contents/Resources"
        cp "dist/${APP_NAME}"/* "dist/${APP_NAME}.app/Contents/MacOS/"
        if [ -f "assets/Icone.png" ]; then
            cp "assets/Icone.png" "dist/${APP_NAME}.app/Contents/Resources/"
        fi
        cat > "dist/${APP_NAME}.app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>${APP_DISPLAY}</string>
    <key>CFBundleDisplayName</key><string>${APP_DISPLAY}</string>
    <key>CFBundleIdentifier</key><string>br.com.neves.downloads</string>
    <key>CFBundleVersion</key><string>${APP_VERSION}</string>
    <key>CFBundleShortVersionString</key><string>${APP_VERSION}</string>
    <key>CFBundleExecutable</key><string>${APP_NAME}</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>LSMinimumSystemVersion</key><string>11.0</string>
    <key>NSHighResolutionCapable</key><true/>
    <key>CFBundleIconFile</key><string>Icone</string>
</dict>
</plist>
EOF
        chmod +x "dist/${APP_NAME}.app/Contents/MacOS/${APP_NAME}"
    else
        echo "ERRO: build onedir não encontrado em dist/${APP_NAME}" >&2
        exit 1
    fi
fi

echo "=== App gerado: ${OSA_APP} ==="

# ── DMG opcional ──────────────────────────────────────────────────────────────
if [ "$BUILD_DMG" = true ]; then
    if command -v create-dmg >/dev/null 2>&1; then
        echo "=== Gerando DMG ==="
        create-dmg \
            --volname "${APP_DISPLAY} ${APP_VERSION}" \
            --window-pos 200 120 \
            --window-size 800 400 \
            --icon-size 100 \
            --app-drop-link 600 185 \
            --icon "${APP_DISPLAY}" 200 190 \
            "dist/${APP_NAME}-${APP_VERSION}.dmg" \
            "${OSA_APP}"
    else
        echo "create-dmg não encontrado. Instale com: brew install create-dmg"
        echo "ou arraste o .app para a pasta Applications."
    fi
fi

echo ""
echo "Build concluído. Artefatos em: $ROOT_DIR/dist/"
ls -la dist/
