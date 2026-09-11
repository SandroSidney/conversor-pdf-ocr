# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ocrmypdf descobre seus plugins de OCR (tesseract_ocr, null_ocr, etc.) em
# tempo de execução via pkgutil.iter_modules(), então o PyInstaller não os
# detecta por análise estática — sem isso o app falha com "No OCR engine
# selected" porque nenhum motor de OCR fica disponível no .exe.
hidden_ocrmypdf_plugins = collect_submodules('ocrmypdf.builtin_plugins')

# ocrmypdf também carrega arquivos de dados (fontes .ttf, perfil sRGB.icc)
# em tempo de execução a partir da pasta ocrmypdf/data/; sem isso a
# conversão falha com "Required fallback font not found".
ocrmypdf_data_files = collect_data_files('ocrmypdf')

a = Analysis(
    ['Converter_PDF_OCR.py'],
    pathex=[],
    binaries=[],
    datas=ocrmypdf_data_files,
    hiddenimports=hidden_ocrmypdf_plugins,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ConversorPDFOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
