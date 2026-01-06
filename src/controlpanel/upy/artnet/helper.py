import struct
from micropython import const

# Constants for Art-Net
_ART_NET_HEADER = const(b"Art-Net\x00")
_ART_NET_VERSION = const(b'\x00\x0e')  # Protocol version
_ART_NET_OEM = const(b'\xff\x00')  # OEM code OemUnknown 0x00ff
_ART_NET_ESTA_MAN = const(b'\x00\x00')  # ESTA Manufacturer code


_OP_ARTPOLL = const(0x2000)
_OP_ARTPOLLREPLY = const(0x2100)
_OP_ARTCMD = const(0x2400)
_OP_ARTTRIGGER = const(0x9900)
_OP_ARTDMX = const(0x5000)


def parse_header(data: bytes) -> int | None:
    # Fast length check first
    if len(data) < 10:
        return None

    if data[0:8] != b"Art-Net\x00":
        return None

    # Little-endian uint16 without struct.unpack
    return data[8] | (data[9] << 8)


def parse_poll(data: bytes) -> tuple[int, int, int, int, int, int, int] | None:
    if len(data) < 22:
        return None

    return (
        data[10] | (data[11] << 8),   # ProtVer
        data[12],                     # Flags (bitmask)
        data[13],                     # DiagPriority
        data[14] | (data[15] << 8),   # TargetPort bottom
        data[16] | (data[17] << 8),   # TargetPort top
        data[18] | (data[19] << 8),   # EstaMan
        data[20] | (data[21] << 8),   # Oem
    )


def parse_artdmx(data: bytes) -> tuple[int, int, memoryview] | None:
    if len(data) < 18:
        return None
    return (
        data[12],                           # seq
        data[14] | (data[15] << 8),         # universe
        memoryview(data)[18:],              # DMX data
    )


def parse_trigger(data: bytes) -> tuple[int, int, int, int, memoryview] | None:
    if len(data) < 18:
        return None

    return (
        data[10] | (data[11] << 8),   # ProtVer
        data[14] | (data[15] << 8),   # Oem
        data[16],                     # Key
        data[17],                     # SubKey
        memoryview(data)[18:],        # Data (zero-copy)
    )


def parse_command(data: bytes) -> tuple[int, int, int, memoryview] | None:
    if len(data) < 16:
        return None

    protver = (data[10] << 8) | data[11]
    estaman = (data[12] << 8) | data[13]

    # Length is BIG-ENDIAN at 14–15
    length = (data[14] << 8) | data[15]
    end = 16 + length

    if len(data) < end:
        print(data, end)
        return None

    return (
        protver,
        estaman,
        length,
        memoryview(data)[16:end-1],
    )


# Dictionary of parsers
ARTNET_REPLY_PARSER = [None] * 256
ARTNET_REPLY_PARSER[_OP_ARTPOLL >> 8] = parse_poll
ARTNET_REPLY_PARSER[_OP_ARTTRIGGER >> 8] = parse_trigger
ARTNET_REPLY_PARSER[_OP_ARTDMX >> 8] = parse_artdmx
ARTNET_REPLY_PARSER[_OP_ARTCMD >> 8] = parse_command


def pack_trigger(key: int, subkey: int, data: bytes = b"") -> bytes:
    return (
            _ART_NET_HEADER +
            b'\x00\x99' +
            _ART_NET_VERSION +
            b"\x00\x00" +
            _ART_NET_OEM +
            bytes((key, subkey)) +
            data
    )


def pack_command(command_data: bytearray | bytes) -> bytes:
    if not command_data.endswith(b"\x00"):
        command_data += b"\x00"  # ensure that data is null-terminated

    # size = 512
    size = len(command_data)

    if size > 512:
        raise ValueError("data too long")

    # Length of Command data
    command_length = struct.pack(">H", size)

    op_code = struct.pack("<H", _OP_ARTCMD)
    packet: bytes = (
            _ART_NET_HEADER +
            op_code +
            _ART_NET_VERSION +
            _ART_NET_ESTA_MAN +
            command_length +
            command_data
    )

    return packet


_POLL_VERS_INFO = const(b"\x00\x01")
_POLL_NET_SWITCH = const(b"\x00")
_POLL_SUB_SWITCH = const(b"\x00")
_POLL_OEM = const(b'\xff\x00')
_POLL_UBEA = const(b'\x00')
_POLL_ESTA = const(b"\x00\x00")
_POLL_STATUS1 = const(b"\xC0")
_POLL_NUM_PORTS = const(b"\x00\x01")
_POLL_PORT_TYPES = const(b"\x80\x00\x00\x00")
_POLL_GOOD_IN = const(b"\x00\x00\x00\x00")
_POLL_GOOD_OUT = const(b"\x80\x00\x00\x00")
_POLL_SW_IN = const(b"\x00\x00\x00\x00")
_POLL_SW_OUT = const(b"\x00\x00\x00\x00")
_POLL_VIDEO = const(b"\x00\x00\x00")
_POLL_SPARE = const(b"\x00\x00\x00")
_POLL_STYLE = const(b"\x00")
_POLL_BIND_INDEX = const(b"\x01")
_POLL_STATUS2 = const(b"\x08")
_POLL_FILLER = const(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
_OP_POLL_REPLY = const(b'\x00!')


def pack_poll_reply(
    ip: str,
    port: int,
    short_name: str,
    long_name: str,
    node_report: str,
    mac: str | bytes,
) -> bytes:

    ip_bytes = bytes(int(x) for x in ip.split("."))
    port_bytes = struct.pack(">H", port)

    short_name = short_name[:18].encode("ascii") + b"\x00" * (18 - len(short_name))
    long_name_encoded = long_name.encode("ascii")[:63]
    long_name = long_name_encoded + b"\x00" * (64 - len(long_name_encoded))
    node_report = node_report[:64].encode("ascii") + b"\x00" * (64 - len(node_report))
    mac = mac if isinstance(mac, bytes) else bytes.fromhex(mac.replace(":", ""))

    packet = (
        _ART_NET_HEADER +
        _OP_POLL_REPLY +
        ip_bytes +
        port_bytes +
        _POLL_VERS_INFO +
        _POLL_NET_SWITCH +
        _POLL_SUB_SWITCH +
        _POLL_OEM +
        _POLL_UBEA +
        _POLL_STATUS1 +
        _POLL_ESTA +
        short_name +
        long_name +
        node_report +
        _POLL_NUM_PORTS +
        _POLL_PORT_TYPES +
        _POLL_GOOD_IN +
        _POLL_GOOD_OUT +
        _POLL_SW_IN +
        _POLL_SW_OUT +
        _POLL_VIDEO +
        _POLL_SPARE +
        _POLL_STYLE +
        mac +
        ip_bytes +
        _POLL_BIND_INDEX +
        _POLL_STATUS2 +
        _POLL_FILLER
    )

    assert len(packet) == 239
    return packet
