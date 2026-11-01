use std::collections::BTreeMap;
use std::fs::File;
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::Path;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use crate::error::{GlassError, Result};

const ASAR_BLOCK_SIZE: usize = 4 * 1024 * 1024; // 4 MB

/// Calcula el objeto `integrity` estándar de Electron ASAR (SHA-256 total + bloques de 4MB)
pub fn compute_asar_integrity(data: &[u8]) -> Value {
    let mut full_hasher = Sha256::new();
    full_hasher.update(data);
    let full_hash = format!("{:x}", full_hasher.finalize());

    let mut blocks = Vec::new();
    if data.is_empty() {
        let mut empty_hasher = Sha256::new();
        empty_hasher.update(b"");
        blocks.push(Value::String(format!("{:x}", empty_hasher.finalize())));
    } else {
        for chunk in data.chunks(ASAR_BLOCK_SIZE) {
            let mut block_hasher = Sha256::new();
            block_hasher.update(chunk);
            blocks.push(Value::String(format!("{:x}", block_hasher.finalize())));
        }
    }

    json!({
        "algorithm": "SHA256",
        "hash": full_hash,
        "blockSize": ASAR_BLOCK_SIZE,
        "blocks": blocks
    })
}

/// Lee el encabezado JSON de un archivo Electron `.asar` y devuelve `(header_json, data_offset)`
pub fn read_asar_header(file: &mut File) -> Result<(Value, u64)> {
    file.seek(SeekFrom::Start(0))?;
    let mut prefix = [0u8; 16];
    file.read_exact(&mut prefix).map_err(|_| {
        GlassError::PatchError("Archivo ASAR inválido o truncado (menor a 16 bytes)".to_string())
    })?;

    let pickle_size = u32::from_le_bytes([prefix[0], prefix[1], prefix[2], prefix[3]]);
    if pickle_size != 4 {
        return Err(GlassError::PatchError(format!(
            "Encabezado Pickle ASAR inválido: se esperaba 4, se obtuvo {}",
            pickle_size
        )));
    }

    let header_size = u32::from_le_bytes([prefix[4], prefix[5], prefix[6], prefix[7]]) as u64;
    let json_len = u32::from_le_bytes([prefix[12], prefix[13], prefix[14], prefix[15]]) as usize;

    let data_offset = 8 + header_size;
    if (16 + json_len as u64) > data_offset {
        return Err(GlassError::PatchError(
            "Longitud de JSON en encabezado ASAR excede el tamaño del bloque".to_string(),
        ));
    }

    let mut json_bytes = vec![0u8; json_len];
    file.read_exact(&mut json_bytes)?;

    let header: Value = serde_json::from_slice(&json_bytes)?;
    Ok((header, data_offset))
}

/// Escribe un archivo `.asar` completo a partir de un encabezado JSON y un payload concatenado
pub fn write_asar_archive(dest: &Path, header: &Value, payload: &[u8]) -> Result<()> {
    let json_bytes = serde_json::to_vec(header)?;
    let json_len = json_bytes.len();
    let aligned_json_len = (json_len + 3) & !3;
    let padding_len = aligned_json_len - json_len;

    let string_pickle_size = (aligned_json_len + 4) as u32;
    let header_size = (aligned_json_len + 8) as u32;

    let mut out = File::create(dest)?;
    out.write_all(&4u32.to_le_bytes())?;
    out.write_all(&header_size.to_le_bytes())?;
    out.write_all(&string_pickle_size.to_le_bytes())?;
    out.write_all(&(json_len as u32).to_le_bytes())?;
    out.write_all(&json_bytes)?;
    if padding_len > 0 {
        out.write_all(&vec![0u8; padding_len])?;
    }
    out.write_all(payload)?;
    out.flush()?;
    Ok(())
}

/// Lee un archivo específico dentro de un `.asar` dado su ruta interna (ej: `dist/preload.js`)
pub fn read_file_from_asar(asar_path: &Path, internal_path: &str) -> Result<Vec<u8>> {
    let mut file = File::open(asar_path)?;
    let (header, data_offset) = read_asar_header(&mut file)?;

    let parts: Vec<&str> = internal_path.trim_start_matches('/').split('/').collect();
    let mut current = &header;

    for (i, part) in parts.iter().enumerate() {
        let files = current.get("files").and_then(|f| f.as_object()).ok_or_else(|| {
            GlassError::PatchError(format!("No se encontró el directorio para '{}'", internal_path))
        })?;
        current = files.get(*part).ok_or_else(|| {
            GlassError::PatchError(format!("No existe '{}' dentro de app.asar", internal_path))
        })?;
        if i == parts.len() - 1 {
            break;
        }
    }

    let size = current
        .get("size")
        .and_then(|s| s.as_u64())
        .ok_or_else(|| GlassError::PatchError(format!("'{}' no tiene atributo size válido", internal_path)))?
        as usize;

    let offset_str = current
        .get("offset")
        .and_then(|o| o.as_str())
        .ok_or_else(|| GlassError::PatchError(format!("'{}' no tiene atributo offset válido", internal_path)))?;

    let rel_offset: u64 = offset_str.parse().map_err(|_| {
        GlassError::PatchError(format!("Offset inválido '{}' en '{}'", offset_str, internal_path))
    })?;

    file.seek(SeekFrom::Start(data_offset + rel_offset))?;
    let mut buf = vec![0u8; size];
    file.read_exact(&mut buf)?;
    Ok(buf)
}

/// Modifica quirúrgicamente archivos dentro de un `.asar` en Rust puro (0 dependencias de Node.js/npx).
/// Reconstruye los offsets y los hashes SHA-256 de integridad de forma determinista y atómica.
pub fn patch_asar_surgically(
    asar_path: &Path,
    replacements: &BTreeMap<String, Vec<u8>>,
) -> Result<()> {
    let mut src_file = File::open(asar_path)?;
    let (mut header, data_offset) = read_asar_header(&mut src_file)?;

    let mut new_payload: Vec<u8> = Vec::new();

    fn rewrite_node(
        node: &mut Value,
        current_path: &str,
        src_file: &mut File,
        data_offset: u64,
        new_payload: &mut Vec<u8>,
        replacements: &BTreeMap<String, Vec<u8>>,
    ) -> Result<()> {
        if let Some(files_obj) = node.get_mut("files").and_then(|f| f.as_object_mut()) {
            for (name, child) in files_obj.iter_mut() {
                let child_path = if current_path.is_empty() {
                    name.clone()
                } else {
                    format!("{}/{}", current_path, name)
                };
                rewrite_node(child, &child_path, src_file, data_offset, new_payload, replacements)?;
            }
            return Ok(());
        }

        // Si el archivo está marcado como unpacked o es un symlink, no tiene bytes en el payload
        let is_unpacked = node.get("unpacked").and_then(|u| u.as_bool()).unwrap_or(false);
        let is_link = node.get("link").is_some();
        if is_unpacked || is_link {
            return Ok(());
        }

        if let (Some(orig_size), Some(orig_offset_str)) = (
            node.get("size").and_then(|s| s.as_u64()),
            node.get("offset").and_then(|o| o.as_str()).map(|s| s.to_string()),
        ) {
            let file_bytes = if let Some(rep_bytes) = replacements.get(current_path) {
                rep_bytes.clone()
            } else {
                let rel_offset: u64 = orig_offset_str.parse().map_err(|_| {
                    GlassError::PatchError(format!("Offset corrupto en '{}'", current_path))
                })?;
                src_file.seek(SeekFrom::Start(data_offset + rel_offset))?;
                let mut buf = vec![0u8; orig_size as usize];
                src_file.read_exact(&mut buf)?;
                buf
            };

            let new_offset = new_payload.len() as u64;
            let new_size = file_bytes.len() as u64;
            let integrity = compute_asar_integrity(&file_bytes);

            new_payload.extend_from_slice(&file_bytes);

            if let Some(obj) = node.as_object_mut() {
                obj.insert("size".to_string(), json!(new_size));
                obj.insert("offset".to_string(), json!(new_offset.to_string()));
                obj.insert("integrity".to_string(), integrity);
            }
        }

        Ok(())
    }

    rewrite_node(
        &mut header,
        "",
        &mut src_file,
        data_offset,
        &mut new_payload,
        replacements,
    )?;

    // Escribir primero a un archivo temporal en el mismo directorio para reemplazo atómico
    let parent_dir = asar_path.parent().unwrap_or_else(|| Path::new("."));
    let tmp_file = tempfile::Builder::new()
        .prefix(".agy_asar_atomic_")
        .suffix(".tmp")
        .tempfile_in(parent_dir)?;

    write_asar_archive(tmp_file.path(), &header, &new_payload)?;
    tmp_file.persist(asar_path).map_err(|e| GlassError::Io(e.error))?;

    Ok(())
}
