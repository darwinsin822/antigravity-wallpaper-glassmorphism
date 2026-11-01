use clap::{Parser, Subcommand};
use colored::*;
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::process::Command;

use agy_glass_core::{
    expand_tilde, find_antigravity_asar, get_candidate_asar_paths, get_wallpaper_dirs,
    get_custom_css_path, get_backup_base_dir, get_devtools_port_file,
    create_backup, verify_backup, optimize_image_to_data_uri,
    generate_css, GlassConfig, patch_preload, patch_utils,
    read_file_from_asar, patch_asar_surgically,
};

#[derive(Parser)]
#[command(name = "agy-glass")]
#[command(author = "Kineyo & DarwinSin")]
#[command(version = "0.2.0")]
#[command(about = "Motor nativo ultrarrápido de personalización Glassmorphism para Antigravity IDE (100% Rust, 0 Node.js)", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Parchea Antigravity IDE en memoria usando el motor ASAR nativo en Rust (0 dependencias externas)
    Patch {
        #[arg(short, long, help = "Ruta manual al archivo resources/app.asar")]
        asar: Option<PathBuf>,
    },

    /// Aplica un wallpaper con efecto Glassmorphism y capa scrim de contraste
    Apply {
        #[arg(help = "Ruta o nombre del archivo de imagen (JPG, PNG, WebP)")]
        image: String,

        #[arg(long, default_value_t = 0.65, help = "Opacidad de fondo (0.0 a 1.0)")]
        opacity: f32,

        #[arg(long, default_value_t = 12, help = "Intensidad del desenfoque blur en píxeles")]
        blur: u32,

        #[arg(long, default_value_t = 0.45, help = "Opacidad de la capa scrim de contraste (0.0 a 1.0)")]
        scrim: f32,
    },

    /// Lista los wallpapers disponibles en las carpetas detectadas (XDG Pictures)
    List,

    /// Restaura Antigravity IDE a su estado previo verificando integridad SHA-256
    Restore {
        #[arg(short, long, help = "Ruta manual al archivo resources/app.asar")]
        asar: Option<PathBuf>,

        #[arg(long, help = "Restaura el respaldo más reciente en lugar del de fábrica")]
        latest: bool,
    },

    /// Diagnostica el estado del sistema, rutas detectadas y configuración activa
    Doctor,
}

fn maybe_resign_macos_bundle(asar_path: &Path) {
    if cfg!(target_os = "macos") {
        // Si la ruta es /Applications/Antigravity.app/Contents/Resources/app.asar, obtener el .app
        for ancestor in asar_path.ancestors() {
            if ancestor.extension().and_then(|e| e.to_str()) == Some("app") {
                println!("{} {}", "🍎 Aplicando firma ad-hoc de macOS Gatekeeper en:".cyan(), ancestor.display());
                let _ = Command::new("xattr").args(["-cr", &ancestor.to_string_lossy()]).status();
                let _ = Command::new("codesign")
                    .args(["--force", "--deep", "--sign", "-", &ancestor.to_string_lossy()])
                    .status();
                break;
            }
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Patch { asar } => {
            println!("{}", "🌌 Iniciando parcheo quirúrgico de Antigravity IDE (Motor ASAR Rust)...".bold().cyan());
            let asar_path = match find_antigravity_asar(asar.as_deref()) {
                Some(p) => p,
                None => {
                    eprintln!("{}", "❌ Error: No se encontró app.asar de Antigravity.".bold().red());
                    eprintln!("🔍 Rutas inspeccionadas:");
                    for cand in get_candidate_asar_paths() {
                        eprintln!("  • {}", cand.display());
                    }
                    eprintln!("\n💡 Puedes especificar la ruta con: agy-glass patch --asar \"/ruta/a/app.asar\"");
                    std::process::exit(1);
                }
            };

            println!("{} {}", "🔍 Antigravity detectado en:".green(), asar_path.display());
            let backup_base = get_backup_base_dir();
            println!("{}", "📦 Creando copia de seguridad verificada con SHA-256...".yellow());
            let (backup_file, sha) = create_backup(&asar_path, &backup_base)?;
            println!("{} {} (SHA-256: {})", "✅ Respaldo creado en:".green(), backup_file.display(), &sha[..16]);

            println!("{}", "⚡ Leyendo dist/preload.js y dist/utils.js directamente desde app.asar...".cyan());
            let preload_bytes = read_file_from_asar(&asar_path, "dist/preload.js")?;
            let preload_code = String::from_utf8_lossy(&preload_bytes);
            let patched_preload = patch_preload(&preload_code);

            let mut replacements = BTreeMap::new();
            replacements.insert("dist/preload.js".to_string(), patched_preload.into_bytes());

            if let Ok(utils_bytes) = read_file_from_asar(&asar_path, "dist/utils.js") {
                let utils_code = String::from_utf8_lossy(&utils_bytes);
                match patch_utils(&utils_code) {
                    Ok(patched_utils) => {
                        replacements.insert("dist/utils.js".to_string(), patched_utils.into_bytes());
                    }
                    Err(_) => {
                        println!("{}", "⚠️ Aviso: Punto de anclaje no encontrado en utils.js; se mantendrá inyección preload.".yellow());
                    }
                }
            }

            println!("{}", "🦀 Reconstruyendo tabla de integridad SHA-256 y offsets ASAR de forma atómica...".cyan());
            patch_asar_surgically(&asar_path, &replacements)?;
            maybe_resign_macos_bundle(&asar_path);

            println!("{}", "🎉 ¡Antigravity IDE parcheado exitosamente sin dependencias externas!".bold().green());
            println!("💡 Para aplicar un wallpaper ejecuta: agy-glass apply \"imagen.jpg\"");
        }

        Commands::Apply { image, opacity, blur, scrim } => {
            let mut image_path = expand_tilde(Path::new(&image));
            if !image_path.exists() {
                let mut found = false;
                for wdir in get_wallpaper_dirs() {
                    let alt = wdir.join(&image);
                    if alt.exists() {
                        image_path = alt;
                        found = true;
                        break;
                    }
                }
                if !found {
                    eprintln!("{} {}", "❌ Error: No se encontró la imagen:".bold().red(), image);
                    std::process::exit(1);
                }
            }

            let file_name = image_path.file_name().unwrap_or_default().to_string_lossy().to_string();
            println!("{} {}", "🖼️ Procesando imagen en memoria:".cyan(), file_name);

            let clamped_op = opacity.clamp(0.0, 1.0);
            let clamped_scrim = scrim.clamp(0.0, 1.0);

            let data_uri = optimize_image_to_data_uri(&image_path)?;
            let config = GlassConfig {
                wallpaper_name: file_name,
                background_opacity: clamped_op,
                sidebar_opacity: (clamped_op + 0.07).clamp(0.0, 1.0),
                card_opacity: (clamped_op + 0.05).clamp(0.0, 1.0),
                scrim_opacity: clamped_scrim,
                sidebar_blur_px: blur,
                card_blur_px: blur.saturating_sub(2),
            };

            let css = generate_css(&data_uri, &config);
            let css_path = get_custom_css_path();
            if let Some(parent) = css_path.parent() {
                std::fs::create_dir_all(parent)?;
            }
            std::fs::write(&css_path, css)?;

            println!("{} {}", "✅ Estilo persistente guardado en:".green(), css_path.display());
            println!("{}", "✨ ¡Wallpaper Glassmorphism establecido con éxito!".bold().green());
        }

        Commands::List => {
            let dirs = get_wallpaper_dirs();
            if dirs.is_empty() {
                println!("{}", "ℹ️ No se encontraron carpetas de imágenes XDG.".yellow());
                return Ok(());
            }

            let mut count = 0;
            for d in dirs {
                if let Ok(entries) = std::fs::read_dir(&d) {
                    let mut files = Vec::new();
                    for entry in entries.flatten() {
                        let path = entry.path();
                        if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
                            let ext_lower = ext.to_lowercase();
                            if ["jpg", "jpeg", "png", "webp"].contains(&ext_lower.as_str()) {
                                files.push(path.file_name().unwrap().to_string_lossy().to_string());
                            }
                        }
                    }
                    if !files.is_empty() {
                        files.sort();
                        println!("{} {}:", "📁 Carpeta:".cyan().bold(), d.display());
                        for f in files {
                            count += 1;
                            println!("  • {}", f);
                        }
                    }
                }
            }
            if count == 0 {
                println!("{}", "ℹ️ No se encontraron imágenes en las carpetas inspeccionadas.".yellow());
            }
        }

        Commands::Restore { asar, latest } => {
            println!("{}", "🔄 Iniciando restauración de Antigravity IDE...".bold().cyan());
            let asar_path = match find_antigravity_asar(asar.as_deref()) {
                Some(p) => p,
                None => {
                    eprintln!("{}", "❌ Error: No se encontró la ruta destino de app.asar.".bold().red());
                    std::process::exit(1);
                }
            };

            let backup_base = get_backup_base_dir();
            if !backup_base.exists() {
                eprintln!("{}", "❌ No se encontraron respaldos previos.".bold().red());
                std::process::exit(1);
            }

            let mut backups = Vec::new();
            for entry in std::fs::read_dir(&backup_base)?.flatten() {
                let candidate = entry.path().join("app.asar");
                if candidate.is_file() {
                    backups.push(candidate);
                }
            }

            if backups.is_empty() {
                eprintln!("{}", "❌ No se encontraron archivos de respaldo app.asar.".bold().red());
                std::process::exit(1);
            }

            backups.sort();
            let target_backup = if latest {
                backups.last().unwrap()
            } else {
                backups.first().unwrap()
            };

            println!("{} {}", "📦 Verificando respaldo:".cyan(), target_backup.display());
            verify_backup(target_backup)?;
            println!("{}", "✅ Verificación criptográfica SHA-256: CORRECTA".green());

            std::fs::copy(target_backup, &asar_path)?;
            maybe_resign_macos_bundle(&asar_path);
            println!("{}", "🎉 ¡Restauración completada con éxito! Antigravity está en su estado original.".bold().green());
        }

        Commands::Doctor => {
            println!("{}", "🩺 Diagnóstico de Entorno Antigravity Glassmorphism:".bold().cyan());
            println!("--------------------------------------------------");

            let asar_path = find_antigravity_asar(None);
            match asar_path {
                Some(p) => println!("  • Antigravity app.asar:     {} ({})", "✅ Detectado".green(), p.display()),
                None => println!("  • Antigravity app.asar:     {}", "❌ No encontrado".red()),
            }

            let css_path = get_custom_css_path();
            if css_path.exists() {
                let size = std::fs::metadata(&css_path).map(|m| m.len()).unwrap_or(0);
                println!("  • Estilo wallpaper.css:     {} ({} bytes)", "✅ Activo".green(), size);
            } else {
                println!("  • Estilo wallpaper.css:     {}", "ℹ️ No configurado".yellow());
            }

            let devtools_port = get_devtools_port_file();
            if devtools_port.exists() {
                println!("  • Puerto DevTools CDP:      {} ({})", "✅ Activo".green(), devtools_port.display());
            } else {
                println!("  • Puerto DevTools CDP:      {}", "ℹ️ Cerrado (Requiere app abierta)".yellow());
            }

            let wall_dirs = get_wallpaper_dirs();
            println!("  • Carpetas de Wallpapers:   {} detectadas", wall_dirs.len());
            for d in wall_dirs {
                println!("    - {}", d.display());
            }
            println!("--------------------------------------------------");
        }
    }

    Ok(())
}
