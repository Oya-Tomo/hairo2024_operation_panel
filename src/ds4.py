from enum import IntEnum


class DS4Stick(IntEnum):
    LEFT_X = 0
    LEFT_Y = 1
    LEFT_P2 = 2

    RIGHT_X = 3
    RIGHT_Y = 4
    RIGHT_P2 = 5


class DS4Button(IntEnum):
    CROSS = 0
    CIRCLE = 1
    TRIANGLE = 2
    RECT = 3

    L1 = 4
    R1 = 5
    L2 = 6
    R2 = 7

    SHARE = 8
    OPTIONS = 9

    PS = 10

    L_ST_CLICK = 11
    R_ST_CLICK = 12

    HAT_UP = 13
    HAT_RIGHT = 14
    HAT_DOWN = 15
    HAT_LEFT = 16
