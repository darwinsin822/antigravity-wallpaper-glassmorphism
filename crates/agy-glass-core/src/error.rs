use thiserror::Error;

#[derive(Error, Debug)]
pub enum GlassError {
    #[error("Error de entrada/salida: {0}")]
    Io(#[from] std::io::Error),

    #[error("No se encontró el archivo app.asar de Antigravity en las rutas del sistema.")]
    AsarNotFound,

    #[error("Error criptográfico: el hash SHA-256 no coincide (Esperado: {expected}, Calculado: {actual})")]
    ShaMismatch {
        expected: String,
        actual: String,
    },

    #[error("Error al procesar la imagen: {0}")]
    ImageProcessing(String),

    #[error("Error de parcheo: {0}")]
    PatchError(String),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
}

pub type Result<T> = std::result::Result<T, GlassError>;
