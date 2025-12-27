# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
project_root = os.path.abspath(os.path.dirname(__file__))

# ✅ Folder that contains your fixed .docx templates
DOC_TEMPLATES_DIR = os.path.join(project_root, 'doc_templates')

# ✅ Django templates/static (keep your existing paths if different)
DJANGO_TEMPLATES_DIR = os.path.join(project_root, 'templates')
STATIC_DIR = os.path.join(project_root, 'static')
MEDIA_DIR = os.path.join(project_root, 'media')

# ---------------------------------------------------------
# Hidden imports (important for Django + docxtpl + jinja2)
# ---------------------------------------------------------
hiddenimports = []

# Django dynamic imports
hiddenimports += collect_submodules('django')

# docxtpl / jinja2
hiddenimports += collect_submodules('docxtpl')
hiddenimports += collect_submodules('jinja2')
hiddenimports += collect_submodules('docx')

# jalali-date packages (if you use them)
hiddenimports += collect_submodules('jdatetime')
hiddenimports += collect_submodules('jalali_date')

# ---------------------------------------------------------
# Data files
# ---------------------------------------------------------

datas = []

# ✅ Include your fixed docx templates folder
if os.path.isdir(DOC_TEMPLATES_DIR):
    datas.append((DOC_TEMPLATES_DIR, 'doc_templates'))

# ✅ Include Django templates folder
if os.path.isdir(DJANGO_TEMPLATES_DIR):
    datas.append((DJANGO_TEMPLATES_DIR, 'templates'))

# ✅ Include static folder
if os.path.isdir(STATIC_DIR):
    datas.append((STATIC_DIR, 'static'))

# ✅ Include media folder (optional, only if you ship sample media)
if os.path.isdir(MEDIA_DIR):
    datas.append((MEDIA_DIR, 'media'))

# ✅ Include docxtpl's internal templates, if any
try:
    datas += collect_data_files('docxtpl')
except Exception:
    pass

# ✅ Include jinja2 package data
try:
    datas += collect_data_files('jinja2')
except Exception:
    pass

# ---------------------------------------------------------
# Build
# ---------------------------------------------------------
a = Analysis(
    ['manage.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='SoldierServer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
