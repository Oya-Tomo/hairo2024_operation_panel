from dataclasses import dataclass


@dataclass
class SystemState:
    is_running: bool = False
    arm_lock: bool = False
    foot_lock: bool = False


@dataclass
class FooterState:
    left_speed: float = 0.0  # -1 ~ 1
    right_speed: float = 0.0  # -1 ~ 1

    left_front_flipper: float = 0.0  # 0 ~ 90
    left_back_flipper: float = 0.0
    right_front_flipper: float = 0.0
    right_back_flipper: float = 0.0


@dataclass
class ArmState:
    joint_base: float = 0.0
    joint_mid: float = 0.0
    joint_tip: float = 0.0


@dataclass
class CollectionState:
    speed: float = 0.0  # -1 ~ 1
    angle: float = 0.0  # 0 ~ 45
