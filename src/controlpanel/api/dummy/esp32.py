from controlpanel.shared.base import Device


class ESP32:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.mac: str | None = None
        self.ip: str | None = None
        self.status: str | None = "Never connected"
        self.devices: dict[str, Device] = {}
        self.subsequent_missed_replies: int | None = None
