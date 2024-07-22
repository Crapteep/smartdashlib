import pygame
import asyncio
import math
import random
from smartdashlib import SmartDash
from utils.joystick import Joystick, Vector2D


"""
Simple game controlled by SmartDash app


For this example, you need to create 3 virtual pins:
1. V1 - for the joystick
2. V3 - for reset button points(min: 0, max: 1, value: 0)
3. V2 - for a label displaying points (min: 0, max: 500, value: 70)

Additionally, you need to add 3 elements to your dashboard and connect them to the corresponding pins:
1. Label (V2)
2. Button (V3)
3. Joystick (V1)

You also need to add your token, which you can copy from DEVICES -> [YOUR_DEVICE] -> 'Device Access Token:'
"""

class Player:
    def __init__(self, x, y):
        self.position = Vector2D(x, y)
        self.speed = 5
        self.velocity = Vector2D(0, 0)
        self.size = 50

    def move(self):
        self.position.x += self.velocity.x
        self.position.y += self.velocity.y

class Item:
    def __init__(self, x, y):
        self.position = Vector2D(x, y)
        self.size = 20

class Game:
    def __init__(self, smart_dash: SmartDash):
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("DEMO Game")
        self.clock = pygame.time.Clock()
        self.player = Player(self.width // 2, self.height // 2)
        self.joystick = Joystick()
        self.running = True
        self.smart_dash = smart_dash
        self.debug_font = pygame.font.Font(None, 36)
        self.deadzone = 0.1
        self.items = []
        self.score = 0
        self.spawn_item()

    def spawn_item(self):
        x = random.randint(0, self.width)
        y = random.randint(0, self.height)
        self.items.append(Item(x, y))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset_score()

    def update(self):
        force = self.joystick.data.force
        angle_rad = self.joystick.data.angle.radian
        
        if force > self.deadzone:
            dx = force * math.cos(angle_rad)
            dy = force * math.sin(angle_rad)
            
            self.player.velocity.x = dx * self.player.speed
            self.player.velocity.y = -dy * self.player.speed
        else:
            self.player.velocity.x = 0
            self.player.velocity.y = 0

        self.player.move()

        self.player.position.x = max(self.player.size//2, min(self.width - self.player.size//2, self.player.position.x))
        self.player.position.y = max(self.player.size//2, min(self.height - self.player.size//2, self.player.position.y))

        self.check_collisions()

    def check_collisions(self):
        for item in self.items[:]:
            if (self.player.position.x - item.position.x)**2 + (self.player.position.y - item.position.y)**2 < (self.player.size//2 + item.size//2)**2:
                self.items.remove(item)
                self.score += 1
                self.spawn_item()
                asyncio.create_task(self.send_score())

    async def send_score(self):
        await self.smart_dash.write("V2", self.score)

    def reset_score(self):
        self.score = 0
        asyncio.create_task(self.send_score())

    def draw(self):
        self.screen.fill((0, 0, 0))
        pygame.draw.rect(self.screen, (255, 0, 0), (int(self.player.position.x - self.player.size//2), int(self.player.position.y - self.player.size//2), self.player.size, self.player.size))
        
        for item in self.items:
            pygame.draw.circle(self.screen, (0, 255, 0), (int(item.position.x), int(item.position.y)), item.size//2)
        
        score_text = f"Score: {self.score}"
        score_surface = self.debug_font.render(score_text, True, (255, 255, 255))
        self.screen.blit(score_surface, (10, 10))
        
        pygame.display.flip()

    async def run(self):
        @self.smart_dash.on_data("V1")
        async def handle_joystick_data(data):
            try:
                self.joystick.update(data)
            except Exception as e:
                print(f"An error occurred while processing joystick data: {e}")

        @self.smart_dash.on_data("V3")
        async def reset_score_app(v):
            self.reset_score()
        await self.smart_dash.connect()

        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            await asyncio.sleep(0)

        pygame.quit()
        await self.smart_dash.disconnect()

async def main():

    TOKEN = 'YOUR TOKEN'
    smart_dash = SmartDash(token=TOKEN)
    game = Game(smart_dash)
    
    await asyncio.gather(
        smart_dash.start(),
        game.run()
    )

if __name__ == "__main__":
    asyncio.run(main())