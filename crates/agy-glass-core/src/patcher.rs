use crate::error::{GlassError, Result};

pub const PRELOAD_PATCH_SIGNATURE: &str = "SISTEMA REACTIVO DE WALLPAPER GLASSMORPHISM";
pub const UTILS_HOOK_SIGNATURE: &str = "applyNativeCSS";

pub fn get_preload_patch_code() -> &'static str {
    r#"
// ============================================================================
// SISTEMA REACTIVO DE WALLPAPER GLASSMORPHISM (EVENT-DRIVEN, 0% DISK I/O EN DOM)
// ============================================================================
(function() {
    try {
        const fs = require('fs');
        const path = require('path');
        const os = require('os');
        const cssPath = path.join(os.homedir(), '.gemini', 'antigravity', 'custom', 'wallpaper.css');
        const STYLE_ID = 'agy-wallpaper-css';

        let cachedCSS = '';
        window.__agy_permanent_heartbeat = true;

        function loadCSSFromDisk() {
            try {
                if (fs.existsSync(cssPath)) {
                    cachedCSS = fs.readFileSync(cssPath, 'utf-8');
                } else {
                    cachedCSS = '';
                }
            } catch (_) {
                cachedCSS = '';
            }
        }

        function ensureStyleNode() {
            try {
                let existing = document.getElementById(STYLE_ID);
                if (!cachedCSS) {
                    if (existing) existing.remove();
                    return;
                }
                const target = document.head || document.documentElement;
                if (!target) return;

                if (existing) {
                    if (existing.textContent !== cachedCSS) {
                        existing.textContent = cachedCSS;
                    }
                    return;
                }

                const style = document.createElement('style');
                style.id = STYLE_ID;
                style.textContent = cachedCSS;
                target.appendChild(style);
            } catch (_) {}
        }

        loadCSSFromDisk();
        ensureStyleNode();
        window.addEventListener('DOMContentLoaded', ensureStyleNode);
        window.addEventListener('load', ensureStyleNode);

        // Vigilar cssPath incluso si aún no ha sido creado en el primer arranque
        try {
            fs.watchFile(cssPath, { interval: 300 }, (curr, prev) => {
                if (curr.mtimeMs !== prev.mtimeMs) {
                    loadCSSFromDisk();
                    ensureStyleNode();
                }
            });
        } catch (_) {}

        function setupObserver() {
            try {
                if (!document.documentElement) return;
                const observer = new MutationObserver(() => {
                    if (cachedCSS && !document.getElementById(STYLE_ID)) {
                        ensureStyleNode();
                    }
                });
                observer.observe(document.documentElement, { childList: true, subtree: false });
            } catch (_) {}
        }

        if (document.documentElement) setupObserver();
        else document.addEventListener('readystatechange', () => { if (document.documentElement) setupObserver(); ensureStyleNode(); });

        try {
            const origPushState = history.pushState;
            history.pushState = function() { origPushState.apply(this, arguments); ensureStyleNode(); };
            const origReplaceState = history.replaceState;
            history.replaceState = function() { origReplaceState.apply(this, arguments); ensureStyleNode(); };
            window.addEventListener('popstate', ensureStyleNode);
        } catch (_) {}
    } catch (e) {
        console.error('[Wallpaper Preload] Error:', e);
    }
})();
"#
}

pub fn get_utils_native_hook() -> &'static str {
    r#"
    // === Respaldo nativo de inyección de CSS a nivel de ventana de Electron (Sin fuga de memoria) ===
    let agyInsertedCssKey = null;
    const applyNativeCSS = async () => {
        try {
            const os_mod = require('os');
            const path_mod = require('path');
            const fs_mod = require('fs');
            const cssPath = path_mod.join(os_mod.homedir(), '.gemini', 'antigravity', 'custom', 'wallpaper.css');
            if (agyInsertedCssKey) {
                try { await win.webContents.removeInsertedCSS(agyInsertedCssKey); } catch (_) {}
                agyInsertedCssKey = null;
            }
            if (fs_mod.existsSync(cssPath)) {
                const css = fs_mod.readFileSync(cssPath, 'utf-8');
                agyInsertedCssKey = await win.webContents.insertCSS(css);
            }
        } catch (_) {}
    };
    win.webContents.on('did-finish-load', applyNativeCSS);
    win.webContents.on('dom-ready', applyNativeCSS);
    win.webContents.on('did-navigate', applyNativeCSS);
    win.webContents.on('did-navigate-in-page', applyNativeCSS);
"#
}

/// Aplica el parche al código fuente de `preload.js` de forma idempotente
pub fn patch_preload(content: &str) -> String {
    if content.contains(PRELOAD_PATCH_SIGNATURE) {
        return content.to_string();
    }
    format!("{}\n{}", content, get_preload_patch_code())
}

/// Aplica el hook nativo al código fuente de `utils.js` verificando los puntos de anclaje
pub fn patch_utils(content: &str) -> Result<String> {
    let mut updated = content
        .replace("devTools: !electron_1.app.isPackaged,", "devTools: true,")
        .replace("devTools: false,", "devTools: true,");

    if updated.contains(UTILS_HOOK_SIGNATURE) {
        return Ok(updated);
    }

    let target_str = "void win.loadURL(url);";
    if !updated.contains(target_str) {
        return Err(GlassError::PatchError(
            "No se encontró el punto de anclaje win.loadURL en utils.js".to_string(),
        ));
    }

    let hook = get_utils_native_hook();
    let replacement = format!("{}\n    {}", hook, target_str);
    updated = updated.replace(target_str, &replacement);

    Ok(updated)
}
