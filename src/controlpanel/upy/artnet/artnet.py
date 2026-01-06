import socket
from micropython import const


from .helper import (
    ARTNET_REPLY_PARSER,
    parse_header,
    pack_trigger,
    pack_command,
    pack_poll_reply,
)


_ART_NET_PORT = const(6454)


class ArtNet:
    def __init__(self, ip="255.255.255.255", port=_ART_NET_PORT):
        self.address = (ip, port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rx.bind(("", port))
        self.rx.setblocking(False)

        self._handlers = [None] * 256  # opcode >> 8

    def subscribe(self, opcode, cb):
        self._handlers[opcode >> 8] = cb

    def poll(self):
        try:
            data, addr = self.rx.recvfrom(1024)
        except OSError:
            return

        op = parse_header(data)
        if op is None:
            return

        handler = self._handlers[op >> 8]
        if not handler:
            return

        parser = ARTNET_REPLY_PARSER[op >> 8]
        if not parser:
            return

        payload = parser(data)
        if payload is not None:
            handler(op, addr[0], addr[1], payload)

    def send_trigger(self, key: int, subkey: int, data: bytearray = b"") -> None:
        """Sends a Trigger packet."""
        self._sock.sendto(pack_trigger(key, subkey, data), self.address)

    def send_command(self, command_data: bytearray | bytes = b""):
        """Sends an ArtCommand packet."""
        self._sock.sendto(pack_command(command_data), self.address)

    def send_poll_reply(self,
                        ip: str,
                        port: int = _ART_NET_PORT,
                        address: tuple[str, int] | None = None,
                        short_name: str = "Unnamed Node",
                        long_name: str = "This is an unnamed node",
                        node_report: str = f"#0001 [0000] Missing node report",
                        mac: str | bytes = b"\x02\x00\x00\x00\x00\x01") -> None:
        """Send an ArtPollReply packet."""
        self._sock.sendto(pack_poll_reply(ip,
                                         port,
                                         short_name,
                                         long_name,
                                         node_report,
                                         mac),
                         address or self.address)
