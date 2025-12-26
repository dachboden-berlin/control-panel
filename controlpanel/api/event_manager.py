from typing import Any, Iterable
from types import ModuleType
import time
from threading import Thread
import asyncio
import inspect
from collections import defaultdict
from controlpanel.shared.base import Device
from controlpanel.api.dummy import Sensor, Fixture
import pygame as pg
from artnet import ArtNet, OpCode, ART_NET_PORT
import importlib.resources
import json
import io
from controlpanel.api.dummy.esp32 import ESP32
from anaconsole import console_command
from controlpanel import api
from controlpanel import dmx
from .commons import (
    Event,
    Condition,
    Subscriber,
    CallbackType,
    EventSourceType,
    EventActionType,
    EventValueType,
    KEY_CONTROL_PANEL_PROTOCOL,
    CONTROL_PANEL_EVENT,
    NodeConfig,
)


class EventManager:
    POSSIBLE_EVENT_TYPES = [
        lambda source, name, value: (source, name, value),
        lambda source, name, value: (source, name, None),
        lambda source, name, value: (source, None, value),
        lambda source, name, value: (source, None, None),
        lambda source, name, value: (None, name, value),
        lambda source, name, value: (None, name, None),
        lambda source, name, value: (None, None, value),
        lambda source, name, value: (None, None, None),
    ]
    DEVICE_MANIFEST_FILENAME = 'device_manifest.json'
    ARTPOLL_INTERVAL: int = 60

    def __init__(self, artnet: ArtNet):
        self._artnet: ArtNet = artnet
        self._artnet.subscribe_all(self._receive)
        Thread(target=artnet.listen, args=(None,), daemon=True).start()

        self.devices: dict[str, Device] = dict()
        self._sensor_dict: dict[str, Sensor] = dict()
        self._fixture_dict: dict[str, Fixture] = dict()
        self._ip: str = self._get_local_ip()

        self._callback_register: dict[Condition, list[Subscriber]] = defaultdict(list)
        self._event_queue = asyncio.Queue()
        self._reply_queue = asyncio.Queue()
        self._ping_queue = asyncio.Queue()
        self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        Thread(target=self._run_async_loop, args=(), daemon=True).start()

        self._artpoll_response_future: asyncio.Future | None = None
        self._nodes: list[ESP32] = list()

        self.print_incoming_arttrigger_packets: bool = False
        self.print_incoming_artdmx_packets: bool = False
        self.print_incoming_artcmd_packets: bool = False
        self.print_incoming_artpollreply_packets: bool = False
        self._accept_own_broadcast: bool = False

    @console_command
    def ping(self, name_or_ip: str, pings: int = 4, timeout: float = 1.0) -> None:
        ip = self._get_ip_from_name_or_ip(name_or_ip)
        if not ip:
            return
        self.loop.create_task(self._ping(ip, pings, timeout))

    @staticmethod
    def median(values: Iterable[float]) -> float:
        nums = sorted(values)
        n = len(nums)
        if n == 0:
            raise ValueError("Empty input")
        mid = n // 2
        return nums[mid] if n % 2 else (nums[mid - 1] + nums[mid]) / 2

    async def _ping(self, ip: str, pings: int, timeout: float) -> None:
        print(f"Sending {pings} pings to {ip}...")
        reply_times: list[float] = []
        timeouts: int = 0
        for _ in range(pings):
            start = time.perf_counter()
            self._artnet.send_command(b"PING", ip_override=ip)
            try:
                while True:
                    await asyncio.wait_for(self._ping_queue.get(), timeout=timeout)
                    stop = time.perf_counter()
                    reply_times.append(stop - start)
                    break
            except asyncio.TimeoutError:
                reply_times.append(float("inf"))
                timeouts += 1
                if timeouts > len(reply_times) // 2 and len(reply_times) > 5:
                    print(f"Timed out {timeouts} / {len(reply_times)} times. Aborting.")
                    return
            await asyncio.sleep(0.01)
        print(f"Received {len(list(r for r in reply_times if r != float('inf')))}/{len(reply_times)} pings. "
              f"Average/Median/Min/Max response times: "
              f"{1000 * sum(reply_times) / len(reply_times):.0f}/"
              f"{1000 * self.median(reply_times):.0f}/"
              f"{1000 * min(reply_times):.0f}/"
              f"{1000 * max(reply_times):.0f}ms".replace("inf", "∞"))

    @property
    def ip(self) -> str:
        return self._ip

    def _run_async_loop(self):
        self.loop.create_task(self._dispatch_loop())
        self.loop.create_task(self._poll_loop(self.ARTPOLL_INTERVAL))
        self.loop.run_forever()

    async def _dispatch_loop(self):
        while True:
            event = await self._event_queue.get()
            await self._notify_subscribers(event)

    async def _poll_and_collect(self, timeout=3.0) -> list[dict[str, Any]]:
        replies: list[dict[str, Any]] = []
        end_time = asyncio.get_running_loop().time() + timeout
        self._artnet.send_poll()
        while True:
            remaining = end_time - asyncio.get_running_loop().time()
            if remaining <= 0:
                break
            try:
                reply: dict[str, Any] = await asyncio.wait_for(self._reply_queue.get(), timeout=min(remaining, 0.1))
                replies.append(reply)
            except asyncio.TimeoutError:
                pass
        return replies

    def _handle_artpoll_replies(self, replies: list[dict[str, Any]]) -> None:
        collected_mac_addresses: set[str] = set()  # a set of all MAC addresses from nodes that replied to our poll
        for reply in replies:
            name: str = reply['ShortName']
            mac: str = reply['Mac']
            collected_mac_addresses.add(mac)
            if mac not in (esp.mac for esp in self._nodes):
                if name not in (esp.name for esp in self._nodes):
                    print(f"Unknown ESP '{name}' with mac {mac} has been registered")
                    esp = ESP32(name)
                    esp.mac = mac
                    esp.ip = reply["IpAddress"]
                    esp.status = reply['NodeReport']
                    self._nodes.append(esp)
                else:
                    esp = next((esp for esp in self._nodes if esp.name == name))
                    esp.mac = mac
                    esp.ip = reply["IpAddress"]
                    esp.status = reply['NodeReport']
                    esp.subsequent_missed_replies = 0
                    print(f"ESP '{name}' with mac {mac} connected for the first time")
            else:
                esp = next((esp for esp in self._nodes if esp.mac == mac), None)
                if esp.subsequent_missed_replies > 0:
                    print(f"ESP '{esp.name}' has regained the connection!")
                esp.name = name
                esp.ip = reply['IpAddress']
                esp.status = reply['NodeReport']
                esp.subsequent_missed_replies = 0
        for esp in self._nodes:
            if esp.status == "Lost connection!" or esp.status == "Never connected":
                continue
            if esp.mac not in collected_mac_addresses:
                esp.subsequent_missed_replies += 1
                print(f"ESP '{esp.name}' failed to reply! ({esp.subsequent_missed_replies} missed repl{'ies' if esp.subsequent_missed_replies > 1 else 'y'})")
                if esp.subsequent_missed_replies >= 3:
                    print(f"ESP '{esp.name}' lost the connection!")
                    esp.status = 'Lost connection!'

    async def _poll_loop(self, poll_interval_seconds: int = 10):
        while True:
            await self._poll()
            for _ in range(poll_interval_seconds):
                await asyncio.sleep(1)

    async def _poll(self):
        self._artnet.send_poll()
        replies: list[dict[str, Any]] = []
        while not self._reply_queue.empty():
            replies.append(self._reply_queue.get_nowait())
        self._handle_artpoll_replies(replies)

    @staticmethod
    def _get_local_ip() -> str:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            return s.getsockname()[0]
        except Exception:  # TODO: what exception can be thrown here?
            return '127.0.0.1'
        finally:
            s.close()

    def instantiate_devices(self, libs: Iterable[ModuleType], *, assign_sequential_universes: bool = False, start_universe: int = 5000) -> None:
        """Read the device_manifest.json and instantiate the devices into a dictionary.
        NOTE: assign_sequential_universes is not yet implemented in the upy package, rendering the feature effectively broken.
        """
        def find_class_in_modules(modules: Iterable[ModuleType], name: str) -> type | None:
            for module in modules:
                cls = getattr(module, name, None)
                if cls and isinstance(cls, type):
                    return cls
            return None

        with importlib.resources.open_binary("controlpanel.shared", self.DEVICE_MANIFEST_FILENAME) as file:
            manifest: dict[str, NodeConfig] = json.load(io.BytesIO(file.read()))

        universe = start_universe
        for node_name, node_config in manifest.items():
            if not node_name in (node.name for node in self._nodes):
                self._nodes.append(ESP32(node_name))
            esp = next((esp for esp in self._nodes if esp.name == node_name), None)
            for device_name, (class_name, phys_kwargs, dummy_kwargs) in node_config["devices"].items():
                kwargs = phys_kwargs | dummy_kwargs
                cls = find_class_in_modules(libs, class_name)
                if cls is None:
                    print(f"Failed to find {class_name} in any of these modules: {[lib.__name__ for lib in libs]}")
                    continue
                if issubclass(cls, Fixture) and assign_sequential_universes and kwargs.get("universe") is None:
                    kwargs["universe"] = universe
                    print(f"Assigned universe {universe} to {kwargs.get('name', '<UNKNOWN>')}.")
                    universe += 1
                filtered_kwargs = {key: value for key, value in kwargs.items()
                                   if key in cls.__init__.__code__.co_varnames}
                try:
                    if issubclass(cls, Fixture):
                        device = cls(self._artnet, self.loop, esp, device_name, **filtered_kwargs)
                    elif issubclass(cls, Sensor):
                        device = cls(self._artnet, device_name, **filtered_kwargs)
                    elif issubclass(cls, dmx.DMXDevice):
                        device = cls(device_name, **filtered_kwargs)
                    else:
                        raise ValueError(f"Unknown device type: {type(cls)}")
                except TypeError:
                    print(f"Type Error raised when instantiating {filtered_kwargs.get('name')}.")
                    raise

                esp.devices[device.name] = device

        self.devices = {name: device for esp in self._nodes for name, device in esp.devices.items()}
        self._sensor_dict = {name: device for name, device in self.devices.items() if isinstance(device, Sensor)}
        self._fixture_dict = {device.universe: device for device in self.devices.values() if isinstance(device, Fixture)}

    def _parse_trigger(self, reply: dict[str, Any], sender: tuple[str, int], ts: float):
        if self.print_incoming_arttrigger_packets:
            print(f"Receiving ArtTrigger event from {sender[0]}: {reply}")

        key = reply.get("Key")
        if key != KEY_CONTROL_PANEL_PROTOCOL:
            return

        data: bytes = reply.get("Data", b"")
        data_fields = data.split(b"\x00", maxsplit=1)
        if len(data_fields) != 2:
            return

        sensor_name: str = data_fields[0].decode("ascii")
        sensor_data: bytes = data_fields[1]

        sensor: Sensor | None = self._sensor_dict.get(sensor_name)
        if sensor is None:
            return

        seq = reply.get("SubKey")
        if sensor.should_ignore_seq(seq):
            return
        sensor._seq = seq

        if sensor.muted:
            return
        sensor.parse_trigger_payload(sensor_data, ts)

    def _parse_dmx(self, reply: dict[str, Any], sender: tuple[str, int], ts: float) -> None:
        if not self.print_incoming_artdmx_packets:
            return
        universe = reply.get("Universe")
        fixture: Fixture | None = self._fixture_dict.get(universe)
        values = [int(byte) for byte in reply.get("Data")]
        if fixture:
            print(f"Receiving ArtDMX event from {sender[0]} to fixture {fixture.name}: {values}")
        else:
            print(f"Receiving ArtDMX event from {sender[0]} to universe {reply.get('Universe')}: {reply.get('Data')}")

    def _parse_artpollreply(self, reply: dict[str, Any], sender: tuple[str, int], ts: float) -> None:
        if self.print_incoming_artpollreply_packets:
            print(f"Receiving ArtPollReply event from {sender[0]}: {reply}")
        self.loop.call_soon_threadsafe(self._reply_queue.put_nowait, reply)

    def _parse_artcmd(self, reply: dict[str, Any], sender: tuple[str, int], ts: float) -> None:
        if self.print_incoming_artcmd_packets:
            print(f"Receiving ArtCommand event from {sender[0]}: {reply.get('Command')}")
        if reply.get("Command") == "RETURN_PING":
            self.loop.call_soon_threadsafe(self._ping_queue.put_nowait, reply.get("Command"))

    def _parse_op(self, sender: tuple[str, int], ts: float, op_code: OpCode, reply: dict[str, Any]) -> None:
        match op_code:
            case OpCode.ArtTrigger:
                self._parse_trigger(reply, sender, ts)
            case OpCode.ArtDmx:
                self._parse_dmx(reply, sender, ts)
            case OpCode.ArtCommand:
                self._parse_artcmd(reply, sender, ts)
            case OpCode.ArtPollReply:
                self._parse_artpollreply(reply, sender, ts)
            case _:
                try:
                    print(f"Received an {OpCode(op_code).name} packet from "
                          f"{sender[0] if sender[0] != self._ip else 'this device'}")
                except ValueError:
                    print(f"Received a packet with invalid op code {hex(op_code)}")

    def _get_ip_from_name_or_ip(self, name_or_ip: str) -> str | None:
        from ipaddress import IPv4Address
        try:
            IPv4Address(name_or_ip)
            return name_or_ip
        except ValueError:
            try:
                ip: str | None = next((esp for esp in self._nodes if esp.name == name_or_ip)).ip
                if not ip:
                    print(f"Node '{name_or_ip}' has no registered IP address.")
                    return None
                return ip
            except StopIteration:
                print(f"{name_or_ip} is neither a valid IPv4 address nor the name of a registered ArtNet node")
                return None

    @console_command(is_cheat_protected=True)
    def send_artcmd(self, cmd: str, name_or_ip: str | None = None) -> None:
        """Sends the given ASCII string as an ArtCommand packet via Artnet"""
        ip = self._get_ip_from_name_or_ip(name_or_ip) if name_or_ip else "255.255.255.255"
        self._artnet.send_command(cmd.encode("ascii"), ip_override=ip)
        if name_or_ip:
            print(f"Sent command '{cmd}' to '{name_or_ip}'.")
        else:
            print(f"Broadcast command '{cmd}' to all nodes in network.")

    @console_command(is_cheat_protected=True)
    def send_artdmx(self, device_name_or_universe: str | int, *values: int) -> None:
        """Sends any number of integer values (0-255) to the universe of the given device"""
        data = bytes(values)
        if type(device_name_or_universe) is str:
            api.send_dmx(device_name_or_universe, data)
        elif type(device_name_or_universe) is int and 0 <= device_name_or_universe < 2**15:
            self._artnet.send_dmx(device_name_or_universe, 0, bytearray(data))

    @console_command(is_cheat_protected=True)
    def send_arttrigger(self, key: int, subkey: int, data: str):
        """Sends the given ASCII string as an ArtCommand packet via Artnet"""
        self._artnet.send_trigger(key, subkey, bytearray(data.encode("ASCII")))

    @console_command(is_cheat_protected=True)
    def send_artpoll(self, name_or_ip: str | None = None) -> None:
        ip = self._get_ip_from_name_or_ip(name_or_ip) if name_or_ip else "255.255.255.255"
        self._artnet.send_poll(ip_override=ip)

    @console_command(is_cheat_protected=True)
    def poll(self):
        self.loop.create_task(self._poll())

    @console_command(is_cheat_protected=True)
    def set_dmx_attr(self, device_name: str, attribute: str, value):
        """Sets any attribute of any DMX device to any value"""
        setattr(api.dmx.devices.get(device_name), attribute, value)

    @console_command("arttrigger_debug")
    def set_enable_print_arttrigger_packets(self, enable: int):
        self.print_incoming_arttrigger_packets = bool(enable)

    @console_command("artdmx_debug")
    def set_enable_print_artdmx_packets(self, enable: int):
        self.print_incoming_artdmx_packets = bool(enable)

    @console_command("artcmd_debug")
    def set_enable_print_artcmd_packets(self, enable: int):
        self.print_incoming_artcmd_packets = bool(enable)

    @console_command("artpollreply_debug")
    def set_enable_print_artpollreply_packets(self, enable: int):
        self.print_incoming_artpollreply_packets = bool(enable)

    @console_command("accept_own_broadcast")
    def set_enable_accept_own_broadcast(self, enable: int):
        self._accept_own_broadcast = bool(enable)

    @console_command(is_cheat_protected=True)
    def fire_event(self,
                   source: EventSourceType,
                   action: EventActionType,
                   value: EventValueType, *,
                   sender: tuple[str, int] | None = None,
                   ts: float | None = None) -> None:
        sender = sender if sender is not None else (self._ip, ART_NET_PORT)
        ts = ts if ts is not None else time.time()
        event = Event(source, action, value, sender, ts)
        print(f"{'Firing event:':<16}{event.source:<20} -> {event.action:<20} -> {str(event.value):<20} from {event.sender}")
        pg.event.post(pg.event.Event(CONTROL_PANEL_EVENT, source=event.source, name=event.action, value=event.value, sender=event.sender))
        asyncio.run_coroutine_threadsafe(self._event_queue.put(event), self.loop)

    async def _notify_subscribers(self, event: Event) -> None:
        for key_func in self.POSSIBLE_EVENT_TYPES:
            source, name, value = key_func(event.source, event.action, event.value)
            subscribers: list[Subscriber] = self._callback_register.get(Condition(source, name, value), [])
            for subscriber in subscribers:
                if not subscriber.allow_parallelism:
                    if subscriber.task is not None and not subscriber.task.done():
                        print(f"[EventManager] Skipping {subscriber.callback.__name__}: still running.")
                        continue
                print(f"{'Event received: ':<16}{subscriber.callback.__module__.rsplit('.')[-1]}.{subscriber.callback.__name__}")

                if inspect.iscoroutinefunction(subscriber.callback):
                    if subscriber.requires_event_arg:
                        task = asyncio.create_task(subscriber.callback(event))
                    else:
                        task = asyncio.create_task(subscriber.callback())
                    subscriber.task = task
                else:
                    # Run sync function in a thread, wrap it in a future
                    if subscriber.requires_event_arg:
                        task = asyncio.to_thread(subscriber.callback, event)
                    else:
                        task = asyncio.to_thread(subscriber.callback)
                    subscriber.task = asyncio.create_task(task)

                if subscriber.fire_once:
                    subscribers.remove(subscriber)

    def _receive(self, op_code: OpCode, ip: str, port: int, reply: Any) -> None:
        if ip == self._ip and not self._accept_own_broadcast:
            return  # ignore packet if it's ours
        sender = (ip, port)
        ts = time.time()
        self._parse_op(sender, ts, op_code, reply)

    def subscribe(self,
                  callback: CallbackType,
                  source: EventSourceType,
                  action: EventActionType,
                  value: EventValueType = None,
                  *,
                  fire_once: bool = False,
                  allow_parallelism: bool = False) -> None:
        arg_count = callback.__code__.co_argcount
        is_method = inspect.ismethod(callback)
        requires_event_arg = arg_count == 1 if not is_method else arg_count == 2
        subscriber = Subscriber(callback, fire_once, allow_parallelism, requires_event_arg)
        condition = Condition(source, action, value)
        self._callback_register[condition].append(subscriber)
