#!/usr/bin/env python3
"""
restore_antigravity.py - Restauración segura de Antigravity IDE al estado original
Soporte multi-distro (Debian, Arch Linux) y validación criptográfica estricta con SHA-256.
Autor original: DarwinSin (darwinsin822)
Refactorización de seguridad y portabilidad: Kineyo
Licencia: MIT
"""

import os
import sys
import glob
import shutil
import hashlib
import argparse

try:
    from paths import find_antigravity_asar, get_candidate_asar_paths, get_backup_base_dir
except ImportError:
    from scripts.paths import find_antigravity_asar, get_candidate_asar_paths, get_backup_base_dir

def calculate_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def restore(custom_asar_path=None, restore_factory=True):
    asar_path = find_antigravity_asar(custom_asar_path)
    if not asar_path:
        print("❌ Error: No se encontró la ruta destino de app.asar para restaurar.")
        print("🔍 Rutas candidatas inspeccionadas:")
        for cand in get_candidate_asar_paths():
            print(f"  • {cand}")
        print("\n💡 Puedes especificar la ruta de destino manualmente con:")
        print("   python3 scripts/restore_antigravity.py --asar-path \"/ruta/a/resources/app.asar\"")
        sys.exit(1)

    backup_base = get_backup_base_dir()
    backups = sorted(glob.glob(os.path.join(backup_base, "*/app.asar")))
    if not backups:
        print(f"❌ Error: No se encontraron respaldos en {backup_base}")
        sys.exit(1)

    # Si restore_factory es True, usa el respaldo más antiguo (el primer estado original)
    # De lo contrario, usa el más reciente
    target_backup = backups[0] if restore_factory else backups[-1]
    backup_type_label = "original (fábrica)" if restore_factory else "más reciente"
    print(f"📦 Respaldo seleccionado [{backup_type_label}]: {target_backup}")

    sha_file = os.path.join(os.path.dirname(target_backup), "backup.sha256")
    if os.path.exists(sha_file):
        with open(sha_file, "r") as f:
            expected_sha = f.readline().split()[0]
        actual_sha = calculate_sha256(target_backup)

        if expected_sha != actual_sha:
            print("🚨 ERROR CRÍTICO DE SEGURIDAD: El hash SHA-256 del respaldo no coincide con el registro original.")
            print(f"  • Esperado: {expected_sha}")
            print(f"  • Calculado: {actual_sha}")
            print("❌ Operación abortada para prevenir la corrupción de la instalación de Antigravity.")
            sys.exit(1)
        print("✅ Verificación SHA-256 del backup: CORRECTA e ÍNTEGRA")
    else:
        print("⚠️ Advertencia: No se encontró archivo backup.sha256 para verificación criptográfica.")

    print(f"Restaurando a {asar_path}...")
    shutil.copy2(target_backup, asar_path)
    print(f"🎉 ¡Restauración completada con éxito! Antigravity IDE ha vuelto a su estado {backup_type_label}.")

def main():
    parser = argparse.ArgumentParser(description="Restaura Antigravity IDE a su estado previo sin modificaciones.")
    parser.add_argument("--asar-path", dest="asar_path", default=None, help="Ruta manual al archivo resources/app.asar")
    parser.add_argument("--latest", action="store_true", help="Restaura el respaldo más reciente en lugar del de fábrica")
    args = parser.parse_args()

    restore(custom_asar_path=args.asar_path, restore_factory=not args.latest)

if __name__ == "__main__":
    main()
