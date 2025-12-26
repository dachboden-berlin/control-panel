import json

from controlpanel import api

# TODO: Relative Path without import os?
MANIFEST_PATH = "/home/walther/Documents/control-panel/controlpanel/shared/device_manifest.json"


def get_all_device_names():
    try:
        with open(MANIFEST_PATH, "r") as f:
            manifest = json.load(f)

        names = []
        for module in manifest.values():
            devices = module.get("devices", {})
            names.extend(devices.keys())
        return names
    except Exception as e:
        print(f"Error loading manifest: {e}")
        return []


@api.callback(source="PowerSwitch", action="ButtonPressed")
def power_off(event=None):
    print("PowerSwitch pressed: Initiating Blackout...")
    device_names = get_all_device_names()

    for name in device_names:
        try:
            device = api.get_device(name)
            if device:
                device.blackout()
        except (AttributeError, Exception):
            continue


@api.callback(source="PowerSwitch", action="ButtonReleased")
def power_on(event=None):
    print("PowerSwitch released: Restoring systems...")
    device_names = get_all_device_names()

    for name in device_names:
        try:
            device = api.get_device(name)
            if device and hasattr(device, "whiteout"):
                device.whiteout()
        except Exception:
            continue


if __name__ == "__main__":
    print(get_all_device_names())
