
import asyncio
import websockets
import json
import random


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


class ClientConnection:
    CONNECTING = 1
    AUTHENTICATING = 2
    AUTHENTICATED = 3
    DISCONNECTED = 4
    RECONNECT_DELAY = 5

    _state = None
    _websocket = None

    def __init__(self, token, server="127.0.0.1", port="8000"):
        self.server = server
        self.port = port
        self.token = token
        self.uri = f"ws://{self.server}:{self.port}/ws/?token={self.token}"
        self._state = self.CONNECTING
        

    def connected(self):
        return True if self._state == self.AUTHENTICATED else False



class SmartDash(ClientConnection):
    def __init__(self, token, server="127.0.0.1", port="8000"):
        super().__init__(token, server, port)
        self._on_data_callbacks = {}
        self._handle_data_task = None
        

    async def connect(self):
        try:
            self._websocket = await websockets.connect(self.uri)
            self._state = self.AUTHENTICATED
        except:
            self._state = self.AUTHENTICATING


    async def send_data(self, data):
        data_json = json.dumps(data)
        try:
            await self._websocket.send(data_json)
        except websockets.exceptions.ConnectionClosedError:
            print("Połączenie zostało zamknięte. Ponowne łączenie...")
            await self.reconnect()


    async def receive_data(self):
        data = await self._websocket.recv()
        data_json = json.loads(data)
        return data_json


    async def disconnect(self):
        if self._websocket:
            await self._websocket.close()
            self._state = self.DISCONNECTED


    async def reconnect(self):
        await asyncio.sleep(self.RECONNECT_DELAY)
        await self.connect()


    def on_data(self, virtual_pin):
        def decorator(func):
            if virtual_pin in self._on_data_callbacks:
                self._on_data_callbacks[virtual_pin].append(func)
            else:
                self._on_data_callbacks[virtual_pin] = [func]
            return func
        return decorator
    

    async def write(self, pin: str, value: int | str | float):
        return await self.send_data({"code": MessageCode.WRITE_PIN, "pin": pin, "value": value})


    async def read(self, pin: str):
        await self.send_data({"code": MessageCode.READ_PIN, "pin": pin})
        response_data = await self.receive_data()

        try:
            receive_pin = response_data.get("pin")
            receive_code = response_data.get("code")
            receive_value = response_data.get("value")

            if receive_code == MessageCode.READ_PIN and receive_pin == pin:
                return receive_value
        except:
            pass
    

    async def switch_trigger(self, pin: str, value: bool):
        return await self.send_data({"code": MessageCode.TRIGGER, "pin": pin, "value": value})


    def get_property(self, pin: int, property: str):
        pass


    def set_property(self, pin: int, property: str, value: int | str | float | bool) -> None:
        pass


    def send_sms(self):
        pass


    def send_email(self):
        pass


    async def handle_data(self):
        try:
            while True:
                data = await self.receive_data()
                if isinstance(data, list):
                    for item in data:
                        await self.process_data(item)
                elif isinstance(data, dict):
                    await self.process_data(data)
                else:
                    print("Received invalid data format:", data)
                    
        except websockets.exceptions.ConnectionClosedError:
            print("WebSocket connection closed unexpectedly")
            
        finally:
            self._handle_data_task = None


    async def process_data(self, data):
        code = data.get("code", None)
        if code == MessageCode.ERROR:
            msg = data.get("value", None)
            print(msg)

        pin = data.get("pin", None)
        if pin in self._on_data_callbacks:
            for func in self._on_data_callbacks[pin]:
                if asyncio.iscoroutinefunction(func):
                    await func(data.get("value", ''))
                else:
                    func(data.get("value", ''))

    
    async def run(self):
        try:
            if not self.connected():
                await self.connect()

            if self._handle_data_task is None or self._handle_data_task.done():
                self._handle_data_task = asyncio.create_task(self.handle_data(), name=f'testr{random.randint(0,10000)}')

            await asyncio.wait([self._handle_data_task])
        except:
            await self.disconnect()


