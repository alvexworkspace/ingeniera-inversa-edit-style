import sys
from pathlib import Path

# `rea` vive en scripts/: se agrega para que las pruebas lo importen sin instalar nada
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
