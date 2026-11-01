#!/usr/bin/env python3
"""
apply_wallpaper.py - Gestor de Wallpapers Glassmorphism para Google Antigravity IDE
Soporte para directrices XDG, distribuciones Debian/Ubuntu/Mint y Arch Linux (AUR).
Autor original: DarwinSin (darwinsin822)
Refactorización de compatibilidad y portabilidad: Kineyo
Licencia: MIT

Uso:
    python3 apply_wallpaper.py "/ruta/a/la/imagen.jpg"
    python3 apply_wallpaper.py --list
"""

import os
import sys
import json
import base64
import argparse
import urllib.request
from PIL import Image
import io

try:
    from paths import get_wallpaper_dirs, get_devtools_port_file, get_custom_css_path
except ImportError:
    from scripts.paths import get_wallpaper_dirs, get_devtools_port_file, get_custom_css_path

try:
    import asyncio
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

CUSTOM_CSS_PATH = get_custom_css_path()

def generate_glassmorphism_css(data_uri, wallpaper_name):
    return f"""/* ======================================================================
   Antigravity IDE — Wallpaper Glassmorphism (Tailwind & Electron Native)
   Generado automáticamente por apply_wallpaper.py
   Wallpaper: {wallpaper_name}
   ====================================================================== */

:root {{
  --background: rgba(12, 14, 18, 0.65) !important;
  --color-background: rgba(12, 14, 18, 0.65) !important;
  --sidebar: rgba(14, 16, 22, 0.72) !important;
  --color-sidebar-secondary: rgba(18, 20, 28, 0.70) !important;
  --card: rgba(16, 18, 24, 0.70) !important;
  --color-card: rgba(16, 18, 24, 0.70) !important;
}}

/* Fondo base de la ventana y HTML */
html,
body {{
  background-image: url("{data_uri}") !important;
  background-size: cover !important;
  background-position: center center !important;
  background-attachment: fixed !important;
  background-repeat: no-repeat !important;
}}

/* Contenedor principal de la aplicación Antigravity */
.bg-background,
[class*="bg-background"] {{
  background-color: transparent !important;
  background-image: url("{data_uri}") !important;
  background-size: cover !important;
  background-position: center center !important;
  background-attachment: fixed !important;
}}

/* Sidebar y paneles de navegación con Glassmorphism translúcido */
.bg-sidebar,
[class*="bg-sidebar"] {{
  background-color: rgba(12, 14, 20, 0.72) !important;
  backdrop-filter: blur(14px) !important;
  -webkit-backdrop-filter: blur(14px) !important;
}}

/* Tarjetas, burbujas de diálogo, chats y paneles secundarios */
.bg-card,
[class*="bg-card"] {{
  background-color: rgba(16, 18, 24, 0.68) !important;
  backdrop-filter: blur(10px) !important;
  -webkit-backdrop-filter: blur(10px) !important;
}}

/* Barra superior / Header / Ventana */
.h-screen > .shrink-0,
.h-screen > .shrink-0 > div {{
  background-color: rgba(10, 12, 16, 0.80) !important;
  backdrop-filter: blur(16px) !important;
  -webkit-backdrop-filter: blur(16px) !important;
}}

/* Área central de trabajo / Chat / Editor */
.flex-1.flex.min-h-0 > div {{
  background-color: rgba(12, 14, 18, 0.60) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}}

/* Separadores y bordes sutiles transparentes estilo glass */
.bg-border,
.border-border,
[class*="border-border"] {{
  border-color: rgba(255, 255, 255, 0.08) !important;
}}

/* Preservar legibilidad absoluta del texto y elementos interactivos */
.text-foreground,
p, span, h1, h2, h3, h4, h5, h6, pre, code, button, input, textarea {{
  opacity: 1 !important;
}}
"""

def optimize_image_to_data_uri(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"No existe la imagen: {image_path}")

    with Image.open(image_path) as im:
        buf = io.BytesIO()
        im.convert("RGB").save(buf, format="JPEG", quality=93, optimize=True)
        jpeg_bytes = buf.getvalue()
        b64 = base64.b64encode(jpeg_bytes).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"

async def inject_live(css_content):
    port_file = get_devtools_port_file()
    if not os.path.exists(port_file):
        print("ℹ️ Antigravity no tiene puerto DevTools activo (probablemente cerrado). Se cargará al abrir el IDE.")
        return

    try:
        with open(port_file, "r") as pf:
            port = pf.readline().strip()
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as r:
            pages = json.loads(r.read())
        if not pages:
            return
        ws_url = pages[0]["webSocketDebuggerUrl"]
        async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
            js = f"""
            (function() {{
                var STYLE_ID = 'agy-wallpaper-css';
                var el = document.getElementById(STYLE_ID);
                if (el) el.remove();
                var style = document.createElement('style');
                style.id = STYLE_ID;
                style.textContent = {json.dumps(css_content)};
                (document.head || document.documentElement).appendChild(style);
                return true;
            }})()
            """
            msg = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}
            await ws.send(json.dumps(msg))
            resp = await ws.recv()
            print("🚀 Wallpaper inyectado en vivo en la ventana activa de Antigravity.")
    except Exception as e:
        print(f"ℹ️ Inyección en caliente omitida: {e}")

def main():
    parser = argparse.ArgumentParser(description="Aplica un wallpaper con efecto Glassmorphism a Google Antigravity IDE.")
    parser.add_argument("image", nargs="?", help="Ruta o nombre del archivo de imagen (JPG, PNG, WebP)")
    parser.add_argument("--list", action="store_true", help="Lista las imágenes disponibles en las carpetas de imágenes detectadas")
    args = parser.parse_args()

    wallpaper_dirs = get_wallpaper_dirs()

    if args.list:
        if not wallpaper_dirs:
            print("❌ No se detectaron carpetas de imágenes en el sistema.")
            return
        found_any = False
        for wdir in wallpaper_dirs:
            if os.path.exists(wdir):
                files = [f for f in sorted(os.listdir(wdir)) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                if files:
                    found_any = True
                    print(f"📁 Wallpapers en {wdir}:")
                    for f in files:
                        print(f"  • {f}")
        if not found_any:
            print(f"ℹ️ No se encontraron imágenes en las carpetas inspeccionadas: {', '.join(wallpaper_dirs)}")
        return

    if not args.image:
        parser.print_help()
        sys.exit(1)

    image_path = os.path.abspath(os.path.expanduser(args.image))
    if not os.path.exists(image_path):
        # Buscar en las carpetas de imágenes detectadas (XDG / Pictures / etc.)
        found = False
        for wdir in wallpaper_dirs:
            alt_path = os.path.join(wdir, args.image)
            if os.path.exists(alt_path):
                image_path = alt_path
                found = True
                break
        if not found:
            print(f"❌ Error: La imagen '{args.image}' no fue encontrada.")
            print(f"🔍 Carpetas inspeccionadas: {', '.join(wallpaper_dirs)}")
            sys.exit(1)

    print(f"🖼️ Procesando wallpaper: {os.path.basename(image_path)}...")
    data_uri = optimize_image_to_data_uri(image_path)
    css_content = generate_glassmorphism_css(data_uri, os.path.basename(image_path))

    os.makedirs(os.path.dirname(CUSTOM_CSS_PATH), exist_ok=True)
    with open(CUSTOM_CSS_PATH, "w") as f:
        f.write(css_content)
    print(f"✅ Estilo persistente guardado en: {CUSTOM_CSS_PATH}")

    if WEBSOCKETS_AVAILABLE:
        asyncio.run(inject_live(css_content))
    else:
        print("ℹ️ websockets no disponible. El cambio será visible al reiniciar Antigravity.")

    print("✨ ¡Wallpaper Glassmorphism establecido con éxito!")

if __name__ == "__main__":
    main()
