#!/usr/bin/env python3
"""
patch_antigravity.py - Instalador y Parcheador del Motor de Persistencia de Antigravity IDE
Soporte para distribuciones Debian/Ubuntu/Mint, Arch Linux (AUR) y mitigación de seguridad CWE-377.
Autor original: DarwinSin (darwinsin822)
Refactorización de seguridad y portabilidad: Kineyo
Licencia: MIT
"""

import os
import sys
import shutil
import hashlib
import tempfile
import argparse
import subprocess
from datetime import datetime

try:
    from paths import find_antigravity_asar, get_candidate_asar_paths, get_backup_base_dir
except ImportError:
    from scripts.paths import find_antigravity_asar, get_candidate_asar_paths, get_backup_base_dir

def calculate_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def patch(custom_asar_path=None):
    asar_path = find_antigravity_asar(custom_asar_path)
    if not asar_path or not os.path.exists(asar_path):
        print("❌ Error: No se encontró app.asar de Antigravity.")
        print("🔍 Rutas inspeccionadas:")
        for cand in get_candidate_asar_paths():
            print(f"  • {cand}")
        print("\n💡 Puedes especificar la ruta manualmente con:")
        print("   python3 scripts/patch_antigravity.py --asar-path \"/ruta/a/resources/app.asar\"")
        sys.exit(1)

    print(f"🔍 Antigravity IDE detectado en: {asar_path}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    backup_base = get_backup_base_dir()
    backup_dir = os.path.join(backup_base, timestamp)
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, "app.asar")

    print(f"📦 Creando copia de seguridad en: {backup_file}...")
    shutil.copy2(asar_path, backup_file)
    sha_orig = calculate_sha256(backup_file)
    with open(os.path.join(backup_dir, "backup.sha256"), "w") as f:
        f.write(f"{sha_orig}  {backup_file}\n")
    print(f"✅ Backup creado con SHA-256: {sha_orig}")

    # Uso de tempfile seguro para mitigar CWE-377 (ataques de enlace simbólico / colisión en /tmp)
    with tempfile.TemporaryDirectory(prefix="agy_patch_") as tmp_dir:
        temp_extract = os.path.join(tmp_dir, "extracted")
        temp_repack = os.path.join(tmp_dir, "repacked.asar")

        print("📂 Extrayendo app.asar de forma segura...")
        subprocess.run(["npx", "--yes", "@electron/asar", "extract", asar_path, temp_extract], check=True)

        preload_path = os.path.join(temp_extract, "dist", "preload.js")
        utils_path = os.path.join(temp_extract, "dist", "utils.js")

        if not os.path.exists(preload_path) or not os.path.exists(utils_path):
            print(f"❌ Error: Estructura interna de app.asar inesperada. No se encontró preload.js o utils.js.")
            sys.exit(1)

        # 1. Parchear preload.js
        print("⚡ Inyectando motor de persistencia en preload.js...")
        with open(preload_path, "r") as f:
            preload_code = f.read()

        preload_patch = """
// ============================================================================
// SISTEMA PERMANENTE DE WALLPAPER GLASSMORPHISM (INDESTRUCTIBLE)
// ============================================================================
(function() {
    try {
        const fs = require('fs');
        const path = require('path');
        const os = require('os');
        const cssPath = path.join(os.homedir(), '.gemini', 'antigravity', 'custom', 'wallpaper.css');
        const STYLE_ID = 'agy-wallpaper-css';

        function getCSS() {
            try {
                if (fs.existsSync(cssPath)) return fs.readFileSync(cssPath, 'utf-8');
            } catch (_) {}
            return '';
        }

        function applyWallpaperStyle() {
            try {
                const target = document.head || document.documentElement;
                if (!target) return;
                const css = getCSS();
                if (!css) return;

                let existing = document.getElementById(STYLE_ID);
                if (existing) {
                    if (existing.textContent !== css) existing.textContent = css;
                    return;
                }

                const style = document.createElement('style');
                style.id = STYLE_ID;
                style.textContent = css;
                target.appendChild(style);
            } catch (_) {}
        }

        applyWallpaperStyle();
        window.addEventListener('DOMContentLoaded', applyWallpaperStyle);
        window.addEventListener('load', applyWallpaperStyle);

        function setupObserver() {
            try {
                if (!document.documentElement) return;
                const observer = new MutationObserver(() => applyWallpaperStyle());
                observer.observe(document.documentElement, { childList: true, subtree: true });
            } catch (_) {}
        }

        if (document.documentElement) setupObserver();
        else document.addEventListener('readystatechange', () => { if (document.documentElement) setupObserver(); applyWallpaperStyle(); });

        try {
            const origPushState = history.pushState;
            history.pushState = function() { origPushState.apply(this, arguments); applyWallpaperStyle(); };
            const origReplaceState = history.replaceState;
            history.replaceState = function() { origReplaceState.apply(this, arguments); applyWallpaperStyle(); };
            window.addEventListener('popstate', applyWallpaperStyle);
        } catch (_) {}

        setInterval(applyWallpaperStyle, 800);
    } catch (e) {
        console.error('[Wallpaper Preload] Error:', e);
    }
})();
"""
        if "SISTEMA PERMANENTE DE WALLPAPER GLASSMORPHISM" not in preload_code:
            preload_code += preload_patch
            with open(preload_path, "w") as f:
                f.write(preload_code)

        # 2. Parchear utils.js (DevTools y listeners nativos)
        print("⚡ Parcheando utils.js (DevTools + listeners Chromium)...")
        with open(utils_path, "r") as f:
            utils_code = f.read()

        utils_code = utils_code.replace("devTools: !electron_1.app.isPackaged,", "devTools: true,")
        native_hook = """
    // === Respaldo nativo de inyección de CSS a nivel de ventana de Electron ===
    const applyNativeCSS = () => {
        try {
            const os_mod = require('os');
            const path_mod = require('path');
            const fs_mod = require('fs');
            const cssPath = path_mod.join(os_mod.homedir(), '.gemini', 'antigravity', 'custom', 'wallpaper.css');
            if (fs_mod.existsSync(cssPath)) {
                const css = fs_mod.readFileSync(cssPath, 'utf-8');
                void win.webContents.insertCSS(css);
            }
        } catch (_) {}
    };
    win.webContents.on('did-finish-load', applyNativeCSS);
    win.webContents.on('dom-ready', applyNativeCSS);
    win.webContents.on('did-navigate', applyNativeCSS);
    win.webContents.on('did-navigate-in-page', applyNativeCSS);
"""
        if "applyNativeCSS" not in utils_code:
            target_str = "void win.loadURL(url);"
            if target_str in utils_code:
                utils_code = utils_code.replace(target_str, native_hook + "    " + target_str)
                with open(utils_path, "w") as f:
                    f.write(utils_code)
            else:
                print("⚠️ Advertencia: No se encontró el punto de anclaje win.loadURL en utils.js. Se mantendrá la inyección en preload.")

        print("📦 Reempaquetando app.asar con @electron/asar de forma atómica...")
        subprocess.run(["npx", "--yes", "@electron/asar", "pack", temp_extract, temp_repack], check=True)

        shutil.copy2(temp_repack, asar_path)

    print(f"🎉 ¡Antigravity IDE parcheado exitosamente en {asar_path}!")
    print("💡 Puedes aplicar cualquier wallpaper ejecutando:")
    print("   python3 scripts/apply_wallpaper.py \"/ruta/a/imagen.jpg\"")

def main():
    parser = argparse.ArgumentParser(description="Instalador y parcheador del motor de personalización de Antigravity IDE.")
    parser.add_argument("--asar-path", dest="asar_path", default=None, help="Ruta manual al archivo resources/app.asar")
    args = parser.parse_args()
    patch(args.asar_path)

if __name__ == "__main__":
    main()
