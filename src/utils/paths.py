import os
import sys

def get_base_path():
    """
    Returns the base path of the application.
    When frozen (PyInstaller), it returns the directory where the .exe is located.
    When running as a script, it returns the project root.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores it in _MEIPASS
        # But for persistent data (DB, config), we want the folder where the EXE is.
        # In our case, the EXE is in /bin/, so the root is one level up.
        exe_dir = os.path.dirname(sys.executable)
        # Check if we are in the 'bin' folder we created
        if os.path.basename(exe_dir).lower() == 'bin':
            return os.path.dirname(exe_dir)
        return exe_dir
    
    # Running from source: main.py is in the root
    # This file is in src/utils/paths.py, so root is two levels up.
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_resource_path(relative_path):
    """
    Returns the absolute path to a resource.
    When frozen, it looks inside the _MEIPASS bundle.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    
    # When running from source, resources are relative to the project root.
    return os.path.join(get_base_path(), relative_path)
