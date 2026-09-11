import base64
import hashlib
import socketserver
import struct
from pathlib import Path
import re
import subprocess
import sys
import threading
import os
from datetime import datetime

LOG_PATH = Path(__file__).with_name("rpc.log")
PERSIST_LOCK = threading.Lock()

def log(*parts):
    line = " ".join(str(x) for x in parts)
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as fp:
        fp.write(datetime.now().isoformat(timespec="seconds") + " " + line + "\n")

def exact(sock, size):
    data = b""
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            raise ConnectionError("WebSocket closed")
        data += part
    return data

def recv_text(sock):
    first, second = exact(sock, 2)
    if first & 15 == 8:
        return None
    masked, length = second & 128, second & 127
    if length == 126:
        length = struct.unpack(">H", exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack(">Q", exact(sock, 8))[0]
    mask = exact(sock, 4) if masked else b""
    payload = bytearray(exact(sock, length))
    if masked:
        for i in range(length):
            payload[i] ^= mask[i % 4]
    return bytes(payload).decode("utf-8")

def send_text(sock, value):
    payload = value.encode("utf-8")
    length = len(payload)
    if length < 126:
        header = bytes([129, length])
    elif length <= 65535:
        header = bytes([129, 126]) + struct.pack(">H", length)
    else:
        header = bytes([129, 127]) + struct.pack(">Q", length)
    sock.sendall(header + payload)

class RpcHandler(socketserver.BaseRequestHandler):
    def handle(self):
        log("WebSocket TCP client:", self.client_address)
        request = b""
        while b"\r\n\r\n" not in request:
            chunk = self.request.recv(4096)
            if not chunk:
                return
            request += chunk
        headers = {}
        for line in request.decode("latin1").split("\r\n")[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.lower().strip()] = value.strip()
        key = headers.get("sec-websocket-key")
        if not key:
            log("缺少 Sec-WebSocket-Key，握手失败")
            return
        accept = base64.b64encode(hashlib.sha1(
            (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()
        ).digest()).decode()
        self.request.sendall(("HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n").encode("ascii"))
        log("WebSocket handshake ok:", self.client_address)
        value = recv_text(self.request)
        if value is not None:
            log("RPC_VALUE_RECEIVED:", repr(value))
            # 先确认 RPC 已收到，再异步执行 HTTPS 请求，避免 SSL/网络异常阻塞浏览器。
            send_text(self.request, "ack")
            threading.Thread(target=persist_qn_value, args=(value,), daemon=True).start()


def persist_qn_value(value):
    """写入 test.py，并执行请求/HTML 提取流程。"""
    with PERSIST_LOCK:
        path = Path(__file__).with_name("test.py")
        source = path.read_text(encoding="utf-8")
        replacement = "QN_VALUE = " + repr(value)
        source, count = re.subn(r"^QN_VALUE\s*=.*$", replacement, source, count=1, flags=re.M)
        if count == 0:
            source = replacement + "\n\n" + source
        path.write_text(source, encoding="utf-8")
        log("已写入 test.py: QN_VALUE")
        try:
            result = subprocess.run(
                [sys.executable, str(path)],
                cwd=str(path.parent), capture_output=True, timeout=30,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            for label, data in (("test.py:", result.stdout), ("test.py stderr:", result.stderr)):
                if not data:
                    continue
                try:
                    output = data.decode("utf-8")
                except UnicodeDecodeError:
                    output = data.decode("gb18030", errors="replace")
                for line in output.splitlines():
                    log(label, line)
        except Exception as exc:
            log("执行 test.py 失败:", repr(exc))

class RpcServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with RpcServer(("127.0.0.1", 8080), RpcHandler) as server:
        log("RPC WebSocket listening on ws://127.0.0.1:8080/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
