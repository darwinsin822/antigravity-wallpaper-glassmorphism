use std::path::{Path, PathBuf};
use std::process::Command;

/// Retorna la lista de rutas candidatas para localizar resources/app.asar
/// en distribuciones Debian/Ubuntu/Mint, Arch Linux (AUR) y rutas de usuario.
pub fn get_candidate_asar_paths() -> Vec<PathBuf> {
    let mut candidates = Vec::new();
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    let home_path = Path::new(&home);

    // 1. Distribuciones Debian / Ubuntu / Linux Mint
    candidates.push(PathBuf::from("/opt/Antigravity/resources/app.asar"));
    candidates.push(PathBuf::from("/opt/antigravity/resources/app.asar"));
    candidates.push(PathBuf::from("/usr/lib/antigravity/resources/app.asar"));
    candidates.push(PathBuf::from("/usr/share/antigravity/resources/app.asar"));
    candidates.push(home_path.join(".local/share/antigravity/resources/app.asar"));
    candidates.push(home_path.join("Documentos/Antigravity-x64/resources/app.asar"));

    // 2. Distribuciones Arch Linux / Manjaro / AUR (antigravity-bin, agy-cli)
    candidates.push(PathBuf::from("/opt/antigravity-bin/resources/app.asar"));
    candidates.push(PathBuf::from("/usr/lib/antigravity-bin/resources/app.asar"));
    candidates.push(PathBuf::from("/usr/share/antigravity-bin/resources/app.asar"));
    candidates.push(home_path.join(".local/share/antigravity-bin/resources/app.asar"));

    // 3. Búsqueda por binario en PATH
    for bin in ["antigravity", "antigravity-ide", "agy"] {
        if let Ok(output) = Command::new("which").arg(bin).output() {
            if output.status.success() {
                let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if let Ok(real_path) = std::fs::canonicalize(&stdout) {
                    if let Some(bin_dir) = real_path.parent() {
                        candidates.push(bin_dir.join("resources/app.asar"));
                        if let Some(parent) = bin_dir.parent() {
                            candidates.push(parent.join("resources/app.asar"));
                            candidates.push(parent.join("lib/antigravity/resources/app.asar"));
                        }
                    }
                }
            }
        }
    }

    // Deduplicar manteniendo orden
    let mut unique = Vec::new();
    for c in candidates {
        if !unique.contains(&c) {
            unique.push(c);
        }
    }
    unique
}

/// Encuentra la ruta existente a app.asar o None si no existe
pub fn find_antigravity_asar(explicit_path: Option<&Path>) -> Option<PathBuf> {
    if let Some(p) = explicit_path {
        if p.is_file() {
            return Some(p.to_path_buf());
        }
    }

    if let Ok(env_path) = std::env::var("AGY_ASAR_PATH") {
        let p = PathBuf::from(env_path);
        if p.is_file() {
            return Some(p);
        }
    }

    for cand in get_candidate_asar_paths() {
        if cand.is_file() {
            return Some(cand);
        }
    }
    None
}

/// Localiza los directorios de imágenes de acuerdo con el estándar XDG
pub fn get_wallpaper_dirs() -> Vec<PathBuf> {
    let mut dirs = Vec::new();

    // 1. XDG_PICTURES_DIR
    if let Ok(xdg_env) = std::env::var("XDG_PICTURES_DIR") {
        let p = PathBuf::from(xdg_env);
        if p.is_dir() {
            dirs.push(p);
        }
    } else if let Ok(output) = Command::new("xdg-user-dir").arg("PICTURES").output() {
        if output.status.success() {
            let out_str = String::from_utf8_lossy(&output.stdout).trim().to_string();
            let p = PathBuf::from(out_str);
            if p.is_dir() && !dirs.contains(&p) {
                dirs.push(p);
            }
        }
    }

    // 2. Fallbacks de usuario
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    let home_path = Path::new(&home);
    let fallbacks = [
        home_path.join("Pictures"),
        home_path.join("Imágenes/WALLPAPERS"),
        home_path.join("Imágenes"),
        home_path.join("Wallpapers"),
        home_path.join("Fondos"),
    ];

    for f in fallbacks {
        if f.is_dir() && !dirs.contains(&f) {
            dirs.push(f);
        }
    }

    dirs
}

/// Ruta donde reside la configuración CSS activa
pub fn get_custom_css_path() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    Path::new(&home).join(".gemini/antigravity/custom/wallpaper.css")
}

/// Directorio base para las copias de seguridad de app.asar
pub fn get_backup_base_dir() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    Path::new(&home).join("agy-wallpaper-backup")
}

/// Busca el archivo DevToolsActivePort para inyección en vivo
pub fn get_devtools_port_file() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    let home_path = Path::new(&home);
    let candidates = [
        home_path.join(".config/Antigravity/DevToolsActivePort"),
        home_path.join(".config/antigravity/DevToolsActivePort"),
        home_path.join(".config/Antigravity-IDE/DevToolsActivePort"),
    ];
    for c in candidates.iter() {
        if c.exists() {
            return c.clone();
        }
    }
    candidates[0].clone()
}
