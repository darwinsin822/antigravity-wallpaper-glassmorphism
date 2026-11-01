use std::path::{Path, PathBuf};
use std::process::Command;

/// Obtiene el directorio home del usuario de forma multiplataforma (Linux, macOS, Windows)
pub fn get_home_dir() -> PathBuf {
    if let Ok(home) = std::env::var("HOME") {
        if !home.is_empty() {
            return PathBuf::from(home);
        }
    }
    if let Ok(userprofile) = std::env::var("USERPROFILE") {
        if !userprofile.is_empty() {
            return PathBuf::from(userprofile);
        }
    }
    PathBuf::from(".")
}

/// Expande el prefijo `~` o `~/` al directorio home real del usuario
pub fn expand_tilde(path: &Path) -> PathBuf {
    let s = path.to_string_lossy();
    if s == "~" {
        return get_home_dir();
    }
    if let Some(stripped) = s.strip_prefix("~/").or_else(|| s.strip_prefix("~\\")) {
        return get_home_dir().join(stripped);
    }
    path.to_path_buf()
}

/// Retorna la lista de rutas candidatas para localizar `resources/app.asar`
/// soportando Linux (Debian/Ubuntu/Mint y Arch Linux/AUR), macOS y Windows.
pub fn get_candidate_asar_paths() -> Vec<PathBuf> {
    let mut candidates = Vec::new();
    let home_path = get_home_dir();

    // 1. Linux: Distribuciones Debian / Ubuntu / Linux Mint
    candidates.push(PathBuf::from("/opt/Antigravity/resources/app.asar"));
    candidates.push(PathBuf::from("/opt/antigravity/resources/app.asar"));
    candidates.push(PathBuf::from("/usr/lib/antigravity/resources/app.asar"));
    candidates.push(PathBuf::from("/usr/share/antigravity/resources/app.asar"));
    candidates.push(home_path.join(".local/share/antigravity/resources/app.asar"));
    candidates.push(home_path.join("Documentos/Antigravity-x64/resources/app.asar"));

    // 2. Linux: Distribuciones Arch Linux / Manjaro / AUR (antigravity-bin, agy-cli)
    candidates.push(PathBuf::from("/opt/antigravity-bin/resources/app.asar"));
    candidates.push(PathBuf::from("/usr/lib/antigravity-bin/resources/app.asar"));
    candidates.push(PathBuf::from("/usr/share/antigravity-bin/resources/app.asar"));
    candidates.push(home_path.join(".local/share/antigravity-bin/resources/app.asar"));

    // 3. macOS: Bundles .app estándar y de usuario
    candidates.push(PathBuf::from("/Applications/Antigravity.app/Contents/Resources/app.asar"));
    candidates.push(home_path.join("Applications/Antigravity.app/Contents/Resources/app.asar"));

    // 4. Windows: %LOCALAPPDATA% y %PROGRAMFILES%
    if let Ok(local_app_data) = std::env::var("LOCALAPPDATA") {
        let lad = Path::new(&local_app_data);
        candidates.push(lad.join("Programs/Antigravity/resources/app.asar"));
        candidates.push(lad.join("Antigravity/resources/app.asar"));
    }
    if let Ok(prog_files) = std::env::var("PROGRAMFILES") {
        candidates.push(Path::new(&prog_files).join("Antigravity/resources/app.asar"));
    }

    // 5. Búsqueda dinámica por binario en PATH
    let locator_cmd = if cfg!(target_os = "windows") { "where" } else { "which" };
    for bin in ["antigravity", "antigravity-ide", "agy"] {
        if let Ok(output) = Command::new(locator_cmd).arg(bin).output() {
            if output.status.success() {
                let first_line = String::from_utf8_lossy(&output.stdout)
                    .lines()
                    .next()
                    .unwrap_or("")
                    .trim()
                    .to_string();
                if !first_line.is_empty() {
                    if let Ok(real_path) = std::fs::canonicalize(&first_line) {
                        if let Some(bin_dir) = real_path.parent() {
                            candidates.push(bin_dir.join("resources/app.asar"));
                            if let Some(parent) = bin_dir.parent() {
                                candidates.push(parent.join("resources/app.asar"));
                                candidates.push(parent.join("Resources/app.asar"));
                                candidates.push(parent.join("lib/antigravity/resources/app.asar"));
                            }
                        }
                    }
                }
            }
        }
    }

    // Deduplicar manteniendo el orden de prioridad
    let mut unique = Vec::new();
    for c in candidates {
        if !unique.contains(&c) {
            unique.push(c);
        }
    }
    unique
}

/// Encuentra la ruta existente a `app.asar` o `None` si no existe
pub fn find_antigravity_asar(explicit_path: Option<&Path>) -> Option<PathBuf> {
    if let Some(p) = explicit_path {
        let expanded = expand_tilde(p);
        if expanded.is_file() {
            return Some(expanded);
        }
    }

    if let Ok(env_path) = std::env::var("AGY_ASAR_PATH") {
        let expanded = expand_tilde(Path::new(&env_path));
        if expanded.is_file() {
            return Some(expanded);
        }
    }

    for cand in get_candidate_asar_paths() {
        if cand.is_file() {
            return Some(cand);
        }
    }
    None
}

/// Localiza los directorios de imágenes de acuerdo con XDG y convenciones de cada SO
pub fn get_wallpaper_dirs() -> Vec<PathBuf> {
    let mut dirs = Vec::new();

    // 1. Variable XDG_PICTURES_DIR o comando xdg-user-dir
    if let Ok(xdg_env) = std::env::var("XDG_PICTURES_DIR") {
        let p = expand_tilde(Path::new(&xdg_env));
        if p.is_dir() {
            dirs.push(p);
        }
    } else if !cfg!(target_os = "windows") {
        if let Ok(output) = Command::new("xdg-user-dir").arg("PICTURES").output() {
            if output.status.success() {
                let out_str = String::from_utf8_lossy(&output.stdout).trim().to_string();
                let p = PathBuf::from(out_str);
                if p.is_dir() && !dirs.contains(&p) {
                    dirs.push(p);
                }
            }
        }
    }

    // 2. Fallbacks multiplataforma
    let home_path = get_home_dir();
    let fallbacks = [
        home_path.join("Pictures/Wallpapers"),
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

/// Ruta donde reside la configuración CSS activa (`~/.gemini/antigravity/custom/wallpaper.css`)
pub fn get_custom_css_path() -> PathBuf {
    get_home_dir().join(".gemini/antigravity/custom/wallpaper.css")
}

/// Directorio base para las copias de seguridad de `app.asar`
pub fn get_backup_base_dir() -> PathBuf {
    get_home_dir().join("agy-wallpaper-backup")
}

/// Busca el archivo `DevToolsActivePort` en Linux, macOS y Windows
pub fn get_devtools_port_file() -> PathBuf {
    let home_path = get_home_dir();
    let mut candidates = vec![
        home_path.join(".config/Antigravity/DevToolsActivePort"),
        home_path.join(".config/antigravity/DevToolsActivePort"),
        home_path.join(".config/Antigravity-IDE/DevToolsActivePort"),
        home_path.join("Library/Application Support/Antigravity/DevToolsActivePort"),
    ];

    if let Ok(appdata) = std::env::var("APPDATA") {
        candidates.push(Path::new(&appdata).join("Antigravity/DevToolsActivePort"));
    }

    for c in candidates.iter() {
        if c.exists() {
            return c.clone();
        }
    }
    candidates[0].clone()
}
