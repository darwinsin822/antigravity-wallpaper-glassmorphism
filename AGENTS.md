# 🤖 AGENTS.md — Reglas y Especificación de Ingeniería para Agentes de IA

Este documento define la arquitectura, estándares técnicos, restricciones de seguridad y directrices de desarrollo para cualquier agente o desarrollador que trabaje en el repositorio `antigravity-wallpaper-glassmorphism`.

---

## 🎯 1. Visión y Objetivos del Proyecto

El objetivo de este proyecto es proveer un motor de personalización de fondos y temas **Glassmorphism** de alto rendimiento para **Google Antigravity 2.0 / Antigravity IDE**:
* **Rendimiento:** Cero lecturas síncronas a disco en el hilo de renderizado (`0% Disk I/O` en el DOM).
* **Portabilidad:** Soporte nativo para distribuciones basadas en **Debian** (Debian, Ubuntu, Linux Mint) y **Arch Linux** (Arch, Manjaro, EndeavourOS).
* **Seguridad:** Cero rutas predecibles en `/tmp` (mitigación CWE-377) y validación criptográfica estricta con SHA-256.
* **Stack actual:** scripts en **Python 3.10+** (`scripts/`) que parchean `app.asar` y plantillas CSS (`styles/`). No hay código Rust en el repositorio: la migración a Rust propuesta por un colaborador fue descartada por el mantenedor y no es un objetivo del proyecto.

---

## 🐧 2. Matriz de Compatibilidad Multi-Distro

Los scripts de parcheo (`scripts/patch_antigravity.py` y `scripts/restore_antigravity.py`) DEBEN buscar el archivo `app.asar` de Antigravity en las siguientes ubicaciones en orden de prioridad:

### A. Parámetro explícito / Variable de entorno
1. Argumento CLI `--asar-path <RUTA>`
2. Variable de entorno `AGY_ASAR_PATH`

### B. Detección por binario en `$PATH`
* `which antigravity` -> resolver enlaces simbólicos hasta el directorio base de la aplicación y localizar `resources/app.asar`.

### C. Rutas del Sistema en Distribuciones Debian / Ubuntu / Linux Mint
* `/opt/Antigravity/resources/app.asar`
* `/opt/antigravity/resources/app.asar`
* `/opt/Antigravity-x64/resources/app.asar`
* `/opt/antigravity-ide/resources/app.asar`
* `/usr/lib/antigravity/resources/app.asar`
* `/usr/share/antigravity/resources/app.asar`
* `~/.local/share/antigravity/resources/app.asar`
* `~/.local/share/Antigravity/resources/app.asar`
* `~/Documentos/Antigravity-x64/resources/app.asar` (Ruta histórica Linux Mint)

> Nota: Google no distribuye un `.deb` oficial de Antigravity 2.x (solo tarball). Las rutas bajo `/usr/lib` y `/usr/share` son conjeturas y solo se usan si el archivo existe.

### D. Rutas del Sistema en Distribuciones Arch Linux
* `/opt/antigravity/resources/app.asar`
* `/usr/lib/antigravity/resources/app.asar`
* `/usr/share/antigravity/resources/app.asar`
* `~/.local/share/applications/antigravity*.desktop` (extrayendo ruta del comando `Exec=`)

### E. Directorios de Imágenes (Wallpapers)
* Consultar `XDG_PICTURES_DIR` mediante comando `xdg-user-dir PICTURES` o variable de entorno `$XDG_PICTURES_DIR`.
* Fallbacks ordenados: `~/Pictures`, `~/Imágenes/WALLPAPERS`, `~/Imágenes`, `~/Wallpapers`.

---

## 🛡️ 3. Reglas Críticas de Seguridad y Rendimiento

1. **PROHIBIDO el uso de rutas fijas en `/tmp`:**
   * En Python: usar obligatoriamente `tempfile.TemporaryDirectory(prefix="agy_")`.
2. **Integridad SHA-256:**
   * En operaciones de restauración (`restore`), si el hash real no coincide con `backup.sha256`, la operación DEBE **abortar inmediatamente** con código de salida distinto de cero (`exit(1)`). Está estrictamente prohibido sobrescribir archivos con datos corruptos.
3. **Cero I/O síncrono en el DOM:**
   * Los scripts inyectados en `preload.js` NO deben ejecutar `fs.readFileSync` dentro de listeners de eventos, mutaciones DOM (`MutationObserver`) ni intervalos frecuentes. Los estilos deben mantenerse cacheados en memoria RAM y actualizarse de forma asíncrona ante eventos del sistema operativo (`fs.watchFile` / IPC).
4. **Protección de Estilos Tailwind:**
   * NO aplicar `opacity: 1 !important` de forma genérica a todos los elementos HTML (`button`, `span`, `input`), ya que rompe estados deshabilitados (`disabled:opacity-50`) y textos atenuados.
   * Utilizar capas *scrim* para contraste en lugar de manipular opacidad de elementos de primer plano.

---

## 🏗️ 4. Estructura del Repositorio

* `.github/workflows/ci.yml` — Pipeline de Integración Continua en GitHub Actions.
* `AGENTS.md` — Esta guía y contrato de ingeniería.
* `README.md` — Documentación pública con guías de inicio rápido y benchmarks.
* `scripts/` — Scripts Python del proyecto (`apply_wallpaper.py`, `patch_antigravity.py`, `restore_antigravity.py`) y el verificador de CI (`ci.sh`).
* `styles/` — Plantillas CSS y muestras para pruebas.
* `docs/` — Documentación técnica (arquitectura, análisis de la SPA).
* `assets/` — Imágenes y recursos de muestra.

> **Nota:** no hay código Rust en este repositorio. La migración a Rust (workspace Cargo con `crates/agy-glass-core` y `crates/agy-glass-cli`, y el archivo `legacy/python/`) fue propuesta en un PR y descartada por el mantenedor. No crear carpetas `crates/` ni `legacy/` ni referirse a ellas como estructura vigente.

---

## ✅ 5. Verificación de Calidad

Antes de finalizar cualquier tarea, se DEBEN ejecutar las pruebas correspondientes:
* **CI Suite:** `./scripts/ci.sh` (código de salida 0).
