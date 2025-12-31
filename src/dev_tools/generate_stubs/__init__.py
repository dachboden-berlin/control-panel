from pathlib import Path
import importlib.util


DEVICE_MANIFEST_PATH = Path(importlib.util.find_spec("controlpanel.shared").origin).parent / "device_manifest.json"
