# 🤖 AGENTS.md — Reglas y Especificación de Ingeniería para Agentes de IA

Este documento define la arquitectura, estándares técnicos, restricciones de seguridad y directrices de desarrollo para cualquier agente o desarrollador que trabaje en el repositorio `antigravity-wallpaper-glassmorphism`.

---

## 🎯 1. Visión y Objetivos del Proyecto

El objetivo de este proyecto es proveer un motor de personalización de fondos y temas **Glassmorphism** de alto rendimiento para **Google Antigravity 2.0 / Antigravity IDE**:
* **Rendimiento:** Cero lecturas síncronas a disco en el hilo de renderizado (`0% Disk I/O` en el DOM).
* **Portabilidad:** Soporte nativo para distribuciones basadas en **Debian** (Debian, Ubuntu, Linux Mint) y **Arch Linux** (Arch, Manjaro, EndeavourOS, AUR `antigravity-bin`, `agy-cli`).
* **Seguridad:** Cero rutas predecibles en `/tmp` (mitigación CWE-377) y validación criptográfica estricta con SHA-256.
* **Transición Tecnológica:** Reemplazar progresivamente el pipeline de scripts Python (que dependía de Python 3.10+, pip, Node.js, npm y npx) por una suite nativa, modular y ultrarrápida escrita en **Rust** (Workspace Cargo).

---

## 🐧 2. Matriz de Compatibilidad Multi-Distro

Los motores de detección de rutas (`paths.py` y `paths.rs`) DEBEN buscar el archivo `app.asar` de Antigravity en las siguientes ubicaciones en orden de prioridad:

### A. Parámetro explícito / Variable de entorno
1. Argumento CLI `--asar-path <RUTA>`
2. Variable de entorno `AGY_ASAR_PATH`

### B. Detección por binario en `$PATH`
* `which antigravity` -> resolver enlaces simbólicos hasta el directorio base de la aplicación y localizar `resources/app.asar`.
* `which agy` -> resolver directorio raíz del CLI / IDE.

### C. Rutas del Sistema en Distribuciones Debian / Ubuntu / Linux Mint
* `/opt/Antigravity/resources/app.asar`
* `/opt/antigravity/resources/app.asar`
* `/usr/lib/antigravity/resources/app.asar`
* `/usr/share/antigravity/resources/app.asar`
* `~/.local/share/antigravity/resources/app.asar`
* `~/Documentos/Antigravity-x64/resources/app.asar` (Ruta histórica Linux Mint)

### D. Rutas del Sistema en Distribuciones Arch Linux (AUR: `antigravity-bin`, `agy-cli`)
* `/opt/antigravity-bin/resources/app.asar`
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
   * En Rust: usar el crate `tempfile::Builder`.
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
* `crates/` — Workspace de Rust:
  * `agy-glass-core/` — Biblioteca principal (parser ASAR, procesador de imágenes, generador CSS, backups).
  * `agy-glass-cli/` — Binario ejecutable de línea de comandos `agy-glass`.
* `scripts/` — Scripts transitorios de soporte y CI (`ci.sh`).
* `legacy/python/` — Código Python archivado para preservación histórica.
* `styles/` — Plantillas CSS y muestras para pruebas.

---

## ✅ 5. Verificación de Calidad

Antes de finalizar cualquier tarea, se DEBEN ejecutar las pruebas correspondientes:
* **CI Suite:** `./scripts/ci.sh` (código de salida 0).
* **Rust Suite:** `cargo clippy -- -D warnings` y `cargo test --workspace`.
