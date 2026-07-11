#!/usr/bin/env python3
"""
Snaketboi Game Launcher
A Snake's Binding
"""

import sys
import subprocess
import os

def check_dependency(module_name, package_name=None):
    """Check if a Python module is installed"""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        return True
    except ImportError:
        print(f"ERROR: {package_name} is not installed!")
        return False

def install_dependency(package_name):
    """Try to install a Python package"""
    print(f"Installing {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to install {package_name}.")
        print(f"Please install it manually: pip3 install {package_name}")
        return False

def main():
    print("=" * 42)
    print("  SNAKETBOI - A Snake's Binding")
    print("=" * 42)
    print()
    
    # Check Python version
    if sys.version_info < (3, 6):
        print("ERROR: Python 3.6 or higher is required!")
        print(f"Current version: {sys.version}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Check dependencies
    print("Checking dependencies...")
    dependencies = [
        ("pygame", "pygame"),
        ("PIL", "Pillow"),
        ("numpy", "numpy")
    ]
    
    missing = []
    for module, package in dependencies:
        if not check_dependency(module, package):
            missing.append((module, package))
    
    # Install missing dependencies
    if missing:
        print()
        for module, package in missing:
            if not install_dependency(package):
                print()
                print("Please install all required packages:")
                for _, pkg in missing:
                    print(f"  pip3 install {pkg}")
                input("\nPress Enter to exit...")
                sys.exit(1)
        print()
    
    print("All dependencies found!")
    print()
    print("Launching game...")
    print()
    
    # Get the directory where the launcher is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Launch the game
    try:
        import main
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user.")
    except Exception as e:
        print(f"\n\nERROR: The game encountered an error:")
        print(f"{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()

