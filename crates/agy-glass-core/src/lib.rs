pub mod error;
pub mod paths;
pub mod backup;
pub mod image_proc;
pub mod css_gen;
pub mod patcher;

pub use error::{GlassError, Result};
pub use css_gen::{GlassConfig, generate_css};
pub use image_proc::optimize_image_to_data_uri;
pub use backup::{calculate_sha256, create_backup, verify_backup};
pub use patcher::{patch_preload, patch_utils};
pub use paths::{find_antigravity_asar, get_candidate_asar_paths, get_wallpaper_dirs};

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    #[test]
    fn test_css_generation_contains_scrim() {
        let config = GlassConfig::default();
        let css = generate_css("data:image/jpeg;base64,TEST", &config);

        assert!(css.contains("--agy-wallpaper-scrim"));
        assert!(css.contains("body::before"));
        assert!(css.contains("data:image/jpeg;base64,TEST"));
        assert!(!css.contains("opacity: 1 !important"));
    }

    #[test]
    fn test_patcher_preload_idempotent() {
        let base = "console.log('original preload');";
        let patched = patch_preload(base);
        assert!(patched.contains("SISTEMA REACTIVO DE WALLPAPER GLASSMORPHISM"));

        let patched_again = patch_preload(&patched);
        assert_eq!(patched, patched_again);
    }

    #[test]
    fn test_patcher_utils_anchor_verification() {
        let valid_utils = "devTools: !electron_1.app.isPackaged,\nvoid win.loadURL(url);";
        let patched = patch_utils(valid_utils).expect("Debe parchear utils válido");
        assert!(patched.contains("devTools: true,"));
        assert!(patched.contains("applyNativeCSS"));

        let invalid_utils = "const noAnchor = true;";
        assert!(patch_utils(invalid_utils).is_err());
    }

    #[test]
    fn test_sha256_calculation() {
        let mut tmp = NamedTempFile::new().unwrap();
        tmp.write_all(b"Hello Antigravity 2.0").unwrap();

        let hash = calculate_sha256(tmp.path()).unwrap();
        assert!(!hash.is_empty());
        assert_eq!(hash.len(), 64);
    }

    #[test]
    fn test_paths_candidates_include_debian_and_arch() {
        let candidates = get_candidate_asar_paths();
        assert!(candidates.iter().any(|p| p.to_string_lossy().contains("opt/Antigravity")));
        assert!(candidates.iter().any(|p| p.to_string_lossy().contains("antigravity-bin")));
    }
}
