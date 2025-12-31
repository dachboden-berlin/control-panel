import socket
import _thread


from .helper import (
    ARTNET_REPLY_PARSER,
    OpCode,
    parse_header,
    pack_address,
    pack_dmx,
    pack_ip,
    pack_nzs,
    pack_poll,
    pack_sync,
    pack_trigger,
    pack_command,
    pack_poll_reply,
)

ART_NET_PORT = 6454

ASCII = 0
MACRO = 1
SOFT = 2
SHOW = 3
UNDEFINED = 4  # 4-255

DEFAULT_FPS = 40.0

ArtNetCallback = object


class ArtNet:
    def __init__(self, ip: str = "255.255.255.255", port: int = ART_NET_PORT) -> None:
        self.address = (ip, port)

        # Create a UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.server_thread = _thread.start_new_thread(self.__init_socket, ())

        self.register: dict[OpCode, ArtNetCallback] = {}

    @property
    def ip(self) -> str:
        return self.address[0]

    @property
    def port(self) -> int:
        return self.address[1]

    def __init_socket(self):
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_server.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_server.bind(('', ART_NET_PORT))  # Listen on any valid IP
        self.socket_server.setblocking(False)  # Set socket to non-blocking mode

        self.socket_server.settimeout(None)

        while True:
            self.receive()

    def __del__(self) -> None:
        self.sock.close()

    @staticmethod
    def to_universe15bit(self, universe: int, net: int, subnet: int) -> int:
        # Calculating the 15-bit universe from net, subnet, and universe
        return ((net & 0b1111111) << 8) | ((subnet & 0b1111) << 4) | universe & 0b1111

    def subscribe(self, op_code: OpCode, callback: ArtNetCallback) -> None:
        self.register[op_code] = callback

    def subscribe_all(self, callback: ArtNetCallback) -> None:
        for op_code in ARTNET_REPLY_PARSER.keys():
            self.register[op_code] = callback

    def unsubscibe(self, op_code: OpCode) -> None:
        if op_code in self.register:
            del self.register[op_code]

    def receive(self, buffer_size: int = 1024) -> None:
        # Buffer size of 1024 bytes
        data, addr = self.socket_server.recvfrom(buffer_size)
        op_code = parse_header(data)
        if op_code is not None:
            parser = ARTNET_REPLY_PARSER.get(op_code, lambda x: x)
            subscriber = self.register.get(op_code)

            if subscriber is None:
                return

            reply = parser(data)
            if reply is None:
                return

            subscriber(op_code, *addr, reply)

    def send_poll(self) -> None:
        """Send an ArtPoll packet."""

        self.sock.sendto(pack_poll(), self.address)

    def send_dmx(self, universe15bit: int, seq: int, dmx_data: bytearray) -> None:
        """Send an ArtDmx packet."""
        self.sock.sendto(pack_dmx(universe15bit, seq, dmx_data), self.address)

    def send_nzs(
            self, universe15bit: int, sequence: int, start_code: int, dmx_data: bytearray
    ) -> None:
        """Send an ArtNzs packet."""
        self.sock.sendto(
            pack_nzs(universe15bit, sequence, start_code, dmx_data), self.address
        )

    def send_trigger(self, key: int, subkey: int, data: bytearray = b"") -> None:
        """Sends a Trigger packet."""
        self.sock.sendto(pack_trigger(key, subkey, data), self.address)

    def send_sync(self) -> None:
        """Sends a Sync packet."""
        self.sock.sendto(pack_sync(), self.address)

    def send_command(self, command_data: bytearray | bytes = b""):
        """Sends an ArtCommand packet."""
        self.sock.sendto(pack_command(command_data), self.address)

    def send_poll_reply(self,
                        ip: str,
                        port: int = ART_NET_PORT,
                        address: tuple[str, int] | None = None,
                        short_name: str = "Unnamed Node",
                        long_name: str = "This is an unnamed node",
                        node_report: str = f"#0001 [0000] Missing node report",
                        mac: str | bytes = b"\x02\x00\x00\x00\x00\x01") -> None:
        """Send an ArtPollReply packet."""
        self.sock.sendto(pack_poll_reply(ip,
                                         port,
                                         short_name,
                                         long_name,
                                         node_report,
                                         mac),
                         address or self.address)

    def configure_ip(
            self,
            dhcp: bool = False,
            prog_ip: str | None = None,
            prog_sm: str | None = None,
            prog_gw: str | None = None,
            reset: bool = False,
    ) -> None:
        """
        Set the IP address, subnet mask and the default gateway, enable DHCP or reset.
        If values are None, they will not be set.
        :param prog_ip: The IP address to set (e.g., '192.168.0.100').
        :param prog_sm: The subnet mask to set (e.g., '255.255.255.0').
        :param prog_gw: The default gateway to set (e.g., '192.168.0.1').
        :param dhcp: Whether to enable DHCP. If True, IP, SM, and GW will be ignored.
        """
        self.sock.sendto(
            pack_ip(
                dhcp,
                prog_ip,
                prog_sm,
                prog_gw,
                reset,
            ),
            self.address,
        )

    def configure_universe(
            self,
            net: int,
            sub: int,
            universe: int,
    ) -> None:
        """
        Set the universe for ArtNet nodes.

        :param net: The net switch (0-127).
        :param sub: The sub switch (0-15).
        :param universe: The universe (0-15).
        """
        self.sock.sendto(
            pack_address(
                net,
                sub,
                universe,
            ),
            self.address,
        )
