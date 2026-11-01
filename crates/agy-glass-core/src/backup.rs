use std::fs::File;
use std::io::Read;
use std::path::{Path, PathBuf};
use sha2::{Digest, Sha256};
use crate::error::{GlassError, Result};

/// Calcula el hash criptográfico SHA-256 de un archivo en bloques de 64 KB
pub fn calculate_sha256(filepath: &Path) -> Result<String> {
    let mut file = File::open(filepath)?;
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 65536];

    loop {
        let count = file.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        hasher.update(&buffer[..count]);
    }

    Ok(format!("{:x}", hasher.finalize()))
}

/// Crea una copia de seguridad timestamped verificada con hash SHA-256
pub fn create_backup(asar_path: &Path, backup_base_dir: &Path) -> Result<(PathBuf, String)> {
    let timestamp = chrono_lite_timestamp();
    let backup_dir = backup_base_dir.join(timestamp);
    std::fs::create_dir_all(&backup_dir)?;

    let target_file = backup_dir.join("app.asar");
    std::fs::copy(asar_path, &target_file)?;

    let sha = calculate_sha256(&target_file)?;
    let sha_file = backup_dir.join("backup.sha256");
    std::fs::write(&sha_file, format!("{}  {}\n", sha, target_file.display()))?;

    Ok((target_file, sha))
}

/// Verifica la integridad del respaldo comparando su SHA-256 con el guardado
pub fn verify_backup(backup_file: &Path) -> Result<String> {
    let parent = backup_file.parent().ok_or_else(|| {
        GlassError::PatchError("Ruta de respaldo inválida".to_string())
    })?;
    let sha_file = parent.join("backup.sha256");

    let actual_sha = calculate_sha256(backup_file)?;

    if sha_file.exists() {
        let content = std::fs::read_to_string(&sha_file)?;
        let expected_sha = content
            .split_whitespace()
            .next()
            .unwrap_or("")
            .trim()
            .to_lowercase();

        if expected_sha != actual_sha.to_lowercase() {
            return Err(GlassError::ShaMismatch {
                expected: expected_sha,
                actual: actual_sha,
            });
        }
    }

    Ok(actual_sha)
}

fn chrono_lite_timestamp() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    // Formato simple y seguro para nombres de directorios
    format!("backup_{}", now)
}
