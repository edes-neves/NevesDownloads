#!/usr/bin/env bash
# =============================================================================
# Neves Downloads - Script de release automatizado
#
# Uso:
#   ./release.sh              # usa versão de app/core/constants.py
#   ./release.sh 1.2.0        # define versão, atualiza constants.py e publica
#
# O que faz:
#   1. Atualiza APP_VERSION em app/core/constants.py (se versão fornecida)
#   2. Build do binário com PyInstaller
#   3. Cria AppImage
#   4. Commit + tag v<versão>
#   5. Push para GitHub
#   6. Cria GitHub Release com o AppImage
# =============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

APP_NAME="NevesDownloads"

# ── Versão ───────────────────────────────────────────────────────────────────
if [ "${1:-}" != "" ]; then
    NEW_VERSION="$1"
    # Atualiza APP_VERSION em constants.py
    sed -i "s/^APP_VERSION = \".*\"/APP_VERSION = \"${NEW_VERSION}\"/" app/core/constants.py
    echo "Versão atualizada para ${NEW_VERSION}"
fi

APP_VERSION="$(python3 -c "import tomllib; print(tomllib.load(open('app/core/constants.py','rb'))['APP_VERSION'])" 2>/dev/null || grep -oP 'APP_VERSION = "\K[^"]+' app/core/constants.py)"

if [ -z "$APP_VERSION" ]; then
    echo "ERRO: Não foi possível detectar APP_VERSION" >&2
    exit 1
fi

TAG="v${APP_VERSION}"
echo "=== Neves Downloads ${TAG} ==="

# ── Verifica dependências ────────────────────────────────────────────────────
if ! command -v gh >/dev/null 2>&1; then
    echo "ERRO: gh CLI não encontrado. Instale: https://cli.github.com/" >&2
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "ERRO: gh CLI não autenticado. Execute: gh auth login" >&2
    exit 1
fi

# ── Build com PyInstaller ────────────────────────────────────────────────────
echo ""
echo "=== [1/6] Build com PyInstaller ==="
rm -rf build dist
./venv/bin/python -m PyInstaller --noconfirm --clean packaging/NevesDownloads.spec
echo "Binário gerado: dist/${APP_NAME}"

# ── AppImage ─────────────────────────────────────────────────────────────────
echo ""
echo "=== [2/6] Gerando AppImage ==="

APPIMAGETOOL="${APPIMAGETOOL:-}"
if [ -z "$APPIMAGETOOL" ]; then
    for candidate in \
        "$HOME/.local/bin/appimagetool" \
        "/usr/local/bin/appimagetool" \
        "/opt/appimagetool/appimagetool" \
        "$ROOT_DIR/.tools/appimagetool"; do
        if [ -x "$candidate" ]; then
            APPIMAGETOOL="$candidate"
            break
        fi
    done
fi

if [ -z "$APPIMAGETOOL" ] || ! command -v "$APPIMAGETOOL" >/dev/null 2>&1; then
    echo "appimagetool não encontrado. Baixando..."
    mkdir -p "$ROOT_DIR/.tools"
    APPIMAGETOOL="$ROOT_DIR/.tools/appimagetool"
    curl -L -o "$APPIMAGETOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

APPDIR="$ROOT_DIR/dist/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/512x512/apps"
cp "$ROOT_DIR/dist/${APP_NAME}" "$APPDIR/usr/bin/${APP_NAME}"
chmod +x "$APPDIR/usr/bin/${APP_NAME}"

cat > "$APPDIR/neves-downloads.desktop" <<EOF
[Desktop Entry]
Name=Neves Downloads
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

if [ -f "$ROOT_DIR/assets/Icone.png" ]; then
    cp "$ROOT_DIR/assets/Icone.png" "$APPDIR/neves-downloads.png"
    cp "$ROOT_DIR/assets/Icone.png" "$APPDIR/usr/share/icons/hicolor/512x512/apps/neves-downloads.png"
fi

cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/NevesDownloads" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

APPIMAGE_PATH="$ROOT_DIR/dist/${APP_NAME}-${APP_VERSION}.AppImage"

RUN_ARGS=()
if ! grep -q "fuse" /proc/filesystems 2>/dev/null && ! [ -e /dev/fuse ]; then
    RUN_ARGS=(--appimage-extract-and-run)
fi

"$APPIMAGETOOL" "${RUN_ARGS[@]}" "$APPDIR" "$APPIMAGE_PATH"
echo "AppImage gerado: $APPIMAGE_PATH"
ls -lah "$APPIMAGE_PATH"

# ── Commit + Tag ─────────────────────────────────────────────────────────────
echo ""
echo "=== [3/6] Commit + Tag ==="
git add -A
if git diff --cached --quiet; then
    echo "Nada para commitar."
else
    git commit -m "chore: release ${TAG}"
fi

if git tag -l | grep -q "^${TAG}$"; then
    echo "Tag ${TAG} já existe. Atualizando..."
    git tag -d "$TAG"
fi
git tag -a "$TAG" -m "Release ${TAG}"
echo "Tag ${TAG} criada."

# ── Push ─────────────────────────────────────────────────────────────────────
echo ""
echo "=== [4/6] Push ==="
git push origin master --tags
echo "Push concluído."

# ── GitHub Release ───────────────────────────────────────────────────────────
echo ""
echo "=== [5/6] Criando GitHub Release ==="
if gh release view "$TAG" >/dev/null 2>&1; then
    echo "Release ${TAG} já existe. Atualizando..."
    gh release delete "$TAG" --yes --cleanup-tag
fi

gh release create "$TAG" \
    --title "${TAG}" \
    --notes "## Neves Downloads ${TAG}

### Como usar
1. Baixe o \`${APP_NAME}-${APP_VERSION}.AppImage}\`
2. Torne executável: \`chmod +x ${APP_NAME}-${APP_VERSION}.AppImage\`
3. Execute: \`./${APP_NAME}-${APP_VERSION}.AppImage\`" \
    "$APPIMAGE_PATH"

echo ""
echo "=== [6/6] Concluído ==="
echo "Release: https://github.com/$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null)/releases/tag/${TAG}"
echo "AppImage: ${APPIMAGE_PATH}"
