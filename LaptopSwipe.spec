# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

a = Analysis(
    ['menubar_app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('common_words.py', '.'),
        ('spatial_engine.py', '.'),
        ('decoder.py', '.'),
    ],
    hiddenimports=[
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'AppKit',
        'Cocoa',
        'Foundation',
        'objc',
        'Quartz',
        'Quartz.CoreGraphics',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LaptopSwipe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LaptopSwipe',
)

app = BUNDLE(
    coll,
    name='Laptop Swipe.app',
    icon='AppIcon.icns',
    bundle_identifier='com.laptopswipe.mac',
    info_plist={
        'CFBundleName': 'Laptop Swipe',
        'CFBundleDisplayName': 'Laptop Swipe',
        'CFBundleIdentifier': 'com.laptopswipe.mac',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'LSUIElement': True,
        'NSHighResolutionCapable': True,
        'NSAppleEventsUsageDescription': 'Laptop Swipe needs access to monitor keyboard swipes and insert text.',
        'NSAccessibilityUsageDescription': 'Laptop Swipe needs Accessibility permissions to replace swiped text.',
    },
)
