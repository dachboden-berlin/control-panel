import json
from pathlib import Path
import importlib.util
from types import ModuleType, GenericAlias
from . import DEVICE_MANIFEST_PATH
import inspect
from typing import Dict, Set, Tuple, FrozenSet
from controlpanel.api.commons import NodeConfig


STUB_PATH = Path(importlib.util.find_spec("controlpanel.api").origin).parent / "callback.pyi"


def collect_dummy_libs() -> list[ModuleType]:
    """Collects all the modules and packages that may contain classes that are interesting to us"""
    from controlpanel.api import dummy
    return [dummy, ]


def collect_classes_from_libs(libs: list[ModuleType], *, filter_by_base_class: type | None = None) -> list[type]:
    def is_strict_subclass(cls: type, base_class: type) -> bool:
        return issubclass(cls, filter_by_base_class) and cls is not base_class
    collected_classes: list[type] = []
    for lib in libs:
        # Iterate over members of the module
        for name, obj in inspect.getmembers(lib, inspect.isclass):
            # Ensure the class is defined in the module (to avoid inherited ones from imports)
            # Check if obj is subclass of base_class but not the base_class itself
            if filter_by_base_class and not is_strict_subclass(obj, filter_by_base_class):
                continue
            collected_classes.append(obj)
    return collected_classes


def get_device_names_classnames() -> dict[str, str]:
    with open(DEVICE_MANIFEST_PATH, "r") as f:
        data: dict[str, NodeConfig] = json.load(f)
    device_names: dict[str, str] = dict()
    for node_config in data.values():
        for device_name, (class_name, phys_kwargs, dummy_kwargs) in node_config["devices"].items():
            if device_name in device_names.keys():
                raise ValueError(f"Duplicate device name found: {device_name}")
            device_names[device_name] = class_name
    return device_names


def simple_type_name(obj: GenericAlias | type) -> str:
    if isinstance(obj, GenericAlias):
        # For generics like tuple[int, int], just return the string representation
        return str(obj)
    elif isinstance(obj, type):
        # For regular classes like int, return just the name
        return obj.__name__
    else:
        # For anything else, fallback to str()
        return str(obj)


def get_device_dict() -> dict[str, dict[str, str]]:
    """Create a mapping that looks like
    {"red_button": {"ButtonPressed": "bool"}}
    """
    result: dict[str, dict[str, str]] = dict()

    device_names_classnames: dict[str, str] = get_device_names_classnames()

    from controlpanel.api.dummy import Sensor
    dummy_sensor_classes: list[type] = collect_classes_from_libs(collect_dummy_libs(), filter_by_base_class=Sensor)
    dummy_sensor_class_mapping: dict[str, type] = {cls.__name__: cls for cls in dummy_sensor_classes}

    sensor_names: dict[str, str] = {name: class_name for name, class_name in device_names_classnames.items() if class_name in dummy_sensor_class_mapping.keys()}

    for sensor_name, sensor_class_name in sensor_names.items():
        sensor_class = dummy_sensor_class_mapping[sensor_class_name]
        event_types = getattr(sensor_class, "EVENT_TYPES")
        result[sensor_name] = {action_name: simple_type_name(value_type) for action_name, value_type in event_types.items()}

    return result


def literal_union_str(items: Set[str]) -> str:
    items = sorted(set(items))
    items_escaped = [f'"{item}"' for item in items]
    literal_single = f"Literal[{', '.join(items_escaped)}]"
    literal_list = f"List[{literal_single}]"
    return f"{literal_single} | {literal_list}"


def generate_overloads(devices: Dict[str, Dict[str, str]]) -> str:
    group_map: Dict[FrozenSet[Tuple[str, str]], Set[str]] = {}

    for device, actions in devices.items():
        key = frozenset(actions.items())
        group_map.setdefault(key, set()).add(device)

    lines = []
    for action_value_set, device_set in group_map.items():
        devices_literal = literal_union_str(device_set)

        if not action_value_set:
            # fallback typing for empty actions
            action_type_str = "str | List[str]"
            base_value_type = "Hashable"
            value_type_str = f"{base_value_type} | List[{base_value_type}]"
        else:
            actions = sorted(action_value_set, key=lambda x: x[0])
            action_names = [act for act, _ in actions]
            action_type_str = literal_union_str(set(action_names))

            value_types = {val for _, val in actions}
            if len(value_types) == 1:
                base_value_type = next(iter(value_types))
            else:
                base_value_type = " | ".join(sorted(value_types))
            value_type_str = f"{base_value_type} | List[{base_value_type}]"

        lines.append("@overload")
        lines.append("def callback(")
        lines.append("    *,")
        lines.append(f"    source: {devices_literal} | None = None,")
        lines.append(f"    action: {action_type_str} | None = None,")
        lines.append(f"    value: {value_type_str} | None = None,")
        lines.append("    fire_once: bool = False,")
        lines.append("    allow_parallelism: bool = False,")
        lines.append(
            f") -> Callable[[Callable[[Event[{base_value_type}]], None]], Callable[[Event[{base_value_type}]], None]]: ...")
        lines.append("")
    return "\n".join(lines)


def generate_callback_stub_file():
    header = '''"""This file has been auto-generated by the generate_stubs script"""
from typing import Callable, List, Literal, Hashable, overload
from controlpanel.api import Event

'''

    pyi_content = header + generate_overloads(get_device_dict())
    Path(STUB_PATH).write_text(pyi_content)

if __name__ == "__main__":
    generate_callback_stub_file()
