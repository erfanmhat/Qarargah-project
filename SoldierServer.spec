# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# ------------------------------------------------------------
# Resolve project root safely (avoid __file__)
# ------------------------------------------------------------
_spec_dir = globals().get("SPECPATH", None)
if _spec_dir:
    PROJECT_ROOT = Path(_spec_dir).resolve()
else:
    PROJECT_ROOT = Path(os.getcwd()).resolve()

# ------------------------------------------------------------
# Entry script (CHANGE THIS if needed)
# ------------------------------------------------------------
ENTRY_SCRIPT = PROJECT_ROOT / "run_server.py"
if not ENTRY_SCRIPT.exists():
    raise SystemExit(f"ENTRY_SCRIPT not found: {ENTRY_SCRIPT}")

# ------------------------------------------------------------
# Hidden imports
# ------------------------------------------------------------
hiddenimports = []
hiddenimports += collect_submodules("xhtml2pdf")
hiddenimports += collect_submodules("reportlab")
hiddenimports += [
    "reportlab.graphics.barcode",
    "reportlab.graphics.barcode.code128",
]
hiddenimports += collect_submodules("html5lib")
hiddenimports += collect_submodules("pypdf")

# ------------------------------------------------------------
# Datas (MUST be list of (src, dest))
# ------------------------------------------------------------
datas = []

# Add templates directory if present
templates_root = PROJECT_ROOT / "templates"
if templates_root.exists():
    datas.append((str(templates_root), "templates"))

core_templates = PROJECT_ROOT / "core" / "templates"
if core_templates.exists():
    datas.append((str(core_templates), "core/templates"))

admin_templates = PROJECT_ROOT / "admin" / "templates"
if admin_templates.exists():
    datas.append((str(admin_templates), "admin/templates"))

# Add fonts directory (Persian)
fonts_dir = PROJECT_ROOT / "core" / "static" / "fonts"
if fonts_dir.exists():
    datas.append((str(fonts_dir), "core/static/fonts"))

# Collect package data
datas += collect_data_files("xhtml2pdf")
datas += collect_data_files("reportlab")


static_dir = PROJECT_ROOT / "staticfiles"
if static_dir.exists():
    datas.append((str(static_dir), "staticfiles"))
# ------------------------------------------------------------
# Excludes to avoid pkg_resources rthook issues
# ------------------------------------------------------------
excludes = [
    "pkg_resources",
    "setuptools",
    "setuptools._vendor",
]

a = Analysis(
    [str(ENTRY_SCRIPT)],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SoldierServer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SoldierServer",
)
