import os
import shutil
import subprocess

asar_path = os.path.expanduser("~/Documentos/Antigravity-x64/resources/app.asar")
temp_extract = "/tmp/agy_master_extract"
temp_repack = "/tmp/agy_master_repack.asar"

if os.path.exists(temp_extract):
    shutil.rmtree(temp_extract)
if os.path.exists(temp_repack):
    os.remove(temp_repack)

print("1. Extrayendo app.asar...")
subprocess.run(["npx", "--yes", "@electron/asar", "extract", asar_path, temp_extract], check=True)

main_path = os.path.join(temp_extract, "dist", "main.js")
utils_path = os.path.join(temp_extract, "dist", "utils.js")
ipc_path = os.path.join(temp_extract, "dist", "ipcHandlers.js")
preload_path = os.path.join(temp_extract, "dist", "preload.js")

# --- 1. Parchear main.js: Agregar switch remote-debugging-port ---
print("2. Parcheando main.js con remote-debugging-port...")
with open(main_path, "r") as f:
    main_code = f.read()

switch_code = """
electron_1.app.commandLine.appendSwitch('remote-debugging-port', '0');
"""
if "'remote-debugging-port'" not in main_code:
    target = "electron_1.app.commandLine.appendSwitch('disable-blink-features', 'AutomationControlled');"
    main_code = main_code.replace(target, switch_code + "\n" + target)
    with open(main_path, "w") as f:
        f.write(main_code)

# --- 2. Parchear ipcHandlers.js: Canal IPC para leer el CSS ---
print("3. Parcheando ipcHandlers.js con canal 'agy:get-wallpaper-css'...")
with open(ipc_path, "r") as f:
    ipc_code = f.read()

ipc_hook = """
    // === Canal IPC síncrono para leer wallpaper.css ===
    electron_1.ipcMain.removeAllListeners?.('agy:get-wallpaper-css');
    electron_1.ipcMain.on('agy:get-wallpaper-css', (event) => {
        try {
            const os = require('os');
            const path = require('path');
            const fs = require('fs');
            const p = path.join(os.homedir(), '.gemini', 'antigravity', 'custom', 'wallpaper.css');
            event.returnValue = fs.existsSync(p) ? fs.readFileSync(p, 'utf-8') : '';
        } catch (_) {
            event.returnValue = '';
        }
    });
"""
if "'agy:get-wallpaper-css'" not in ipc_code:
    target_ipc = "electron_1.ipcMain.removeAllListeners?.('storage:get-items-sync');"
    ipc_code = ipc_code.replace(target_ipc, ipc_hook + "\n    " + target_ipc)
    with open(ipc_path, "w") as f:
        f.write(ipc_code)

# --- 3. Parchear utils.js: Inyección nativa en hubContents ---
print("4. Parcheando utils.js con inyección nativa en hubContents...")
with open(utils_path, "r") as f:
    utils_code = f.read()

native_injection = """
        const applyNativeWallpaperCSS = () => {
            try {
                const os_mod = require('os');
                const path_mod = require('path');
                const fs_mod = require('fs');
                const cssPath = path_mod.join(os_mod.homedir(), '.gemini', 'antigravity', 'custom', 'wallpaper.css');
                if (fs_mod.existsSync(cssPath) && !win.isDestroyed?.() && !hubContents.isDestroyed?.()) {
                    const css = fs_mod.readFileSync(cssPath, 'utf-8');
                    void hubContents.insertCSS(css);
                }
            } catch (_) {}
        };
        hubContents.on('did-finish-load', applyNativeWallpaperCSS);
        hubContents.on('dom-ready', applyNativeWallpaperCSS);
"""
if "applyNativeWallpaperCSS" not in utils_code:
    target_utils = "const handleDidFinishLoad = () => {"
    utils_code = utils_code.replace(target_utils, native_injection + "\n        " + target_utils)
    with open(utils_path, "w") as f:
        f.write(utils_code)

# --- 4. Parchear preload.js: Inyección en DOM usando ipcRenderer ---
print("5. Parcheando preload.js con soporte robusto vía ipcRenderer...")
with open(preload_path, "r") as f:
    preload_code = f.read()

# Remover parche anterior si existía para actualizarlo
if "// SISTEMA PERMANENTE DE WALLPAPER GLASSMORPHISM" in preload_code:
    idx = preload_code.find("// ============================================================================\n// SISTEMA PERMANENTE DE WALLPAPER GLASSMORPHISM")
    preload_code = preload_code[:idx]

preload_patch = """
// ============================================================================
// SISTEMA PERMANENTE DE WALLPAPER GLASSMORPHISM (INDESTRUCTIBLE V2)
// ============================================================================
(function() {
    try {
        const STYLE_ID = 'agy-wallpaper-css';

        function getCSS() {
            try {
                if (typeof electron_1 !== 'undefined' && electron_1.ipcRenderer && typeof electron_1.ipcRenderer.sendSync === 'function') {
                    const c = electron_1.ipcRenderer.sendSync('agy:get-wallpaper-css');
                    if (c) return c;
                }
            } catch (_) {}
            try {
                const fs = require('fs');
                const path = require('path');
                const os = require('os');
                const cssPath = path.join(os.homedir(), '.gemini', 'antigravity', 'custom', 'wallpaper.css');
                if (fs.existsSync(cssPath)) return fs.readFileSync(cssPath, 'utf-8');
            } catch (_) {}
            return '';
        }

        function applyWallpaperStyle() {
            try {
                const doc = typeof document !== 'undefined' ? document : (globalThis.document || null);
                if (!doc) return;
                const target = doc.head || doc.documentElement;
                if (!target) return;
                const css = getCSS();
                if (!css) return;

                let existing = doc.getElementById(STYLE_ID);
                if (existing) {
                    if (existing.textContent !== css) existing.textContent = css;
                    return;
                }

                const style = doc.createElement('style');
                style.id = STYLE_ID;
                style.textContent = css;
                target.appendChild(style);
            } catch (_) {}
        }

        applyWallpaperStyle();
        if (typeof window !== 'undefined') {
            window.addEventListener('DOMContentLoaded', applyWallpaperStyle);
            window.addEventListener('load', applyWallpaperStyle);
        }

        function setupObserver() {
            try {
                const doc = typeof document !== 'undefined' ? document : (globalThis.document || null);
                if (!doc || !doc.documentElement) return;
                const Obs = typeof MutationObserver !== 'undefined' ? MutationObserver : globalThis.MutationObserver;
                if (typeof Obs === 'function') {
                    const observer = new Obs(() => applyWallpaperStyle());
                    observer.observe(doc.documentElement, { childList: true, subtree: true });
                }
            } catch (_) {}
        }

        setupObserver();
        setInterval(applyWallpaperStyle, 1000);
    } catch (e) {
        console.error('[Wallpaper Preload] Error:', e);
    }
})();
"""
preload_code += preload_patch
with open(preload_path, "w") as f:
    f.write(preload_code)

print("6. Reempaquetando app.asar con @electron/asar...")
subprocess.run(["npx", "--yes", "@electron/asar", "pack", temp_extract, temp_repack], check=True)

shutil.copy2(temp_repack, asar_path)
shutil.rmtree(temp_extract, ignore_errors=True)
if os.path.exists(temp_repack):
    os.remove(temp_repack)

print("🎉 ¡Parche integral V2 aplicado con éxito en", asar_path, "!")
