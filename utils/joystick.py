from dataclasses import dataclass
import math


@dataclass
class Vector2D:
    x: float = 0.0
    y: float = 0.0


@dataclass
class Angle:
    radian: float = 0.0
    degree: float = 0.0


@dataclass
class Direction:
    x: str | None = None
    y: str | None = None
    angle: str | None = None


@dataclass
class JoystickData:
    position: Vector2D = Vector2D()
    force: float = 0.0
    pressure: float = 0.0
    distance: float = 0.0
    angle: Angle = Angle()
    direction: Direction = Direction()


class Joystick:
    def __init__(self) -> None:
        self.data = JoystickData()

    
    def update(self, data: dict) -> None:
        """Updates all states from received data"""
        self.data.position.x = data.get('position', {}).get('x', self.data.position.x)
        self.data.position.y = data.get('position', {}).get('y', self.data.position.y)
        self.data.force = data.get('force', self.data.force)
        self.data.pressure = data.get('pressure', self.data.pressure)
        self.data.distance = data.get('distance', self.data.distance)
        self.data.angle.radian = data.get('angle', {}).get('radian', self.data.angle.radian)
        self.data.angle.degree = data.get('angle', {}).get('degree', self.data.angle.degree)
        self.data.direction.x = data.get('direction', {}).get('x', self.data.direction.x)
        self.data.direction.y = data.get('direction', {}).get('y', self.data.direction.y)
        self.data.direction.angle = data.get('direction', {}).get('angle', self.data.direction.angle)


    def get_cartesian_control(self) -> Vector2D:
        """Returns control values based on x and y position."""
        return self.data.position
    
    def get_polar_control(self) -> tuple[float, float]:
        """Returns control values based on distance and angle."""
        return self.data.distance, self.data.angle.radian
    
    def get_force_based_control(self) -> float:
        """Returns control value based on force."""
        return self.data.force

    def get_angle_control(self) -> float:
        """Returns angle in degree."""
        return self.data.angle.degree
    
    def get_normalized_vector(self) -> Vector2D:
        """Returns normalized vector (x,y) based on joystick position"""
        magnitude = math.sqrt(self.data.position.x**2 + self.data.position.y**2)
        if magnitude == 0:
            return Vector2D(0,0)
        return Vector2D(self.data.position.x / magnitude, self.data.position.y / magnitude)