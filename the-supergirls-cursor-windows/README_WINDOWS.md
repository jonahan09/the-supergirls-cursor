# SuperGirls Pet v11 — Windows

Versión adaptada del proyecto original de Linux para Windows 10/11.

## Qué se cambió

- Se eliminó la dependencia de `python-xlib`, `xdotool` y `xwininfo`.
- El cursor se obtiene con PyQt6 de forma global.
- La detección de la ventana bajo el cursor y la función de **posarse en ventanas** usan la API nativa de Windows (`user32.dll`) mediante `ctypes`.
- Se mantienen las 5 skins, sprites, aura, animaciones, seguimiento, arrastre, cambio de tamaño y selector.
- El código funciona desde una carpeta normal y también al empaquetarlo con PyInstaller.

## Forma fácil de abrirlo

1. Instala Python 3.11, 3.12 o 3.13 para Windows si todavía no lo tienes.
2. Durante la instalación de Python marca **Add python.exe to PATH**.
3. Haz doble clic en `INSTALAR_Y_ABRIR.bat`.
4. La primera vez instalará PyQt6; después abrirá la mascota.

Para las siguientes veces puedes usar `EJECUTAR.bat`.

## Crear un .exe

En una PC con Windows, haz doble clic en `CREAR_EXE.bat`.

Al terminar encontrarás:

`dist\SuperGirls Pet v11\SuperGirls Pet v11.exe`

PyInstaller debe ejecutarse en Windows para producir un `.exe` de Windows; por eso este paquete incluye el script de compilación en lugar de un ejecutable precompilado.

## Controles

- **Clic izquierdo + arrastrar:** mover manualmente la chica.
- **Clic derecho:** abrir el menú.
- Desde el menú puedes cambiar skin, tamaño, aura, animación y tipo de vuelo.
- Si el cursor permanece quieto sobre una ventana durante aproximadamente 0.65 s, la chica intenta posarse en el borde superior de esa ventana.

## Archivos principales

- `supergirls_pet.py`: versión para Windows.
- `skins/`: sprites de las 5 chicas.
- `skins.json`: nombres de las skins.
- `requirements.txt`: dependencia de PyQt6.
- `INSTALAR_Y_ABRIR.bat`: instala dependencia y abre el programa.
- `EJECUTAR.bat`: abre el programa si ya está instalado.
- `CREAR_EXE.bat`: genera el ejecutable con PyInstaller.
