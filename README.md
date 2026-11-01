# 🌌 Antigravity Wallpaper Glassmorphism

[![Platform: Linux Mint](https://img.shields.io/badge/Platform-Linux%20Mint%20Cinnamon-87cf3e.svg?logo=linuxmint&logoColor=white)](https://linuxmint.com/)
[![App: Google Antigravity 2.0](https://img.shields.io/badge/Google%20Antigravity%202.0-Desktop-4285F4.svg?logo=google&logoColor=white)](https://antigravity.google)
[![Engine: Electron & Tailwind](https://img.shields.io/badge/Engine-Electron%20%7C%20TailwindCSS-38bdf8.svg?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Personalización avanzada de Google Antigravity 2.0 con wallpapers locales, efecto Glassmorphism y arquitectura de persistencia indestructible de 5 capas.**

<div align="center">
  <img src="./assets/antigravity-glassmorphism-showcase.jpg" alt="Google Antigravity 2.0 Glassmorphism UI Showcase" width="100%" style="border-radius: 10px; margin: 16px 0; box-shadow: 0 8px 24px rgba(0,0,0,0.6);" />
</div>

---

## 📖 Descripción General

**Google Antigravity 2.0** es un entorno de desarrollo asistido por IA basado en Electron. Por defecto, su interfaz posee un fondo oscuro sólido `#101010`, carece de sistema de extensiones para temas y tiene las herramientas de desarrollo (*DevTools*) deshabilitadas en entornos de producción.

Este laboratorio proporciona una solución técnica completa, segura y reversible para:
1. Utilizar tus propias **fotografías y wallpapers locales** (JPG, PNG, WebP) como fondo de la interfaz.
2. Aplicar un efecto de diseño moderno **Glassmorphism** (paneles translúcidos con `backdrop-filter: blur()`).
3. Mantener **legibilidad 100% nítida** en textos, código, botones y menús.
4. Garantizar **persistencia indestructible**: el fondo no desaparece al cambiar de chat, navegar entre proyectos o ante reinicios automáticos del servidor interno de Antigravity.
5. Permitir el **cambio en caliente**: actualiza la imagen en vivo en la ventana abierta sin necesidad de reiniciar la aplicación.

---

## 🏛️ Arquitectura de Persistencia Indestructible (5 Capas)

A diferencia de VS Code, la interfaz de Antigravity es una **Single Page Application (SPA)** reactiva que monta capas opacas (`.bg-background`) y reinicia dinámicamente su servidor backend (`language_server`).

Para resolver esto de forma definitiva, diseñamos una arquitectura de **Doble Blindaje**:

```
┌─────────────────────────────────────────────────────────────┐
│                     ANTIGRAVITY IDE                         │
├─────────────────────────────────────────────────────────────┤
│  Nivel 1: preload.js (Inyección autónoma previa al DOM)     │
│  Nivel 2: MutationObserver (Defensa activa anti-reemplazo)  │
│  Nivel 3: History API Interceptor (pushState / replaceState)│
│  Nivel 4: Heartbeat de Salvaguarda (Monitoreo cada 800ms)   │
│  Nivel 5: utils.js (Respaldo nativo Chromium insertCSS)     │
└─────────────────────────────────────────────────────────────┘
```

Consulta los detalles técnicos en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) y [docs/TAILWIND_SPA_ANALYSIS.md](docs/TAILWIND_SPA_ANALYSIS.md).

---

## 🚀 Requisitos Previos

En Linux Mint (o cualquier distribución Linux):

* **Python 3.10+**
* **Bibliotecas Python:**
  ```bash
  pip install pillow websockets
  ```
* **Node.js y npx** (para extraer y reempaquetar el archivo `app.asar`):
  ```bash
  sudo apt install nodejs npm
  ```

---

## 🛠️ Instalación y Uso Rápido

### 1. Clonar el repositorio
```bash
git clone https://github.com/darwinsin822/antigravity-wallpaper-glassmorphism.git
cd antigravity-wallpaper-glassmorphism
```

### 2. Parchear Antigravity 2.0 (Operación Segura de 1 sola vez)
El script crea automáticamente una **copia de seguridad verificada con SHA-256** de tu `app.asar` antes de cualquier modificación:
```bash
python3 scripts/patch_antigravity.py
```

### 3. Aplicar cualquier Wallpaper local
Puedes pasarle cualquier imagen de tu sistema (la imagen original nunca se modifica; se procesa en memoria a stream optimizado):
```bash
python3 scripts/apply_wallpaper.py ~/Imágenes/WALLPAPERS/mi_wallpaper.jpg
```

Para listar las imágenes disponibles en tu carpeta predeterminada:
```bash
python3 scripts/apply_wallpaper.py --list
```

### 4. Diagnosticar estado en tiempo real
Con Antigravity abierto, ejecuta:
```bash
python3 scripts/test_persistence.py
```

---

## 🎨 Ajustes de Transparencia (Glassmorphism)

El archivo de configuración generado se aloja en:
```bash
~/.gemini/antigravity/custom/wallpaper.css
```

Puedes ajustar las variables de color en `:root` según tu preferencia:

```css
:root {
  /* Opacidad de las capas de fondo (0.0 = transparente, 1.0 = negro sólido) */
  --background: rgba(12, 14, 18, 0.65) !important;       /* Fondo general del editor */
  --sidebar: rgba(14, 16, 22, 0.72) !important;          /* Sidebar y explorador */
  --card: rgba(16, 18, 24, 0.70) !important;             /* Tarjetas y burbujas de chat */
}
```

Gracias al **Heartbeat de 800ms**, al guardar cambios en este archivo, el IDE se actualizará **automáticamente en menos de un segundo** sin recargar la página.

---

## 🔄 Restauración al Estado de Fábrica

Si alguna vez deseas revertir todas las modificaciones y volver al estado original de Antigravity:

```bash
python3 scripts/restore_antigravity.py
```

Esto restaura el `app.asar` original verificando su hash criptográfico SHA-256.

---

## 📁 Estructura del Repositorio

```text
antigravity-wallpaper-glassmorphism/
├── README.md                 # Guía completa y documentación
├── LICENSE                   # Licencia MIT
├── .gitignore                # Reglas de exclusión de Git
├── scripts/
│   ├── apply_wallpaper.py    # CLI para aplicar wallpapers y cambio en caliente
│   ├── patch_antigravity.py  # Instalador del motor permanente en app.asar
│   ├── restore_antigravity.py# Restaurador de emergencia al estado original
│   └── test_persistence.py  # Diagnóstico en vivo via Chrome DevTools Protocol
├── styles/
│   ├── template.css          # Plantilla CSS con selectores documentados
│   └── active_sample.css     # Muestra de CSS activo
└── docs/
    ├── ARCHITECTURE.md       # Explicación del Doble Blindaje y 5 niveles de persistencia
    └── TAILWIND_SPA_ANALYSIS.md # Análisis del DOM y Tailwind en Antigravity
```

---

## 👤 Autor

Desarrollado por **DarwinSin** ([@darwinsin822](https://github.com/darwinsin822))  
Laboratorio de personalización y hardening de entornos de desarrollo en Linux Mint Cinnamon.

---


---

## 📊 Evidencia de Ejecución en Vivo

A continuación se muestra la evidencia empírica de la ejecución determinista del pipeline de verificación e integridad técnica:

<div align="center">
  <img src="./assets/wallpaper-execution.png" alt="Execution Results" width="95%" style="border-radius: 8px; border: 1px solid #282e3e; margin: 16px 0;" />
</div>

## 📄 Licencia

Este proyecto está bajo la Licencia [MIT](LICENSE).
