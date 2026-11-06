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
   Antigravity IDE — Wallpaper Glassmorphism & High-Contrast Readability
   Wallpaper: {wallpaper_name}
   ====================================================================== */

/* Limpieza de fondos anidados para evitar multiplicación de opacidades y oscurecimiento */
.agy-shell,
.agy-sheet,
[data-split-root],
[data-testid="aux-pane-split"],
[data-testid="aux-pane-split"] > div,
.flex-1.flex.min-h-0,
.flex-1.flex.min-h-0 > div {{
  background-color: transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}}

/* Fondo wallpaper con viñeta para balance óptimo de saturación */
html,
body,
.bg-background,
[class*="bg-background"] {{
  background: #080a10 !important;
  background-image: linear-gradient(rgba(10, 14, 22, 0.45), rgba(10, 14, 22, 0.65)), url("{data_uri}") !important;
  background-size: cover !important;
  background-position: center center !important;
  background-attachment: fixed !important;
  background-repeat: no-repeat !important;
}}

/* Sidebar y navegación con Glassmorphism suave */
.bg-sidebar,
[class*="bg-sidebar"],
[data-testid="sidebar"] {{
  background-color: rgba(10, 14, 24, 0.78) !important;
  backdrop-filter: blur(16px) !important;
  -webkit-backdrop-filter: blur(16px) !important;
}}

/* Panel principal y área de conversación: translúcido pero con contraste para lectura */
.agy-sheet,
.browser-hole-opaque {{
  background-color: rgba(9, 12, 18, 0.45) !important;
}}

/* Tarjetas de mensajes, bloques y diálogos: legibilidad 100% nítida */
[class*="bg-card"],
[class*="bg-muted"],
[class*="bg-secondary"],
div.group\\/message {{
  background-color: rgba(14, 18, 28, 0.82) !important;
  border-color: rgba(255, 255, 255, 0.12) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
}}

/* Tipografía de alto contraste */
.text-foreground,
[class*="text-foreground"],
p, span, h1, h2, h3, h4, h5, h6, li, pre, code, button {{
  color: #f8fafc !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.85) !important;
  opacity: 1 !important;
}}

.text-secondary-foreground,
[class*="text-secondary-foreground"],
.text-muted-foreground {{
  color: #94a3b8 !important;
}}

/* Encabezados y títulos */
h1, h2, h3, h4, [class*="font-semibold"] {{
  color: #ffffff !important;
}}

/* Bloques de código pre/code */
pre, code {{
  background-color: rgba(10, 13, 22, 0.90) !important;
  border-color: rgba(56, 189, 248, 0.25) !important;
  color: #e2e8f0 !important;
}}

/* Caja de entrada / prompt de chat */
textarea,
input,
[contenteditable="true"] {{
  background-color: rgba(12, 16, 26, 0.88) !important;
  color: #ffffff !important;
  border: 1px solid rgba(56, 189, 248, 0.40) !important;
  backdrop-filter: blur(14px) !important;
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
        injected = 0
        for p in pages:
            ws_url = p.get("webSocketDebuggerUrl")
            if not ws_url:
                continue
            try:
                async with websockets.connect(ws_url, max_size=25*1024*1024) as ws:
                    msg = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}
                    await ws.send(json.dumps(msg))
                    await ws.recv()
                    injected += 1
            except Exception:
                pass
        print(f"🚀 Wallpaper inyectado en vivo en {injected} vista(s) de Antigravity.")
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
