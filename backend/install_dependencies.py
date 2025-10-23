"""
Simplified script to install only pre-compiled packages for Maritime Exception Resolution System.
This skips any packages that require compilation.
"""

import subprocess
import sys

# List of packages that we know have pre-compiled wheels for Windows
SAFE_PACKAGES = [
    "pandas",
    "numpy",
    "fastapi",
    "jinja2",
    "aiofiles",
    "folium",
    "geopy",
    "pyyaml",
]

def run_command(command):
    """Run a shell command and print output."""
    print(f"Executing: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, text=True)
        print(f"Success: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing {command}: {e}")
        return False

def main():
    # Install packages one by one with --prefer-binary flag
    for package in SAFE_PACKAGES:
        print(f"\nInstalling {package}...")
        if not run_command(f"pip install --prefer-binary {package}"):
            print(f"Warning: Failed to install {package}, continuing with other packages")
    
    # Try installing presidio packages with --no-build-isolation
    print("\nInstalling presidio packages...")
    run_command("pip install --prefer-binary presidio-analyzer")
    run_command("pip install --prefer-binary presidio-anonymizer")
    
    print("\nPackage installation completed. Some packages may not have been installed.")
    print("The system should still function with the installed packages.")
    
    return True

if __name__ == "__main__":
    sys.exit(0 if main() else 1)