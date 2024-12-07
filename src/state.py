from dataclasses import dataclass

# Shared with Master


@dataclass
class SystemState:
    is_running: bool = False


@dataclass
class FooterState:
    left_speed: float = 0.0  # -1 ~ 1
    right_speed: float = 0.0  # -1 ~ 1

    left_front_flipper: float = 0.0  # 0.0 ~ PI/2
    left_back_flipper: float = 0.0
    right_front_flipper: float = 0.0
    right_back_flipper: float = 0.0


@dataclass
class ArmState:
    base_angle: float = 0.0
    mid_angle: float = 0.0
    tip_angle: float = 0.0
    rotate: float = 0.0  # -PI ~ PI
    gripper_speed: float = 0.0  # -1 ~ 1


@dataclass
class CollectionState:
    speed: float = 0.0  # -1 ~ 1
    angle: float = 0.0  # 0 ~ 45
