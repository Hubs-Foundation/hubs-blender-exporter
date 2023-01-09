import subprocess
import sys
from shutil import which

if which("autopep8") is None:
    print("Error: autopep8 could not be found. Please install autopep8 and run this script again: https://pypi.org/project/autopep8/")
    sys.exit(1)

cp = subprocess.run(["autopep8", "--exclude=models", "--in-place",
                     "--recursive", "--max-line-length=120", "--experimental", "addons"])
sys.exit(cp.returncode)
