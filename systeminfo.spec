# -*- mode: python -*-

block_cipher = None

SPEC_DIR = os.path.dirname(SPEC)
MAIN_PY  = os.path.join(SPEC_DIR,"systeminfo","main.py")
ICO      = os.path.join(SPEC_DIR,"res","utilities-system-monitor-icon.icns")

a = Analysis([MAIN_PY],
             pathex=[SPEC_DIR],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='systeminfo',
          debug=False,
          strip=False,
          upx=True,
          console=False)

app = BUNDLE(exe,
           name='systeminfo.app',
           icon=ICO,
           bundle_identifier=None)
