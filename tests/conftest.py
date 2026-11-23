import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# los tests usan los datos ficticios, nunca el cv_base.json real
os.environ["CV_FILE"] = str(ROOT / "cv_base.example.json")
