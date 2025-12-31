import uasyncio as asyncio
from controlpanel.upy.node import Node


node = Node()
asyncio.run(node.update_all_devices())
