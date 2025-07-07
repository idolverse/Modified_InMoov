import asyncio
import websockets
import json
import threading


class WebSocketBridge:
    def __init__(self, uri="ws://192.168.110.80:8765"):
        self.uri = uri
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.connected_event = threading.Event()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect())
        self.loop.run_forever()

    async def _connect(self):
        self.websocket = await websockets.connect(self.uri)
        self.connected_event.set()

    def send(self, topic, data: dict):
        self.connected_event.wait()
        msg = {
            "topic": topic,
            "data": json.dumps(data)
        }
        asyncio.run_coroutine_threadsafe(
            self.websocket.send(json.dumps(msg)),
            self.loop
        )

    def close(self):
        asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)
        self.loop.call_soon_threadsafe(self.loop.stop)
