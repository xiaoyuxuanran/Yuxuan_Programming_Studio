"""Generate build overlays without modifying the upstream checkout.

Use from Windows or WSL. Forward --source-root / --native-root / --compile when
rebuilding against a different checkout. Release-time seed generation is separate.
"""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
script = HERE / 'build-speed/prepare-overlays.py'
subprocess.run([sys.executable, str(script)] + sys.argv[1:], check=True)
