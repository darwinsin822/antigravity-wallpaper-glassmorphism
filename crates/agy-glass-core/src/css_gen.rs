use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlassConfig {
    pub wallpaper_name: String,
    pub background_opacity: f32,
    pub sidebar_opacity: f32,
    pub card_opacity: f32,
    pub scrim_opacity: f32,
    pub sidebar_blur_px: u32,
    pub card_blur_px: u32,
}

impl Default for GlassConfig {
    fn default() -> Self {
        Self {
            wallpaper_name: "custom_wallpaper".to_string(),
            background_opacity: 0.65,
            sidebar_opacity: 0.72,
            card_opacity: 0.70,
            scrim_opacity: 0.45,
            sidebar_blur_px: 14,
            card_blur_px: 10,
        }
    }
}

/// Genera la hoja de estilos Glassmorphism altamente optimizada y no invasiva
pub fn generate_css(data_uri: &str, config: &GlassConfig) -> String {
    format!(
r#"/* ======================================================================
   Antigravity IDE — Wallpaper Glassmorphism (Motor Nativo Rust agy-glass)
   Wallpaper: {wallpaper_name}
   ====================================================================== */

:root {{
  --background: rgba(12, 14, 18, {bg_op:.2}) !important;
  --color-background: rgba(12, 14, 18, {bg_op:.2}) !important;
  --sidebar: rgba(14, 16, 22, {sb_op:.2}) !important;
  --color-sidebar-secondary: rgba(18, 20, 28, {sb_op:.2}) !important;
  --card: rgba(16, 18, 24, {card_op:.2}) !important;
  --color-card: rgba(16, 18, 24, {card_op:.2}) !important;
  --agy-wallpaper-scrim: rgba(8, 10, 14, {scrim_op:.2}) !important;
}}

/* Fondo base de la ventana y HTML */
html,
body {{
  background-image: url("{data_uri}") !important;
  background-size: cover !important;
  background-position: center center !important;
  background-attachment: fixed !important;
  background-repeat: no-repeat !important;
}}

/* Capa Scrim de contraste adaptativo para garantizar legibilidad de sintaxis */
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

/* Sidebar y paneles de navegación con Glassmorphism */
.bg-sidebar,
[class*="bg-sidebar"] {{
  background-color: rgba(12, 14, 20, {sb_op:.2}) !important;
  backdrop-filter: blur({sb_blur}px) !important;
  -webkit-backdrop-filter: blur({sb_blur}px) !important;
}}

/* Tarjetas y burbujas de diálogo */
.bg-card,
[class*="bg-card"] {{
  background-color: rgba(16, 18, 24, {card_op:.2}) !important;
  backdrop-filter: blur({card_blur}px) !important;
  -webkit-backdrop-filter: blur({card_blur}px) !important;
}}

/* Barra superior / Header */
.h-screen > .shrink-0,
.h-screen > .shrink-0 > div {{
  background-color: rgba(10, 12, 16, 0.80) !important;
  backdrop-filter: blur(16px) !important;
  -webkit-backdrop-filter: blur(16px) !important;
}}

/* Área central de trabajo / Chat / Editor */
.flex-1.flex.min-h-0 > div {{
  background-color: rgba(12, 14, 18, {bg_op:.2}) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}}

/* Separadores y bordes sutiles estilo cristal */
.bg-border,
.border-border,
[class*="border-border"] {{
  border-color: rgba(255, 255, 255, 0.08) !important;
}}
"#,
        wallpaper_name = config.wallpaper_name,
        bg_op = config.background_opacity,
        sb_op = config.sidebar_opacity,
        card_op = config.card_opacity,
        scrim_op = config.scrim_opacity,
        sb_blur = config.sidebar_blur_px,
        card_blur = config.card_blur_px,
        data_uri = data_uri
    )
}
