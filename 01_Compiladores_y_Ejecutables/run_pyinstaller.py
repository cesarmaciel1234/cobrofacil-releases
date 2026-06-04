import PyInstaller.__main__
import sys

PyInstaller.__main__.run([
    '--noconfirm',
    '--onefile',
    '--windowed',
    '--name=Instalar_CobroFacil_POS_Online',
    '--hidden-import=win32com',
    '--hidden-import=win32com.client',
    '--icon=NONE',
    'launcher_installer/web_installer.py'
])
