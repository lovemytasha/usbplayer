# -*- mode: python ; coding: utf-8 -*-
import os

# ⚠⚠⚠ 改成你的 VLC 实际安装路径 ⚠⚠⚠
VLC_DIR = r"C:\Program Files\VideoLAN\VLC"

vlc_binaries = []
if os.path.isdir(VLC_DIR):
    # 1) VLC 根目录下所有 DLL
    for f in os.listdir(VLC_DIR):
        if f.lower().endswith('.dll'):
            vlc_binaries.append((os.path.join(VLC_DIR, f), 'vlc'))
    # 2) plugins 整个目录（保持子目录结构）
    plugin_dir = os.path.join(VLC_DIR, 'plugins')
    if os.path.isdir(plugin_dir):
        for root, dirs, files in os.walk(plugin_dir):
            for f in files:
                src = os.path.join(root, f)
                rel = os.path.relpath(root, VLC_DIR)
                vlc_binaries.append((src, rel))
else:
    print(f"⚠ 警告: 找不到 VLC 目录 {VLC_DIR}，请修改 spec 里的 VLC_DIR")

a = Analysis(
    ['u盘歌曲播放.py'],          # ← 你的脚本文件名
    pathex=[],
    binaries=vlc_binaries,
    datas=[],
    hiddenimports=[
        'vlc',
        'soundcard',
        'soundcard.mediafoundation',
        'pystray',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'psutil',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='usbplayer',          # ← 生成的 exe 名字
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,               # 隐藏控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',             # ← 图标
)