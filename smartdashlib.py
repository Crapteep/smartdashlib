import asyncio
import websockets
import json
import random
import logging
from typing import Callable, Dict, Any, List, Union
from custom_decorators import disabled

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for Message Codes
class MessageCode:
    READ_PIN = 0
    WRITE_PIN = 1
    GET_PROPERTY = 2
    SET_PROPERTY = 3
    TRIGGER = 4
    SEND_SMS = 5
    SEND_EMAIL = 6
    TRIGGER_SWITCH = 7
    ERROR = 8

# Constants for Connection States
class ConnectionState:
    CONNECTING = 1
    AUTHENTICATING = 2
    AUTHENTICATED = 3
    DISCONNECTED = 4
    RECONNECT_DELAY = 5

class ClientConnection:
    def __init__(self, token: str, server: str = "127.0.0.1", port=None):
        self.server = server
        self.port = port
        self.token = token
        if self.port is None:
            self.uri = f"wss://{self.server}/ws/?token={self.token}"
        else:
            self.uri = f"wss://{self.server}:{self.port}/ws/?token={self.token}"
        self._state = ConnectionState.CONNECTING
        self._websocket = None
        self._recv_lock = asyncio.Lock()

    def connected(self) -> bool:
        return self._state == ConnectionState.AUTHENTICATED

class SmartDash(ClientConnection):
    def __init__(self, token: str, server: str = "127.0.0.1", port=None):
        super().__init__(token, server, port)
        self._on_data_callbacks: Dict[int, List[Callable[[Any], None]]] = {}
        self._handle_data_task: Union[asyncio.Task, None] = None

    async def connect(self) -> None:
        try:
            self._websocket = await websockets.connect(self.uri)
            self._state = ConnectionState.AUTHENTICATED
            logging.info("Connected to WebSocket server.")
        except Exception as e:
            self._state = ConnectionState.AUTHENTICATING
            logging.error(f"Failed to connect to WebSocket server: {e}")

    async def send_data(self, data: Dict[str, Any]) -> None:
        if not self._websocket or self._state != ConnectionState.AUTHENTICATED:
            logging.error("Cannot send data, WebSocket is not connected.")
            return

        data_json = json.dumps(data)
        try:
            await self._websocket.send(data_json)
            # logging.info(f"Sent data: {data_json}")
        except websockets.ConnectionClosed:
            logging.warning("Connection closed. Reconnecting...")
            await self.reconnect()
        except Exception as e:
            logging.error(f"Error sending data: {e}")


    async def receive_data(self) -> Dict[str, Any]:
        async with self._recv_lock:
            try:
                data = await self._websocket.recv()
                data_json = json.loads(data)
                return data_json
            except websockets.ConnectionClosed as e:
                logging.error(f"Error receiving data: {e}")
                raise
            except Exception as e:
                logging.error(f"Unexpected error receiving data: {e}")
                raise

    async def disconnect(self) -> None:
        if self._websocket:
            await self._websocket.close()
            self._state = ConnectionState.DISCONNECTED
            logging.info("Disconnected from WebSocket server.")

    async def reconnect(self) -> None:
        logging.info("Attempting to reconnect...")
        await asyncio.sleep(ConnectionState.RECONNECT_DELAY)
        await self.connect()

    def on_data(self, virtual_pin: int) -> Callable:
        def decorator(func: Callable) -> Callable:
            async def wrapper(data, *args, **kwargs):
                await func(data, *args, **kwargs)
            if virtual_pin in self._on_data_callbacks:
                self._on_data_callbacks[virtual_pin].append(wrapper)
            else:
                self._on_data_callbacks[virtual_pin] = [wrapper]
            return wrapper
        return decorator

    async def write(self, pin: str, value: Union[int, str, float]) -> None:
        await self.send_data({"code": MessageCode.WRITE_PIN, "pin": pin, "value": value})


    @disabled
    async def read(self, pin: str) -> Any:
        await self.send_data({"code": MessageCode.READ_PIN, "pin": pin})
        response_data = await self.receive_data()
        try:
            if response_data.get("code") == MessageCode.READ_PIN and response_data.get("pin") == pin:
                return response_data.get("value")
        except Exception as e:
            logging.error(f"Error reading pin {pin}: {e}")

  

    async def switch_trigger(self, pin: str, value: bool) -> None:
        await self.send_data({"code": MessageCode.TRIGGER, "pin": pin, "value": value})


    @disabled
    def get_property(self, pin: int, property: str) -> None:
        pass


    @disabled
    def set_property(self, pin: int, property: str, value: Union[int, str, float, bool]) -> None:
        pass

    @disabled
    def send_sms(self) -> None:
        pass

    @disabled
    def send_email(self) -> None:
        pass


    async def handle_data(self) -> None:
        try:
            while True:
                data = await self.receive_data()
                if isinstance(data, list):
                    for item in data:
                        await self.process_data(item)
                elif isinstance(data, dict):
                    await self.process_data(data)
                else:
                    logging.warning("Received invalid data format.")
        except websockets.exceptions.ConnectionClosedError:
            logging.error("WebSocket connection closed unexpectedly.")
        finally:
            self._handle_data_task = None


    async def process_data(self, data: Dict[str, Any]) -> None:
        if data.get("code") == MessageCode.ERROR:
            logging.error(f"Error message received: {data.get('value')}")

        pin = data.get("pin")
        if pin in self._on_data_callbacks:
            for func in self._on_data_callbacks[pin]:
                if asyncio.iscoroutinefunction(func):
                    await func(data.get("value", ''))
                else:
                    func(data.get("value", ''))


    async def start(self) -> None:
        while True:
            try:
                if not self.connected():
                    await self.connect()

                if self._handle_data_task is None or self._handle_data_task.done():
                    self._handle_data_task = asyncio.create_task(self.handle_data(), name=f'task_{random.randint(0,10000)}')

                await asyncio.gather(self._handle_data_task)

            except Exception as e:
                logging.error(f"Run loop error: {e}")
                await self.disconnect()


    async def run(self) -> None:
        asyncio.create_task(self.start())
