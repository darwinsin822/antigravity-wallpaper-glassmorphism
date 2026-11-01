#!/usr/bin/env python3
"""
paths.py - Resolución dinámica y multiplataforma de rutas para Antigravity IDE
Soporte para distribuciones Debian/Ubuntu/Mint, Arch Linux (AUR) y directrices XDG.
"""

import os
import sys
import shutil
import subprocess

def get_candidate_asar_paths():
    home = os.path.expanduser("~")
    candidates = []

    # 1. Rutas Debian / Ubuntu / Linux Mint y empaquetados .deb / tarball
    candidates.extend([
        "/opt/Antigravity/resources/app.asar",
        "/opt/antigravity/resources/app.asar",
        "/usr/lib/antigravity/resources/app.asar",
        "/usr/share/antigravity/resources/app.asar",
        os.path.join(home, ".local/share/antigravity/resources/app.asar"),
        os.path.join(home, "Documentos/Antigravity-x64/resources/app.asar"),
    ])

    # 2. Rutas Arch Linux / Manjaro / EndeavourOS (AUR: antigravity-bin, agy-cli)
    candidates.extend([
        "/opt/antigravity-bin/resources/app.asar",
        "/usr/lib/antigravity-bin/resources/app.asar",
        "/usr/share/antigravity-bin/resources/app.asar",
        os.path.join(home, ".local/share/antigravity-bin/resources/app.asar"),
    ])

    # 3. Inspeccionar resolución de binario en $PATH (antigravity o agy)
    for bin_name in ["antigravity", "antigravity-ide", "agy"]:
        bin_path = shutil.which(bin_name)
        if bin_path:
            try:
                real_bin = os.path.realpath(bin_path)
                bin_dir = os.path.dirname(real_bin)
                # Típico: /opt/Antigravity/antigravity -> resources/app.asar
                p1 = os.path.join(bin_dir, "resources", "app.asar")
                p2 = os.path.join(bin_dir, "..", "resources", "app.asar")
                p3 = os.path.join(bin_dir, "..", "lib", "antigravity", "resources", "app.asar")
                candidates.extend([os.path.abspath(p) for p in [p1, p2, p3]])
            except Exception:
                pass

    # Eliminar duplicados manteniendo el orden
    seen = set()
    unique = []
    for c in candidates:
        norm = os.path.normpath(c)
        if norm not in seen:
            seen.add(norm)
            unique.append(norm)
    return unique

def find_antigravity_asar(explicit_path=None):
    if explicit_path:
        exp = os.path.abspath(os.path.expanduser(explicit_path))
        if os.path.isfile(exp):
            return exp
        return None

    env_path = os.environ.get("AGY_ASAR_PATH")
    if env_path:
        exp = os.path.abspath(os.path.expanduser(env_path))
        if os.path.isfile(exp):
            return exp

    for cand in get_candidate_asar_paths():
        if os.path.isfile(cand):
            return cand
    return None

def get_wallpaper_dirs():
    dirs = []
    # 1. Consultar XDG Pictures
    xdg_env = os.environ.get("XDG_PICTURES_DIR")
    if xdg_env and os.path.isdir(xdg_env):
        dirs.append(xdg_env)
    else:
        try:
            out = subprocess.check_output(["xdg-user-dir", "PICTURES"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
            if out and os.path.isdir(out):
                dirs.append(out)
        except Exception:
            pass

    # 2. Fallbacks estándar
    home = os.path.expanduser("~")
    fallbacks = [
        os.path.join(home, "Pictures"),
        os.path.join(home, "Imágenes", "WALLPAPERS"),
        os.path.join(home, "Imágenes"),
        os.path.join(home, "Wallpapers"),
        os.path.join(home, "Fondos"),
    ]
    for d in fallbacks:
        if os.path.isdir(d) and d not in dirs:
            dirs.append(d)
    return dirs

def get_devtools_port_file():
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".config/Antigravity/DevToolsActivePort"),
        os.path.join(home, ".config/antigravity/DevToolsActivePort"),
        os.path.join(home, ".config/Antigravity-IDE/DevToolsActivePort"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

def get_custom_css_path():
    return os.path.expanduser("~/.gemini/antigravity/custom/wallpaper.css")

def get_backup_base_dir():
    # Preferir directorio de respaldos estándar o de usuario
    legacy_dir = os.path.expanduser("~/agy-wallpaper-backup")
    return legacy_dir
