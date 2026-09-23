#!/usr/bin/env bash
# =============================================================================
# Neves Downloads - Script de build para Linux (AppImage / binário).
#
# Gera um empacotamento com PyInstaller e, opcionalmente, um AppImage
# (via appimagetool) quando `--appimage` é informado.
#
# Uso:
#   ./packaging/build_linux.sh                 # gera binário em dist/
#   ./packaging/build_linux.sh --appimage      # gera .AppImage em dist/
#   ./packaging/build_linux.sh --onedir        # gera pasta onedir em dist/
#
# Pré-requisitos:
#   - Python 3.11+ com venv ativado (dependências já instaladas)
#   - PyInstaller instalado (pip install pyinstaller)
#   - Para AppImage: appimagetool (veja --help) e libfuse2
#
# FFmpeg:
#   Por padrão o script baixa um ffmpeg ESTÁTICO (johnvansickle) para
#   .tools/ffmpeg-static e o empacota, garantindo que rode em qualquer distro
#   (ex.: BigLinux/GNOME), mesmo quando a máquina de build tem um ffmpeg
#   dinâmico incompatível. Para desabilitar: SKIP_STATIC_FFMPEG=1 (usa o do
#   sistema) ou informe o seu próprio com FFMPEG_STATIC=/caminho/do/ffmpeg.
# =============================================================================

set -euo pipefail

# ── Configuração ─────────────────────────────────────────────────────────────
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

APP_NAME="NevesDownloads"
APP_VERSION="$(python packaging/get_version.py 2>/dev/null || echo "0.0.0")"
APP_CAPITALIZED="Neves Downloads"

BUILD_APPIMAGE=false
BUILD_ONEDIR=false

# ── Parsing de argumentos ────────────────────────────────────────────────────
for arg in "$@"; do
    case "$arg" in
        --appimage) BUILD_APPIMAGE=true ;;
        --onedir)   BUILD_ONEDIR=true ;;
        --help|-h)
            echo "Uso: $0 [--appimage] [--onedir]"
            echo "  --appimage   Gera também um AppImage (dist/NevesDownloads-<versao>.AppImage)"
            echo "  --onedir     Gera pasta com todos os arquivos (modo onedir)"
            echo "Sem flags geramos um binário único (onefile) em dist/NevesDownloads"
            exit 0
            ;;
        *)
            echo "Argumento desconhecido: $arg" >&2
            exit 1
            ;;
    esac
done

# ── Verificação de dependências ──────────────────────────────────────────────
if ! command -v python >/dev/null 2>&1; then
    echo "ERRO: Python não encontrado. Use um venv com as dependências instaladas." >&2
    exit 1
fi

if ! python -c "import PyInstaller" >/dev/null 2>&1; then
    echo "PyInstaller não encontrado. Instalando..."
    python -m pip install pyinstaller
fi

# ── FFmpeg estático (portável) ────────────────────────────────────────────────
# Baixa um ffmpeg estático (johnvansickle) e o usa no empacotamento via env
# FFMPEG_STATIC. A causa do "ffmpeg não roda" no AppImage em algumas distros
# (ex.: BigLinux/GNOME) é o ffmpeg dinâmico da máquina de build (Ubuntu) não
# executar lá; um estático resolve de forma definitiva.
SKIP_STATIC_FFMPEG="${SKIP_STATIC_FFMPEG:-0}"
if [ "${SKIP_STATIC_FFMPEG}" = "1" ]; then
    echo "SKIP_STATIC_FFMPEG=1: usando o ffmpeg do sistema (portabilidade reduzida)."
    export FFMPEG_STATIC=""
elif [ -n "${FFMPEG_STATIC:-}" ]; then
    if [ ! -x "$FFMPEG_STATIC" ]; then
        echo "ERRO: FFMPEG_STATIC='$FFMPEG_STATIC' não é um binário executável." >&2
        exit 1
    fi
    echo "Usando FFmpeg estático informado: $FFMPEG_STATIC"
    export FFMPEG_STATIC
else
    FFMPEG_TOOLS_DIR="$ROOT_DIR/.tools"
    FFMPEG_STATIC="$FFMPEG_TOOLS_DIR/ffmpeg-static"
    if [ ! -x "$FFMPEG_STATIC" ]; then
        echo "=== Baixando FFmpeg estático (johnvansickle) ==="
        command -v curl >/dev/null 2>&1 || { echo "ERRO: curl não instalado. Instale o curl ou defina FFMPEG_STATIC." >&2; exit 1; }
        case "$(uname -m)" in
            x86_64|amd64) FF_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz" ;;
            aarch64|arm64) FF_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz" ;;
            *)
                echo "WARN: sem ffmpeg estático para $(uname -m); usando o do sistema (pode não ser portável)." >&2
                FF_URL=""
                ;;
        esac
        if [ -n "${FF_URL:-}" ]; then
            mkdir -p "$FFMPEG_TOOLS_DIR"
            FF_TARBALL="$FFMPEG_TOOLS_DIR/ffmpeg-static.tar.xz"
            if curl -fL --retry 2 -o "$FF_TARBALL" "$FF_URL"; then
                tar -xJf "$FF_TARBALL" -C "$FFMPEG_TOOLS_DIR"
                rm -f "$FF_TARBALL"
                find "$FFMPEG_TOOLS_DIR" -maxdepth 2 -type f -name ffmpeg \
                    -exec cp -f {} "$FFMPEG_STATIC" \;
                chmod +x "$FFMPEG_STATIC"
                if ! "$FFMPEG_STATIC" -version >/dev/null 2>&1; then
                    echo "ERRO: ffmpeg estático baixado não pode ser executado." >&2
                    exit 1
                fi
            else
                rm -f "$FF_TARBALL"
                echo "WARN: falha ao baixar ffmpeg estático; usando o do sistema (portabilidade reduzida)." >&2
            fi
        fi
    fi
    if [ -x "$FFMPEG_STATIC" ]; then
        echo "Usando FFmpeg estático: $FFMPEG_STATIC ($("$FFMPEG_STATIC" -version 2>/dev/null | head -n1))"
        export FFMPEG_STATIC
    else
        export FFMPEG_STATIC=""
    fi
fi

# ── Build com PyInstaller ────────────────────────────────────────────────────
echo "=== Construindo ${APP_NAME} v${APP_VERSION} com PyInstaller ==="

EXTRA_SPEC=""
if [ "$BUILD_ONEDIR" = true ]; then
    EXTRA_SPEC="-- --onedir"
fi

rm -rf build dist
python -m PyInstaller --noconfirm --clean packaging/NevesDownloads.spec $EXTRA_SPEC

if [ "$BUILD_ONEDIR" = true ] && [ -d "dist/${APP_NAME}" ]; then
    echo "Build onedir gerado em dist/${APP_NAME}/"
fi

echo "=== Build PyInstaller concluído ==="
ls -la dist/

# ── AppImage (opcional) ──────────────────────────────────────────────────────
if [ "$BUILD_APPIMAGE" = true ]; then
    echo ""
    echo "=== Gerando AppImage ==="

    # Localiza appimagetool (env ou caminho comum)
    APPIMAGETOOL="${APPIMAGETOOL:-}"
    if [ -z "$APPIMAGETOOL" ]; then
        for candidate in \
            "$HOME/.local/bin/appimagetool" \
            "/usr/local/bin/appimagetool" \
            "/opt/appimagetool/appimagetool"; do
            if [ -x "$candidate" ]; then
                APPIMAGETOOL="$candidate"
                break
            fi
        done
    fi

    if [ -z "$APPIMAGETOOL" ] || ! command -v "$APPIMAGETOOL" >/dev/null 2>&1; then
        echo "appimagetool não encontrado. Baixando para x86_64..."
        APPIMAGETOOL_DIR="$ROOT_DIR/.tools"
        mkdir -p "$APPIMAGETOOL_DIR"
        APPIMAGETOOL="$APPIMAGETOOL_DIR/appimagetool"
        if ! command -v curl >/dev/null 2>&1; then
            echo "ERRO: curl não instalado." >&2
            exit 1
        fi
        curl -L -o "$APPIMAGETOOL" \
            "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
        chmod +x "$APPIMAGETOOL"
    fi

    # Prepara o AppDir (do onefile ou onedir).
    APPDIR="$ROOT_DIR/dist/AppDir"
    rm -rf "$APPDIR"
    mkdir -p "$APPDIR/usr/bin"
    mkdir -p "$APPDIR/usr/share/applications"
    mkdir -p "$APPDIR/usr/share/icons/hicolor/512x512/apps"

    if [ -d "$ROOT_DIR/dist/${APP_NAME}" ]; then
        cp -r "$ROOT_DIR/dist/${APP_NAME}/"* "$APPDIR/usr/bin/"
    else
        cp "$ROOT_DIR/dist/${APP_NAME}" "$APPDIR/usr/bin/${APP_NAME}"
    fi

    # O ffmpeg empacotado (estático) é copiado junto; garante execução.
    if [ -f "$APPDIR/usr/bin/ffmpeg" ]; then
        chmod +x "$APPDIR/usr/bin/ffmpeg"
    fi

    # Desktop Entry
    cat > "$APPDIR/neves-downloads.desktop" <<EOF
[Desktop Entry]
Name=${APP_CAPITALIZED}
Comment=Downloader de vídeos e playlists
Exec=${APP_NAME} %U
Icon=neves-downloads
Terminal=false
Type=Application
Categories=AudioVideo;
StartupWMClass=NevesDownloads
MimeType=x-scheme-handler/http;x-scheme-handler/https;
EOF
    cp "$APPDIR/neves-downloads.desktop" "$APPDIR/usr/share/applications/neves-downloads.desktop"

    # Ícone
    if [ -f "$ROOT_DIR/assets/Icone.png" ]; then
        cp "$ROOT_DIR/assets/Icone.png" "$APPDIR/neves-downloads.png"
        cp "$ROOT_DIR/assets/Icone.png" "$APPDIR/usr/share/icons/hicolor/512x512/apps/neves-downloads.png"
    fi

    # AppRun
    cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/NevesDownloads" "$@"
EOF
    chmod +x "$APPDIR/AppRun"
    chmod +x "$APPDIR/usr/bin/${APP_NAME}"

    # FUSE disponível? Se não, executa o appimagetool via extração.
    # O kernel pode reportar "fuse" em /proc/filesystems sem a biblioteca
    # user-space, então verificamos a presença de libfuse.so.2 de fato.
    RUN_ARGS=()
    if ! ldconfig -p 2>/dev/null | grep -q "libfuse\.so\.2"; then
        echo "libfuse.so.2 indisponível - usando extração para executar o appimagetool."
        RUN_ARGS=(--appimage-extract-and-run)
    fi

    echo "Gerando AppImage..."
    "$APPIMAGETOOL" "${RUN_ARGS[@]}" "$APPDIR" "$ROOT_DIR/dist/${APP_NAME}-${APP_VERSION}.AppImage"

    echo ""
    echo "=== AppImage gerado ==="
    ls -lah "$ROOT_DIR/dist/"*.AppImage
fi

echo ""
echo "Build concluído. Artefatos em: $ROOT_DIR/dist/"
