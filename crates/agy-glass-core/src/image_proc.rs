use std::path::Path;
use std::io::Cursor;
use image::imageops::FilterType;
use base64::engine::general_purpose::STANDARD as BASE64_STANDARD;
use base64::Engine;
use crate::error::{GlassError, Result};

const MAX_WIDTH: u32 = 2560;
const MAX_HEIGHT: u32 = 1440;

/// Optimiza y comprime una imagen local convirtiéndola a Data URI base64
pub fn optimize_image_to_data_uri(image_path: &Path) -> Result<String> {
    if !image_path.exists() {
        return Err(GlassError::ImageProcessing(format!(
            "No se encontró el archivo de imagen: {}",
            image_path.display()
        )));
    }

    let img = image::open(image_path)
        .map_err(|e| GlassError::ImageProcessing(format!("Error decodificando imagen: {}", e)))?;

    // Redimensionar suavemente si excede la resolución recomendada
    let (w, h) = (img.width(), img.height());
    let resized = if w > MAX_WIDTH || h > MAX_HEIGHT {
        img.resize(MAX_WIDTH, MAX_HEIGHT, FilterType::Triangle)
    } else {
        img
    };

    let rgb_img = resized.to_rgb8();
    let mut buffer = Cursor::new(Vec::new());

    // Codificar a JPEG de alta fidelidad (calidad ~93)
    let mut encoder = image::codecs::jpeg::JpegEncoder::new_with_quality(&mut buffer, 93);
    encoder
        .encode_image(&rgb_img)
        .map_err(|e| GlassError::ImageProcessing(format!("Error codificando a JPEG: {}", e)))?;

    let jpeg_bytes = buffer.into_inner();
    let b64 = BASE64_STANDARD.encode(&jpeg_bytes);

    Ok(format!("data:image/jpeg;base64,{}", b64))
}
