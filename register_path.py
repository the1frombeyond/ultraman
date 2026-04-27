import os
import sys
import subprocess
import winreg
from rich.console import Console

console = Console()

def add_to_path(new_path):
    try:
        # Get current user path
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS) as key:
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path = ""
            
            if new_path.lower() in current_path.lower():
                print(f"INFO: Path already exists in User PATH: {new_path}")
                return
            
            updated_path = f"{current_path};{new_path}" if current_path else new_path
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, updated_path)
            
            # Notify system of changes
            import ctypes
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 0, 5000, None)
            
            print(f"SUCCESS: Successfully added to User PATH.")
            print("NOTE: You may need to restart your terminal for changes to take effect.")
    except Exception as e:
        print(f"ERROR: Failed to update PATH: {e}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"--- Registering ULTRAMAN Universal Command ---")
    add_to_path(current_dir)
