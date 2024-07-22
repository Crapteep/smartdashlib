import asyncio
import math
import pyautogui
from smartdashlib import SmartDash
from utils.joystick import Joystick, Vector2D


"""
Simple mouse controlled by SmartDash app


For this example, you need to create 3 virtual pins:
1. V1 - for the joystick
2. V3 - for the mouse button (min: 0, max: 1, value: 0)
3. V2 - for the mouse speed (min: 0, max: 500)

Additionally, you need to add 4 elements to your dashboard and connect them to the corresponding pins:
1. Input (V2)
2. Button LPM [on_click_value=0] (V3)
3. Button PPM [on_click_value=1] (V3)
4. Joystick (V1)

You also need to add your token, which you can copy from DEVICES -> [YOUR_DEVICE] -> 'Device Access Token:'
"""


class Mouse:
    def __init__(self):
        self.speed = 20
        self.velocity = Vector2D(0, 0)

    def move(self):
        current_position = pyautogui.position()
        new_position = (current_position[0] + self.velocity.x, current_position[1] + self.velocity.y)
        pyautogui.moveTo(*new_position)


class MouseController:
    def __init__(self, smart_dash: SmartDash):
        self.joystick = Joystick()
        self.mouse_sensitivity = 100
        self.running = True
        self.smart_dash = smart_dash
        self.deadzone = 0.1
        self.mouse = Mouse()

    def update(self):
        force = self.joystick.data.force
        angle_rad = self.joystick.data.angle.radian

        if force > self.deadzone:
            dx = force * math.cos(angle_rad)
            dy = force * math.sin(angle_rad)

            self.mouse.velocity.x = dx * self.mouse.speed
            self.mouse.velocity.y = -dy * self.mouse.speed
        else:
            self.mouse.velocity.x = 0
            self.mouse.velocity.y = 0

        self.mouse.move()

    async def run(self):
        @self.smart_dash.on_data("V1")
        async def handle_joystick_data(data):
            try:
                self.joystick.update(data)
            except Exception as e:
                print(f"An error occurred while processing joystick data: {e}")
        
        @self.smart_dash.on_data("V2")
        async def set_mouse_senitivity(val):
            self.mouse.speed = val

        @self.smart_dash.on_data("V3")
        async def set_mouse_click(val):
            if val == 0:
                pyautogui.click()
            elif val == 1:
                pyautogui.rightClick()

        await self.smart_dash.connect()
        while self.running:
            self.update()
            await asyncio.sleep(0)

        await self.smart_dash.disconnect()


async def main():
    TOKEN = 'YOUR_TOKEN'
    smart_dash = SmartDash(token=TOKEN)
    game = MouseController(smart_dash)

    await asyncio.gather(
        smart_dash.start(),
        game.run()
    )

if __name__ == "__main__":
    asyncio.run(main())
