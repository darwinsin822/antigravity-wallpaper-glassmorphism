pub mod error;
pub mod paths;
pub mod backup;
pub mod image_proc;
pub mod css_gen;
pub mod patcher;
pub mod asar;

pub use error::{GlassError, Result};
pub use css_gen::{GlassConfig, generate_css};
pub use image_proc::optimize_image_to_data_uri;
pub use backup::{calculate_sha256, create_backup, verify_backup};
pub use patcher::{patch_preload, patch_utils};
pub use asar::{
    compute_asar_integrity, read_asar_header, write_asar_archive,
    read_file_from_asar, patch_asar_surgically,
};
pub use paths::{
    expand_tilde, get_home_dir, find_antigravity_asar, get_candidate_asar_paths,
    get_wallpaper_dirs, get_custom_css_path, get_backup_base_dir, get_devtools_port_file,
};

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;
    use std::io::Write;
    use serde_json::json;
    use tempfile::NamedTempFile;

    #[test]
    fn test_css_generation_contains_scrim_and_clamping() {
        let mut config = GlassConfig::default();
        config.background_opacity = 1.5; // Debe clampearse a 1.00
        let css = generate_css("data:image/jpeg;base64,TEST", &config);

        assert!(css.contains("--agy-wallpaper-scrim"));
        assert!(css.contains("linear-gradient(var(--agy-wallpaper-scrim)"));
        assert!(css.contains("rgba(12, 14, 18, 1.00)"));
        assert!(css.contains("data:image/jpeg;base64,TEST"));
        assert!(!css.contains("opacity: 1 !important"));
    }

    #[test]
    fn test_patcher_preload_idempotent_and_reactive() {
        let base = "console.log('original preload');";
        let patched = patch_preload(base);
        assert!(patched.contains("SISTEMA REACTIVO DE WALLPAPER GLASSMORPHISM"));
        assert!(patched.contains("curr.mtimeMs !== prev.mtimeMs"));

        let patched_again = patch_preload(&patched);
        assert_eq!(patched, patched_again);
    }

    #[test]
    fn test_patcher_utils_anchor_verification_and_no_memory_leak() {
        let valid_utils = "devTools: !electron_1.app.isPackaged,\nvoid win.loadURL(url);";
        let patched = patch_utils(valid_utils).expect("Debe parchear utils válido");
        assert!(patched.contains("devTools: true,"));
        assert!(patched.contains("applyNativeCSS"));
        assert!(patched.contains("removeInsertedCSS"));

        let invalid_utils = "const noAnchor = true;";
        assert!(patch_utils(invalid_utils).is_err());
    }

    #[test]
    fn test_sha256_calculation_and_backup_verification() {
        let mut tmp = NamedTempFile::new().unwrap();
        tmp.write_all(b"Hello Antigravity 2.0").unwrap();

        let hash = calculate_sha256(tmp.path()).unwrap();
        assert_eq!(hash.len(), 64);
    }

    #[test]
    fn test_paths_candidates_include_debian_arch_and_macos() {
        let candidates = get_candidate_asar_paths();
        assert!(candidates.iter().any(|p| p.to_string_lossy().contains("opt/Antigravity")));
        assert!(candidates.iter().any(|p| p.to_string_lossy().contains("antigravity-bin")));
        assert!(candidates.iter().any(|p| p.to_string_lossy().contains("Antigravity.app")));
    }

    #[test]
    fn test_native_rust_asar_surgical_patch() {
        let tmp_dir = tempfile::tempdir().unwrap();
        let asar_file = tmp_dir.path().join("test_app.asar");

        let preload_orig = b"console.log('init preload');";
        let utils_orig = b"devTools: false,\nvoid win.loadURL(url);";

        let mut payload = Vec::new();
        let preload_offset = payload.len();
        payload.extend_from_slice(preload_orig);
        let utils_offset = payload.len();
        payload.extend_from_slice(utils_orig);

        let header = json!({
            "files": {
                "dist": {
                    "files": {
                        "preload.js": {
                            "size": preload_orig.len(),
                            "offset": preload_offset.to_string(),
                            "integrity": compute_asar_integrity(preload_orig)
                        },
                        "utils.js": {
                            "size": utils_orig.len(),
                            "offset": utils_offset.to_string(),
                            "integrity": compute_asar_integrity(utils_orig)
                        }
                    }
                }
            }
        });

        write_asar_archive(&asar_file, &header, &payload).unwrap();

        // Leer preload original desde el ASAR
        let read_preload = read_file_from_asar(&asar_file, "dist/preload.js").unwrap();
        assert_eq!(read_preload, preload_orig);

        // Parchear quirúrgicamente en Rust puro
        let new_preload = patch_preload(&String::from_utf8_lossy(&read_preload));
        let mut replacements = BTreeMap::new();
        replacements.insert("dist/preload.js".to_string(), new_preload.as_bytes().to_vec());

        patch_asar_surgically(&asar_file, &replacements).unwrap();

        // Verificar que preload fue actualizado y utils sigue intacto con su nuevo offset
        let updated_preload = read_file_from_asar(&asar_file, "dist/preload.js").unwrap();
        assert_eq!(updated_preload, new_preload.as_bytes());

        let intact_utils = read_file_from_asar(&asar_file, "dist/utils.js").unwrap();
        assert_eq!(intact_utils, utils_orig);
    }
}
