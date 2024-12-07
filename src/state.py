from dataclasses import dataclass
from struct import pack, unpack

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


def convert_to_list(
    system_state: SystemState,
    footer_state: FooterState,
    arm_state: ArmState,
    collection_state: CollectionState,
) -> list[float]:
    return [
        # SystemState
        system_state.is_running,
        # FooterState
        footer_state.left_speed,
        footer_state.right_speed,
        footer_state.left_front_flipper,
        footer_state.left_back_flipper,
        footer_state.right_front_flipper,
        footer_state.right_back_flipper,
        # ArmState
        arm_state.base_angle,
        arm_state.mid_angle,
        arm_state.tip_angle,
        arm_state.rotate,
        arm_state.gripper_speed,
        # CollectionState
        collection_state.speed,
        collection_state.angle,
    ]


def convert_from_list(
    data: list,
) -> tuple[
    SystemState,
    FooterState,
    ArmState,
    CollectionState,
]:
    return (
        SystemState(
            is_running=data[0],
        ),
        FooterState(
            left_speed=data[1],
            right_speed=data[2],
            left_front_flipper=data[3],
            left_back_flipper=data[4],
            right_front_flipper=data[5],
            right_back_flipper=data[6],
        ),
        ArmState(
            base_angle=data[7],
            mid_angle=data[8],
            tip_angle=data[9],
            rotate=data[10],
            gripper_speed=data[11],
        ),
        CollectionState(
            speed=data[12],
            angle=data[13],
        ),
    )


def pack_state(
    SystemState,
    FooterState,
    ArmState,
    CollectionState,
) -> bytes:
    return pack(
        "?fffffffffffff",
        *convert_to_list(
            SystemState,
            FooterState,
            ArmState,
            CollectionState,
        )
    )


def unpack_state(data: bytes) -> tuple[
    SystemState,
    FooterState,
    ArmState,
    CollectionState,
]:
    return convert_from_list(
        unpack(
            "?fffffffffffff",
            data,
        )
    )
