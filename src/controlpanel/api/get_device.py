from controlpanel.shared.base import Device
from .services import services


def get_device(device_name) -> Device:
    return services.event_manager.devices.get(device_name)
