#!/usr/bin/env python3
"""
patch_antigravity.py - Instalador y Parcheador del Motor de Persistencia de Antigravity IDE
Autor: DarwinSin (darwinsin822)
Licencia: MIT
"""

import os
import sys
import shutil
import hashlib
import subprocess
from datetime import datetime

POSSIBLE_ASAR_PATHS = [
    os.path.expanduser("~/Descargas/Antigravity-x64/resources/app.asar"),
    os.path.expanduser("~/Documentos/Antigravity-x64/resources/app.asar"),
]

def get_asar_path():
    for p in POSSIBLE_ASAR_PATHS:
        if os.path.exists(p):
            return p
    return POSSIBLE_ASAR_PATHS[0]

DEFAULT_ASAR_PATH = get_asar_path()
BACKUP_BASE_DIR = os.path.expanduser("~/agy-wallpaper-backup")

def calculate_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def patch():
    if not os.path.exists(DEFAULT_ASAR_PATH):
        print(f"❌ Error: No se encontró app.asar en {DEFAULT_ASAR_PATH}")
        sys.exit(1)

    print("🔍 Antigravity IDE detectado.")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    backup_dir = os.path.join(BACKUP_BASE_DIR, timestamp)
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, "app.asar")

    print(f"📦 Creando copia de seguridad en: {backup_file}...")
    shutil.copy2(DEFAULT_ASAR_PATH, backup_file)
    sha_orig = calculate_sha256(backup_file)
    with open(os.path.join(backup_dir, "backup.sha256"), "w") as f:
        f.write(f"{sha_orig}  {backup_file}\n")
    print(f"✅ Backup creado con SHA-256: {sha_orig}")

    temp_extract = "/tmp/agy_patch_extract"
    temp_repack = "/tmp/agy_patch_output.asar"
    if os.path.exists(temp_extract):
        shutil.rmtree(temp_extract)
    if os.path.exists(temp_repack):
        os.remove(temp_repack)

    print("📂 Extrayendo app.asar...")
    subprocess.run(["npx", "--yes", "@electron/asar", "extract", DEFAULT_ASAR_PATH, temp_extract], check=True)

    preload_path = os.path.join(temp_extract, "dist", "preload.js")
    utils_path = os.path.join(temp_extract, "dist", "utils.js")

    # 1. Parchear preload.js
    print("⚡ Inyectando motor de persistencia indestructible en preload.js...")
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
        utils_code = utils_code.replace(target_str, native_hook + "    " + target_str)
        with open(utils_path, "w") as f:
            f.write(utils_code)

    print("📦 Reempaquetando app.asar con @electron/asar...")
    subprocess.run(["npx", "--yes", "@electron/asar", "pack", temp_extract, temp_repack], check=True)

    shutil.copy2(temp_repack, DEFAULT_ASAR_PATH)
    shutil.rmtree(temp_extract, ignore_errors=True)
    if os.path.exists(temp_repack):
        os.remove(temp_repack)

    print(f"🎉 ¡Antigravity IDE parcheado exitosamente en {DEFAULT_ASAR_PATH}!")
    print(f"💡 Puedes aplicar cualquier wallpaper ejecutando:")
    print("   python3 scripts/apply_wallpaper.py \"/ruta/a/imagen.jpg\"")

if __name__ == "__main__":
    patch()
