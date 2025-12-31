from .artnet import ArtNet, OpCode
from micropython import const

KEY = const(76)


# def receive(op_code: OpCode, ip: str, port: int, reply) -> None:
#     print(f"Received {hex(op_code)} from {ip}:{port}")
#
#     for k, v in reply.items():
#         print(f"\t{k} = {v}")
