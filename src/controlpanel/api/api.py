import time
import threading
from typing import TypeVar
from controlpanel.shared.base import Device
from controlpanel.api.dummy import Fixture
from .services import services
from .commons import EventSourceType, EventActionType, EventValueType, CallbackType
import inspect
from types import ModuleType, FrameType


T = TypeVar("T", bound="BaseGame")


def _get_caller_name_and_module() -> str:
    frame = inspect.currentframe()
    caller_frame: FrameType = frame.f_back.f_back
    module: ModuleType | None = inspect.getmodule(caller_frame)
    module_name: str | None = module.__name__.rsplit(".", maxsplit=1)[-1] if module else None
    function_name: str = caller_frame.f_code.co_name
    if function_name == "<module>":
        function_name = "DeveloperConsole"
    return module_name + "." + function_name if module_name else function_name


def fire_event(source: EventSourceType | None = None,
               action: EventActionType | None = None,
               value: EventValueType | None = None,
               *,
               sender: tuple[str, int] | None = None,
               ts: float | None = None) -> None:
    if not source:
        source = _get_caller_name_and_module()
    services.event_manager.fire_event(source, action, value, sender=sender, ts=ts)


def call_with_frequency(frequency: float | int):
    def decorator(func):
        def wrapper(*args, **kwargs):
            def run_function():
                interval = 1 / frequency  # Calculate interval based on frequency
                setattr(wrapper, "_is_running", True)
                setattr(wrapper, "stop", lambda: setattr(wrapper, "_is_running", False))
                while getattr(wrapper, "_is_running"):
                    func(*args, **kwargs)
                    time.sleep(interval)  # Wait for the calculated interval

            thread = threading.Thread(target=run_function, daemon=True)
            thread.start()

        wrapper()  # Automatically start the function without needing to call it
        return wrapper

    return decorator


def subscribe(callback: CallbackType,
              source_name: EventSourceType | None,
              action: EventActionType | None,
              condition_value: EventValueType | None,
              *,
              fire_once=False,
              allow_parallelism: bool = False
              ) -> None:
    if not services.event_manager:
        raise RuntimeError("Event manager not initialized")
    services.event_manager.subscribe(callback,
                                     source_name,
                                     action,
                                     condition_value,
                                     fire_once=fire_once,
                                     allow_parallelism=allow_parallelism)


def send_dmx(device_name: str, data: bytes):
    device: Device = services.event_manager.devices.get(device_name)
    if device is None:
        print("No device with that name exists in the Device Manifest.")
        return
    if not isinstance(device, Fixture):
        print("Device {device_name} is not a Fixture and hence does not receive DMX signals.")
        return
    universe = device.universe
    print(f"Sending DMX Package to {device_name} @ {universe} with data {data}")
    services.artnet.send_dmx(universe, 0, bytearray(data))
