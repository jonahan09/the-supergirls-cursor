#!/usr/bin/env bash
set -e

APP_DIR="$HOME/.local/share/supergirls-pet-v11"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "Instalando dependencias..."
sudo dnf install -y python3-pyqt6 python3-xlib xdotool xorg-x11-utils

echo "Eliminando accesos directos antiguos de SuperGirls Pet..."
rm -f "$DESKTOP_DIR"/supergirls-pet-v4.desktop
rm -f "$DESKTOP_DIR"/supergirls-pet-v5.desktop
rm -f "$DESKTOP_DIR"/supergirls-pet-v6.desktop
rm -f "$DESKTOP_DIR"/supergirls-pet-v7.desktop
rm -f "$DESKTOP_DIR"/supergirls-pet-v8.desktop
rm -f "$DESKTOP_DIR"/supergirls-pet-v11.desktop

mkdir -p "$APP_DIR" "$DESKTOP_DIR"
rm -rf "$APP_DIR/skins"

cp supergirls_pet.py "$APP_DIR/supergirls_pet.py"
cp skins.json "$APP_DIR/skins.json"
cp -r skins "$APP_DIR/skins"
chmod +x "$APP_DIR/supergirls_pet.py"

cat > "$DESKTOP_DIR/supergirls-pet-v11.desktop" <<EOF
[Desktop Entry]
Name=SuperGirls Pet v11
Comment=5 chicas animadas con aura por color y opciones extra
Exec=env QT_QPA_PLATFORM=xcb python3 $APP_DIR/supergirls_pet.py
Icon=applications-games
Terminal=false
Type=Application
Categories=Game;Utility;
StartupNotify=false
EOF

chmod +x "$DESKTOP_DIR/supergirls-pet-v11.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

echo
echo "LISTO."
echo "Abre exactamente: SuperGirls Pet v11"
