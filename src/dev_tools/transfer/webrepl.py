import socket
import struct
import os
import time

WEBREPL_PORT = 8266
WEBREPL_FRAME_TXT = 0x81
WEBREPL_FRAME_BIN = 0x82

WEBREPL_REQ_S = "<2sBBQLH64s"
WEBREPL_PUT_FILE = 1
WEBREPL_GET_FILE = 2
WEBREPL_GET_VER  = 3


class WebSocket:
    """Minimal WebSocket implementation for MicroPython WebREPL."""

    def __init__(self, s):
        self.s = s
        self.buf = b""

    def write(self, data, frame=WEBREPL_FRAME_BIN):
        l = len(data)
        if l < 126:
            hdr = struct.pack(">BB", frame, l)
        else:
            hdr = struct.pack(">BBH", frame, 126, l)
        self.s.sendall(hdr + data)

    def recvexactly(self, sz):
        res = b""
        while len(res) < sz:
            data = self.s.recv(sz - len(res))
            if not data:
                break
            res += data
        return res

    def read(self, size=None, text_ok=False):
        if not self.buf:
            hdr = self.recvexactly(2)
            if len(hdr) != 2:
                return b""
            fl, sz = struct.unpack(">BB", hdr)
            if sz == 126:
                hdr = self.recvexactly(2)
                (sz,) = struct.unpack(">H", hdr)
            data = self.recvexactly(sz)
            if (fl == 0x82) or (text_ok and fl == 0x81):
                self.buf = data
            else:
                return b""
        if size is None:
            size = len(self.buf)
        d = self.buf[:size]
        self.buf = self.buf[size:]
        return d

    def close(self):
        try:
            self.s.close()
        except:
            pass


def handshake(sock):
    """Minimal WebSocket handshake."""
    cl = sock.makefile("rwb", 0)
    cl.write(b"GET / HTTP/1.1\r\n"
             b"Host: esp8266\r\n"
             b"Connection: Upgrade\r\n"
             b"Upgrade: websocket\r\n"
             b"Sec-WebSocket-Key: foo\r\n"
             b"\r\n")
    # read until blank line
    while True:
        line = cl.readline()
        if not line or line == b"\r\n":
            break


def login(ws, password) -> None:
    """Wait for password prompt and send password."""
    login_time = time.time()
    while True:
        c = ws.read(text_ok=True)
        if b":" in c:  # Password: prompt
            ws.write(password.encode() + b"\r", WEBREPL_FRAME_TXT)
            break
        if time.time() > login_time + 10.0:
            raise ConnectionRefusedError("Connection refused. (Different session?)")
    # wait for '>>>'
    while True:
        c = ws.read(text_ok=True)
        if b">>>" in c:
            return
        if b"Access denied" in c:
            raise ConnectionRefusedError("Wrong password!")


def read_resp(ws):
    data = ws.read(4)
    if len(data) < 4:
        raise IOError("Invalid response length")
    sig, code = struct.unpack("<2sH", data)
    if sig != b"WB":
        raise IOError("Bad response signature")
    return code


def send_req(ws, op, sz=0, fname=b""):
    rec = struct.pack(WEBREPL_REQ_S, b"WA", op, 0, 0, sz, len(fname), fname)
    ws.write(rec)


def webrepl_put(ws, local_file: str, remote_file: str):
    """Upload a file to the remote device via WebREPL."""
    sz = os.stat(local_file).st_size
    dest = remote_file.encode("utf-8")
    rec = struct.pack(WEBREPL_REQ_S, b"WA", WEBREPL_PUT_FILE, 0, 0, sz, len(dest), dest)
    ws.write(rec[:10])
    ws.write(rec[10:])
    if read_resp(ws) != 0:
        raise OSError("Remote refused file write request")

    sent = 0
    with open(local_file, "rb") as f:
        while True:
            buf = f.read(1024)
            if not buf:
                break
            ws.write(buf)
            sent += len(buf)
            print(f"Sent {sent}/{sz} bytes", end="\r")
    print()
    if read_resp(ws) != 0:
        raise OSError("Remote write failed")
    print(f"Uploaded {local_file} -> {remote_file}")


def webrepl_get(ws, local_file, remote_file):
    """Download a file from the remote device via WebREPL."""
    src = remote_file.encode("utf-8")
    rec = struct.pack(WEBREPL_REQ_S, b"WA", WEBREPL_GET_FILE, 0, 0, 0, len(src), src)
    ws.write(rec)
    if read_resp(ws) != 0:
        raise OSError("Remote refused read request")

    with open(local_file, "wb") as f:
        total = 0
        while True:
            ws.write(b"\0")
            sz_bytes = ws.read(2)
            (sz,) = struct.unpack("<H", sz_bytes)
            if sz == 0:
                break
            data = ws.read(sz)
            f.write(data)
            total += len(data)
            print(f"Received {total} bytes", end="\r")
    print()
    if read_resp(ws) != 0:
        raise OSError("Remote read failed")
    print(f"✅ Downloaded {remote_file} -> {local_file}")


def run_webrepl_cmd(ws: WebSocket, command):
    ws.write(command.encode("utf-8") + b"\r", WEBREPL_FRAME_TXT)
    time.sleep(0.25)

    output = b""
    while True:
        data = ws.read(text_ok=True)
        if not data:
            break
        output += data
        if b">>>" in data:
            break

    return output.decode(errors="ignore")


def webrepl_interrupt(ws: WebSocket):
    """Experimental!"""
    ws.write(b"\x03", WEBREPL_FRAME_TXT)  # Ctrl-C interrupt


def webrepl_connect(host, password, port=WEBREPL_PORT, timeout: float = 30.0) -> WebSocket:
    """Open and return a persistent WebREPL connection (WebSocket)."""
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((host, port))
    handshake(s)
    ws = WebSocket(s)
    login(ws, password)
    return ws
