#!/usr/bin/env python3
"""
test_persistence.py - Diagnóstico en tiempo real del motor Glassmorphism via Chrome DevTools Protocol
Autor: DarwinSin (darwinsin822)
"""

import os
import sys
import json
import urllib.request
import asyncio

try:
    import websockets
except ImportError:
    print("❌ Instala websockets para ejecutar este script: pip install websockets")
    sys.exit(1)

PORT_FILE = os.path.expanduser("~/.config/Antigravity/DevToolsActivePort")

async def test():
    if not os.path.exists(PORT_FILE):
        print(f"❌ Error: DevToolsActivePort no existe en {PORT_FILE}. Asegúrate de que Antigravity esté abierto.")
        return

    with open(PORT_FILE, "r") as pf:
        port = pf.readline().strip()

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as r:
            pages = json.loads(r.read())
    except Exception as e:
        print(f"❌ Error al conectar al puerto DevTools {port}: {e}")
        return

    if not pages:
        print("❌ No se encontraron páginas activas en Antigravity.")
        return

    ws_url = pages[0]["webSocketDebuggerUrl"]
    print(f"🔗 Conectando a target DevTools: {pages[0]['title']} ({ws_url})")

    async with websockets.connect(ws_url, max_size=15*1024*1024) as ws:
        test_script = """
        (function() {
            var el = document.getElementById('agy-wallpaper-css');
            var bgEl = document.querySelector('.bg-background');
            return {
                styleTagPresent: !!el,
                styleTagLength: el ? el.textContent.length : 0,
                bodyBgImage: window.getComputedStyle(document.body).backgroundImage.slice(0, 60),
                containerBgImage: bgEl ? window.getComputedStyle(bgEl).backgroundImage.slice(0, 60) : 'NO_ELEMENT',
                containerClasses: bgEl ? bgEl.className : '',
                hasHeartbeat: !!window.__agy_permanent_heartbeat
            };
        })()
        """
        msg = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": test_script, "returnByValue": True}}
        await ws.send(json.dumps(msg))
        resp = await ws.recv()
        data = json.loads(resp)["result"]["result"]["value"]
        print("\n📊 RESULTADOS DEL DIAGNÓSTICO EN VIVO:")
        print(f"  • Tag <style> inyectado:    {'✅ Sí' if data.get('styleTagPresent') else '❌ No'}")
        print(f"  • Tamaño del CSS activo:    {data.get('styleTagLength')} bytes")
        print(f"  • Fondo de <body>:          {data.get('bodyBgImage')}")
        print(f"  • Fondo de .bg-background:  {data.get('containerBgImage')}")
        print(f"  • Heartbeat activo:         {'✅ Sí' if data.get('hasHeartbeat') else 'ℹ️ Inyectado por preload'}")

if __name__ == "__main__":
    asyncio.run(test())
