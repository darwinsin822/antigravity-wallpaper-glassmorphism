#!/usr/bin/env python3
"""
restore_antigravity.py - Restauración instantánea de Antigravity IDE al estado de fábrica
Autor: DarwinSin (darwinsin822)
Licencia: MIT
"""

import os
import sys
import glob
import shutil
import hashlib

POSSIBLE_ASAR_PATHS = [
    os.path.expanduser("~/Descargas/Antigravity-x64/resources/app.asar"),
    os.path.expanduser("~/Documentos/Antigravity-x64/resources/app.asar"),
]

def get_asar_path():
    for p in POSSIBLE_ASAR_PATHS:
        if os.path.exists(p):
            return p
    return POSSIBLE_ASAR_PATHS[0]

DEFAULT_ASAR_PATH = get_asar_path()
BACKUP_BASE_DIR = os.path.expanduser("~/agy-wallpaper-backup")

def calculate_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def restore():
    backups = sorted(glob.glob(os.path.join(BACKUP_BASE_DIR, "*/app.asar")))
    if not backups:
        print(f"❌ Error: No se encontraron respaldos en {BACKUP_BASE_DIR}")
        sys.exit(1)

    latest_backup = backups[0] # el más antiguo/original
    print(f"📦 Respaldo original encontrado: {latest_backup}")

    sha_file = os.path.join(os.path.dirname(latest_backup), "backup.sha256")
    if os.path.exists(sha_file):
        with open(sha_file, "r") as f:
            expected_sha = f.readline().split()[0]
        actual_sha = calculate_sha256(latest_backup)
        if expected_sha == actual_sha:
            print("✅ Verificación SHA-256 del backup: CORRECTA")
        else:
            print("⚠️ Advertencia: El hash del backup no coincide.")

    print(f"Restaurando a {DEFAULT_ASAR_PATH}...")
    shutil.copy2(latest_backup, DEFAULT_ASAR_PATH)
    print("🎉 ¡Restauración completada! Antigravity IDE ha vuelto a su estado original.")

if __name__ == "__main__":
    restore()
