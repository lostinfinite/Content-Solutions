import subprocess
import sys
import importlib

# List of required packages
required_packages = ['py-cord', 'python-dotenv', 'json', 'os', 'scikit-learn', 'numpy', 'requests', 'asyncio']

def install(package):
    """Install a package using pip."""
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# Check and install packages if not already installed
for package in required_packages:
    try:
        importlib.import_module(package.replace('-', '_'))
    except ImportError:
        print(f"Installing {package}...")
        install(package)

# Run beta.py
try:
    print("Running beta.py...")
    subprocess.run([sys.executable, "beta.py"])
except Exception as e:
    print(f"Failed to run beta.py: {e}")
