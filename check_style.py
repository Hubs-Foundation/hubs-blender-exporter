import subprocess
import sys
from shutil import which

if which("pycodestyle") is None:
    print("Error: pycodestyle could not be found. Please install pycodestyle and run this script again: https://pypi.org/project/pycodestyle/")
    sys.exit(1)

cp = subprocess.run(["pycodestyle", "--exclude=models", "--ignore=E501,W504", "addons"])
sys.exit(cp.returncode)
