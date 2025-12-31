"""Adapted from https://github.com/maximecb/pyopendmx"""

import time
import random
import threading
from pyftdi.ftdi import Ftdi
import numpy as np
from typing import Callable


def get_device_url() -> str | None:
    devices = Ftdi.list_devices()
    if not devices:
        return None
    else:
        device = devices[0]
        vid = hex(device[0].vid)
        pid = hex(device[0].pid)
        sn = device[0].sn
        return f'ftdi://{vid}:{pid}:{sn}/1'


def random_rgb():
    while True:
        color = np.array([
            random.choice([1, 0]),
            random.choice([1, 0]),
            random.choice([1, 0]),
        ])

        if color.any():
            break

    return color


def random_rgbw():
    while True:
        color = np.array([
            random.choice([1, 0]),
            random.choice([1, 0]),
            random.choice([1, 0]),
            random.choice([1, 0]),
        ])

        if color.any():
            break

    return color


def map_to(val, to_min, to_max):
    assert to_max > to_min
    val = np.clip(val, 0, 1)
    return int(round(to_min + val * (to_max - to_min)))


class DMXUniverse:
    """
    Interface to an ENTTEC OpenDMX (FTDI) DMX interface
    """
    def __init__(self, url: str | None, devices: list['DMXDevice'] | None = None, *, target_frequency: int = 20):
        if url is None:
            url = get_device_url()

        self.target_frequency = target_frequency  # In Hz
        # The 0th byte must be 0 (start code)
        # 513 bytes are sent in total
        self.data = bytearray(513 * [0])
        
        self.devices: dict[str, 'DMXDevice'] = {}
        if devices is None:
            devices = []
        for device in devices:
            self.add_device(device)
            
        if url:
            self.url = url
            self.port = Ftdi.create_from_url(url)
            self.port.reset()
            self.port.set_baudrate(baudrate=250000)
            self.port.set_line_property(bits=8, stopbit=2, parity='N', break_=False)
            assert self.port.is_connected
            self.start_dmx_thread()
            print(f"Successfully initiated a DMX universe @ {url}.")
        else:
            print("Was unable to initiate physical DMX Universe: no USB to DMX devices discovered.")

    def __del__(self):
        try:
            self.port.close()
        except AttributeError:
            pass

    def __setitem__(self, idx, val):
        assert (1 <= idx <= 512)
        assert isinstance(val, int)
        assert (0 <= val <= 255)
        self.data[idx] = val

    def set_int(self, start_chan, chan_no, int_val):
        self[start_chan + chan_no - 1] = int_val

    def set_float(self, start_chan, chan_no, val, min=0, max=255):
        assert (chan_no >= 1)

        # If val is an array of values
        if hasattr(val, '__len__'):
            for i in range(len(val)):
                int_val = map_to(val[i], min, max)
                self[start_chan + chan_no - 1 + i] = int_val
        else:
            int_val = map_to(val, min, max)
            self[start_chan + chan_no - 1] = int_val

    def add_device(self, device: 'DMXDevice'):
        # Check if name is already in use:
        if self.devices.get(device.name):
            raise Exception('Device name {} already in use.'.format(device.name))
        
        # Check for partial channel overlaps between devices, which
        # are probably an error
        for other in self.devices.values():
            # Two devices with the same type and the same channel are probably ok
            if device.chan_no == other.chan_no and type(device) == type(other):
                continue

            if device.chan_overlap(other):
                raise Exception('partial channel overlap between devices "{}" and "{}"'.format(device.name, other.name))

        self.devices[device.name] = device
        return device

    def start_dmx_thread(self):
        """
        Thread to write channel data to the output port
        """

        def dmx_thread_fn():
            target_interval = 1.0/self.target_frequency # The maximum update rate for the Enttec OpenDMX is 40Hz
            
            while True:
                start_time = time.time()  # Get the current time at the start of the loop

                current_time = time.time()
                for dev in self.devices.values():
                    if dev._animation is not None:
                        dev.animate(self, current_time)
                    else:
                        dev.update(self)

                self.port.set_break(True)
                self.port.set_break(False)
                self.port.write_data(self.data)

                elapsed_time = time.time() - start_time
                sleep_time = max(0.0, target_interval - elapsed_time)
                if sleep_time == 0:
                    # print(f"Warning: DMX thread could not keep up with target frequency of {self.target_frequency}. "
                    #       f"If this warning appears often, consider lowering it.")
                    pass
                time.sleep(sleep_time)

        dmx_thread = threading.Thread(target=dmx_thread_fn, args=(), daemon=True)
        dmx_thread.start()


class DMXDevice:
    def __init__(self, name: str, chan_no: int, num_chans: int):
        assert (chan_no >= 1)
        self.name = name
        self.chan_no = chan_no
        self.num_chans = num_chans

        self._animation: Callable[[float], tuple[int, ...]] | None = None

    def chan_overlap(self, other: 'DMXDevice'):
        """
        Check if two devices have overlapping channels
        """

        self_last = self.chan_no + (self.num_chans - 1)
        other_last = other.chan_no + (other.num_chans - 1)

        return (
                (other.chan_no <= self.chan_no <= other_last) or
                (self.chan_no <= other.chan_no <= self_last)
        )

    def animate(self, dmx: DMXUniverse, t: float):
        raise NotImplementedError
