#!/usr/bin/env python3
"""
apply_wallpaper.py - Gestor de Wallpapers Glassmorphism para Google Antigravity IDE
Autor: DarwinSin (darwinsin822)
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
    import asyncio
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

CUSTOM_CSS_PATH = os.path.expanduser("~/.gemini/antigravity/custom/wallpaper.css")
DEFAULT_WALLPAPER_DIR = os.path.expanduser("~/Imágenes/WALLPAPERS")
DEVTOOLS_PORT_FILE = os.path.expanduser("~/.config/Antigravity/DevToolsActivePort")

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
        # Si la imagen excede 2880px de ancho, escalar suavemente con Lanczos para optimizar RAM y renderizado
        target_im = im
        if im.width > 2880:
            new_h = int(2880 * im.height / im.width)
            target_im = im.resize((2880, new_h), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        target_im.convert("RGB").save(buf, format="JPEG", quality=93, optimize=True)
        jpeg_bytes = buf.getvalue()
        b64 = base64.b64encode(jpeg_bytes).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"

async def inject_live(css_content):
    if not os.path.exists(DEVTOOLS_PORT_FILE):
        print("ℹ️ Antigravity no tiene puerto DevTools activo (probablemente cerrado). Se cargará al abrir el IDE.")
        return

    try:
        with open(DEVTOOLS_PORT_FILE, "r") as pf:
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
    parser.add_argument("image", nargs="?", help="Ruta de la imagen de wallpaper (JPG, PNG, WebP)")
    parser.add_argument("--list", action="store_true", help="Lista las imágenes disponibles en ~/Imágenes/WALLPAPERS")
    args = parser.parse_args()

    if args.list:
        if os.path.exists(DEFAULT_WALLPAPER_DIR):
            print(f"📁 Wallpapers en {DEFAULT_WALLPAPER_DIR}:")
            for f in sorted(os.listdir(DEFAULT_WALLPAPER_DIR)):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    print(f"  • {f}")
        else:
            print(f"Directorio no encontrado: {DEFAULT_WALLPAPER_DIR}")
        return

    if not args.image:
        parser.print_help()
        sys.exit(1)

    image_path = os.path.abspath(os.path.expanduser(args.image))
    if not os.path.exists(image_path):
        # Intentar en la carpeta de wallpapers por defecto
        alt_path = os.path.join(DEFAULT_WALLPAPER_DIR, args.image)
        if os.path.exists(alt_path):
            image_path = alt_path
        else:
            print(f"❌ Error: La imagen '{args.image}' no fue encontrada.")
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
