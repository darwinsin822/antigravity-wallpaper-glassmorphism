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

def generate_cyberpunk_css(data_uri, wallpaper_name):
    return f"""/* ======================================================================
   Antigravity IDE — Futuristic Cyberpunk High-Tech Theme
   Theme: Cyberpunk HUD & Neon Glassmorphism
   Wallpaper: {wallpaper_name}
   ====================================================================== */

:root {{
  --primary: #00f0ff !important;
  --primary-foreground: #020617 !important;
  --cyber-magenta: #ff0055 !important;
  --cyber-yellow: #ffe600 !important;
  --cyber-cyan: #00f0ff !important;
  --background: rgba(8, 12, 22, 0.70) !important;
  --color-background: rgba(8, 12, 22, 0.70) !important;
  --sidebar: rgba(6, 9, 18, 0.82) !important;
  --color-sidebar-secondary: rgba(10, 15, 28, 0.78) !important;
  --card: rgba(10, 15, 28, 0.82) !important;
  --color-card: rgba(10, 15, 28, 0.82) !important;
  --agy-wallpaper-scrim: linear-gradient(180deg, rgba(5, 7, 15, 0.40) 0%, rgba(8, 12, 22, 0.65) 100%) !important;
}}

/* Limpieza de contenedores anidados para evitar multiplicación de opacidades y oscurecimiento */
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

/* Fondo Cyberpunk con wallpaper */
html,
body {{
  background: #05070f !important;
  background-image: url("{data_uri}") !important;
  background-size: cover !important;
  background-position: center center !important;
  background-attachment: fixed !important;
  background-repeat: no-repeat !important;
}}

/* Scrim con viñeta para máxima nitidez y profundidad */
body::before {{
  content: "" !important;
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  background: radial-gradient(circle at center, rgba(5, 8, 18, 0.35) 0%, rgba(3, 5, 12, 0.75) 100%) !important;
  pointer-events: none !important;
  z-index: 0 !important;
}}

.bg-background,
[class*="bg-background"] {{
  background-color: transparent !important;
}}

/* Sidebar Cyberpunk HUD con borde de neón cian */
.bg-sidebar,
[class*="bg-sidebar"],
[data-testid="sidebar"] {{
  background-color: rgba(6, 9, 18, 0.82) !important;
  backdrop-filter: blur(18px) !important;
  -webkit-backdrop-filter: blur(18px) !important;
  border-right: 1px solid rgba(0, 240, 255, 0.22) !important;
  box-shadow: 2px 0 15px rgba(0, 240, 255, 0.05) !important;
}}

/* Panel principal y área de chat */
.agy-sheet,
.browser-hole-opaque {{
  background-color: rgba(6, 9, 16, 0.40) !important;
}}

/* Tarjetas HUD de mensajes y diálogos */
[class*="bg-card"],
[class*="bg-muted"],
[class*="bg-secondary"],
div.group\\/message {{
  background-color: rgba(9, 14, 26, 0.84) !important;
  border: 1px solid rgba(0, 240, 255, 0.20) !important;
  border-radius: 8px !important;
  backdrop-filter: blur(14px) !important;
  -webkit-backdrop-filter: blur(14px) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45), inset 0 0 12px rgba(0, 240, 255, 0.03) !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}}

div.group\\/message:hover {{
  border-color: rgba(0, 240, 255, 0.40) !important;
  box-shadow: 0 4px 25px rgba(0, 240, 255, 0.12), inset 0 0 15px rgba(0, 240, 255, 0.05) !important;
}}

/* Tipografía de alto contraste con estética futurista */
.text-foreground,
[class*="text-foreground"],
p, span, li {{
  color: #f1f5f9 !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.9) !important;
}}

.text-secondary-foreground,
[class*="text-secondary-foreground"],
.text-muted-foreground {{
  color: #94a3b8 !important;
}}

/* Encabezados y títulos con resplandor cian */
h1, h2, h3, h4, [class*="font-semibold"] {{
  color: #ffffff !important;
  letter-spacing: 0.02em !important;
}}

h1, h2 {{
  text-shadow: 0 0 10px rgba(0, 240, 255, 0.4) !important;
}}

/* Terminal de código: Bloques de código pre y code */
pre {{
  background-color: rgba(4, 7, 15, 0.94) !important;
  border: 1px solid rgba(0, 240, 255, 0.25) !important;
  border-left: 3px solid #00f0ff !important;
  border-radius: 6px !important;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.6) !important;
}}

code {{
  color: #38bdf8 !important;
}}

/* Caja de entrada / Prompt terminal Cyberpunk */
textarea,
input,
[contenteditable="true"] {{
  background-color: rgba(7, 11, 22, 0.90) !important;
  color: #ffffff !important;
  border: 1px solid rgba(0, 240, 255, 0.40) !important;
  border-radius: 8px !important;
  backdrop-filter: blur(16px) !important;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.5) !important;
  transition: all 0.25s ease !important;
}}

textarea:focus,
input:focus,
[contenteditable="true"]:focus {{
  border-color: #00f0ff !important;
  box-shadow: 0 0 16px rgba(0, 240, 255, 0.45), inset 0 0 8px rgba(0, 240, 255, 0.15) !important;
  outline: none !important;
}}

/* Botones con estilo Cyberpunk Neón */
button[class*="bg-primary"],
.bg-primary {{
  background: linear-gradient(135deg, #00f0ff 0%, #00b8d4 100%) !important;
  color: #030712 !important;
  font-weight: 600 !important;
  border: 1px solid #00f0ff !important;
  box-shadow: 0 0 12px rgba(0, 240, 255, 0.4) !important;
  transition: all 0.2s ease !important;
}}

button[class*="bg-primary"]:hover,
.bg-primary:hover {{
  background: linear-gradient(135deg, #38bdf8 0%, #00f0ff 100%) !important;
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.65) !important;
  transform: translateY(-1px) !important;
}}

/* Scrollbars Cyberpunk Neón */
::-webkit-scrollbar {{
  width: 6px !important;
  height: 6px !important;
}}

::-webkit-scrollbar-track {{
  background: rgba(4, 6, 12, 0.6) !important;
}}

::-webkit-scrollbar-thumb {{
  background: linear-gradient(180deg, #00f0ff, #ff0055) !important;
  border-radius: 4px !important;
}}

::-webkit-scrollbar-thumb:hover {{
  background: #00f0ff !important;
  box-shadow: 0 0 10px #00f0ff !important;
}}

/* Badges y chips de estado */
[class*="badge"],
[class*="tag"] {{
  border: 1px solid rgba(0, 240, 255, 0.35) !important;
  background-color: rgba(0, 240, 255, 0.08) !important;
  color: #00f0ff !important;
}}

/* Separadores y bordes sutiles transparentes estilo glass */
.bg-border,
.border-border,
[class*="border-border"] {{
  border-color: rgba(0, 240, 255, 0.15) !important;
}}
"""

def generate_glassmorphism_css(data_uri, wallpaper_name):
    return f"""/* ======================================================================
   Antigravity IDE — Wallpaper Glassmorphism & High-Contrast Readability
   Wallpaper: {wallpaper_name}
   ====================================================================== */

:root {{
  --background: rgba(12, 14, 18, 0.65) !important;
  --color-background: rgba(12, 14, 18, 0.65) !important;
  --sidebar: rgba(14, 16, 22, 0.72) !important;
  --color-sidebar-secondary: rgba(18, 20, 28, 0.70) !important;
  --card: rgba(16, 18, 24, 0.70) !important;
  --color-card: rgba(16, 18, 24, 0.70) !important;
  --agy-wallpaper-scrim: rgba(8, 10, 14, 0.45) !important;
}}

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

/* Fondo base de la ventana y HTML */
html,
body {{
  background: #080a10 !important;
  background-image: url("{data_uri}") !important;
  background-size: cover !important;
  background-position: center center !important;
  background-attachment: fixed !important;
  background-repeat: no-repeat !important;
}}

/* Capa de contraste adaptativo (Scrim) para proteger legibilidad de sintaxis */
body::before {{
  content: "" !important;
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  background: var(--agy-wallpaper-scrim) !important;
  pointer-events: none !important;
  z-index: 0 !important;
}}

/* Contenedor principal de la aplicación Antigravity */
.bg-background,
[class*="bg-background"] {{
  background-color: transparent !important;
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
p, span, h1, h2, h3, h4, h5, h6, li, pre, code {{
  color: #f8fafc !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.85) !important;
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

/* Separadores y bordes sutiles transparentes estilo glass */
.bg-border,
.border-border,
[class*="border-border"] {{
  border-color: rgba(255, 255, 255, 0.08) !important;
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
    parser = argparse.ArgumentParser(description="Aplica un tema y wallpaper Glassmorphism/Cyberpunk a Google Antigravity IDE.")
    parser.add_argument("image", nargs="?", help="Ruta o nombre del archivo de imagen (JPG, PNG, WebP)")
    parser.add_argument("--theme", choices=["cyberpunk", "glassmorphism"], default="cyberpunk", help="Tema estético a aplicar ('cyberpunk' predeterminado o 'glassmorphism')")
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

    target_image = args.image
    if not target_image:
        if args.theme == "cyberpunk":
            # Buscar automáticamente wallpaper cyberpunk por defecto
            for wdir in wallpaper_dirs:
                candidate = os.path.join(wdir, "cyberpunk_futuristic_city.jpg")
                if os.path.exists(candidate):
                    target_image = candidate
                    break

    if not target_image:
        parser.print_help()
        sys.exit(1)

    image_path = os.path.abspath(os.path.expanduser(target_image))
    if not os.path.exists(image_path):
        # Buscar en las carpetas de imágenes detectadas (XDG / Pictures / etc.)
        found = False
        for wdir in wallpaper_dirs:
            alt_path = os.path.join(wdir, target_image)
            if os.path.exists(alt_path):
                image_path = alt_path
                found = True
                break
        if not found:
            print(f"❌ Error: La imagen '{target_image}' no fue encontrada.")
            print(f"🔍 Carpetas inspeccionadas: {', '.join(wallpaper_dirs)}")
            sys.exit(1)

    print(f"🎨 Tema seleccionado: {args.theme.upper()}")
    print(f"🖼️ Procesando wallpaper: {os.path.basename(image_path)}...")
    data_uri = optimize_image_to_data_uri(image_path)
    
    if args.theme == "cyberpunk":
        css_content = generate_cyberpunk_css(data_uri, os.path.basename(image_path))
    else:
        css_content = generate_glassmorphism_css(data_uri, os.path.basename(image_path))

    os.makedirs(os.path.dirname(CUSTOM_CSS_PATH), exist_ok=True)
    with open(CUSTOM_CSS_PATH, "w") as f:
        f.write(css_content)
    print(f"✅ Estilo persistente guardado en: {CUSTOM_CSS_PATH}")

    if WEBSOCKETS_AVAILABLE:
        asyncio.run(inject_live(css_content))
    else:
        print("ℹ️ websockets no disponible. El cambio será visible al reiniciar Antigravity.")

    print(f"✨ ¡Tema {args.theme.capitalize()} y Wallpaper establecidos con éxito!")

if __name__ == "__main__":
    main()
