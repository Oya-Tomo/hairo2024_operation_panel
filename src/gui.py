import sys
import math
import pygame
from enum import IntEnum

from src.ds4 import DS4Button, DS4Stick
from src import state
from src import arm
from src import connection
from src.arm import deg_to_rad, rad_to_deg
from src.utils import guard


class OpMode(IntEnum):
    Drive = 0
    Arm = 1
    Collect = 2

    def __str__(self) -> str:
        if self == OpMode.Drive:
            return "drive"
        elif self == OpMode.Arm:
            return "arm"
        elif self == OpMode.Collect:
            return "collect"
        else:
            return "unknown"

    def next_mode(self):
        if self == OpMode.Drive:
            return OpMode.Arm
        elif self == OpMode.Arm:
            return OpMode.Collect
        elif self == OpMode.Collect:
            return OpMode.Drive
        else:
            return OpMode.Drive


class OperationPanel:
    def __init__(self) -> None:
        # shared state

        self.system_state = state.SystemState(
            is_running=True,
        )

        self.footer_state = state.FooterState(
            left_speed=0.0,
            right_speed=0.0,
            left_front_flipper=0.0,
            left_back_flipper=0.0,
            right_front_flipper=0.0,
            right_back_flipper=0.0,
        )

        self.arm_state = state.ArmState(
            base_angle=math.pi / 4 * 3,
            mid_angle=math.pi / 4,
            tip_angle=0.0,
            rotate=0.0,
            gripper_speed=0.0,
        )

        self.col_state = state.CollectionState(
            speed=0.0,
            angle=0.0,
        )

        self.arm_ik = arm.ArmIK(
            tip=50,
            mid=100,
            base=100,
        )

        # internal state

        self.arm_x, self.arm_y = self.arm_ik.calculate_fk(
            self.arm_state.base_angle,
            self.arm_state.mid_angle,
            self.arm_state.tip_angle,
        )

        # gui state

        self.mode = OpMode.Drive

        self.screen: pygame.Surface = None
        self.events: list[pygame.event.Event] = []
        self.ctlr: pygame.joystick.JoystickType = None
        self.timer = pygame.time.Clock()

    def update_event_buf(self):
        self.events = pygame.event.get()

    def update_state(self):
        for event in self.events:
            if event.type == pygame.JOYBUTTONDOWN:
                if self.ctlr_get_button(DS4Button.PS):
                    # mode change
                    if self.mode == OpMode.Drive:
                        self.drive_mode_trans_prep()
                    elif self.mode == OpMode.Arm:
                        pass
                    elif self.mode == OpMode.Collect:
                        pass

                    self.mode = self.mode.next_mode()

        if self.mode == OpMode.Drive:
            self.drive_mode_update_state()
        elif self.mode == OpMode.Arm:
            self.arm_mode_update_state()
        elif self.mode == OpMode.Collect:
            self.collect_mode_update_state()
        else:
            pass

    def ctlr_get_axis(self, axis: int) -> float:
        value = self.ctlr.get_axis(axis)
        if -0.1 < value < 0.1:
            return 0
        else:
            return value

    def ctlr_get_button(self, btn: int) -> bool:
        hat = self.ctlr.get_hat(0)
        if btn == DS4Button.HAT_UP:
            return hat[1] == 1
        elif btn == DS4Button.HAT_RIGHT:
            return hat[0] == 1
        elif btn == DS4Button.HAT_DOWN:
            return hat[1] == -1
        elif btn == DS4Button.HAT_LEFT:
            return hat[0] == -1
        else:
            return self.ctlr.get_button(btn)

    # Mode : Drive
    def drive_mode_update_state(self):
        # footer
        self.footer_state.left_speed = -self.ctlr_get_axis(DS4Stick.LEFT_Y)
        self.footer_state.right_speed = -self.ctlr_get_axis(DS4Stick.RIGHT_Y)

        # flipper
        self.footer_state.left_front_flipper = guard(
            self.footer_state.left_front_flipper
            + (0.05 if self.ctlr_get_button(DS4Button.HAT_UP) else 0)
            - (0.05 if self.ctlr_get_button(DS4Button.HAT_LEFT) else 0),
            0.0,
            math.pi / 2,
        )

        self.footer_state.left_back_flipper = guard(
            self.footer_state.left_back_flipper
            + (0.05 if self.ctlr_get_button(DS4Button.HAT_RIGHT) else 0)
            - (0.05 if self.ctlr_get_button(DS4Button.HAT_DOWN) else 0),
            0.0,
            math.pi / 2,
        )

        self.footer_state.right_front_flipper = guard(
            self.footer_state.right_front_flipper
            + (0.05 if self.ctlr_get_button(DS4Button.TRIANGLE) else 0)
            - (0.05 if self.ctlr_get_button(DS4Button.CIRCLE) else 0),
            0.0,
            math.pi / 2,
        )

        self.footer_state.right_back_flipper = guard(
            self.footer_state.right_back_flipper
            + (0.05 if self.ctlr_get_button(DS4Button.RECT) else 0)
            - (0.05 if self.ctlr_get_button(DS4Button.CROSS) else 0),
            0.0,
            math.pi / 2,
        )

        # arm rotate
        self.arm_state.rotate = guard(
            self.arm_state.rotate
            + (0.05 if self.ctlr_get_button(DS4Button.L1) else 0)
            - (0.05 if self.ctlr_get_button(DS4Button.R1) else 0),
            -math.pi * 3 / 4,
            math.pi * 3 / 4,
        )

    def drive_mode_trans_prep(self):
        self.footer_state.left_speed = 0.0
        self.footer_state.right_speed = 0.0

    # Mode : Arm
    def arm_mode_update_state(self):
        # arm joints
        _arm_x = self.arm_x + self.ctlr_get_axis(DS4Stick.RIGHT_X) * 5
        _arm_y = self.arm_y - self.ctlr_get_axis(DS4Stick.RIGHT_Y) * 5
        _tip_angle = (
            self.arm_state.tip_angle + self.ctlr_get_axis(DS4Stick.LEFT_Y) * 0.1
        )

        angles = self.arm_ik.calculate_ik(
            _arm_x,
            _arm_y,
            _tip_angle,
        )
        if angles is not None:
            self.arm_state.base_angle = angles[0]
            self.arm_state.mid_angle = angles[1]
            self.arm_state.tip_angle = angles[2]
            self.arm_x = _arm_x
            self.arm_y = _arm_y

        # arm rotate
        self.arm_state.rotate = guard(
            self.arm_state.rotate
            + (0.05 if self.ctlr_get_button(DS4Button.L1) else 0)
            - (0.05 if self.ctlr_get_button(DS4Button.R1) else 0),
            -math.pi * 3 / 4,
            math.pi * 3 / 4,
        )

        # arm hand
        self.arm_state.gripper_speed = guard(
            0.0
            + (1.0 if self.ctlr_get_button(DS4Button.L2) else 0)
            - (1.0 if self.ctlr_get_button(DS4Button.R2) else 0),
            -1.0,
            1.0,
        )

    # Mode : Collect
    def collect_mode_update_state(self):
        # footer
        self.footer_state.left_speed = -self.ctlr_get_axis(DS4Stick.LEFT_Y)
        self.footer_state.right_speed = -self.ctlr_get_axis(DS4Stick.RIGHT_Y)

        self.col_state.angle = guard(
            self.col_state.angle
            + (0.05 if self.ctlr_get_button(DS4Button.L2) else 0)
            - (0.05 if self.ctlr_get_button(DS4Button.R2) else 0),
            0.0,
            math.pi / 4,
        )

        # arm rotate
        self.arm_state.rotate = guard(
            self.arm_state.rotate
            + (0.05 if self.ctlr_get_button(DS4Button.L1) else 0)
            - (0.05 if self.ctlr_get_button(DS4Button.R1) else 0),
            -math.pi * 3 / 4,
            math.pi * 3 / 4,
        )

    def update_screen(self):
        self.screen.fill((255, 255, 255))

        self.system_render()
        self.footer_render()
        self.arm_render()
        self.collect_render()

        pygame.display.update()

    def run(self):
        pygame.init()

        self.screen = pygame.display.set_mode((1000, 800))
        pygame.display.set_caption("Operation Panel")

        self.ctlr = pygame.joystick.Joystick(0)
        self.ctlr.init()

        while True:
            self.update_event_buf()
            self.update_state()
            self.update_screen()

            # print(self.mode)
            # print(self.footer_state)
            # print(self.arm_state)
            # print(self.col_state)

            for event in self.events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            connection.tcp_send(
                state.pack_state(
                    self.system_state,
                    self.footer_state,
                    self.arm_state,
                    self.col_state,
                )
            )

            self.timer.tick(20)

    def system_render(self):
        width = self.screen.get_width()
        height = 100

        surface = pygame.Surface((width, height))
        surface.fill((255, 255, 255))

        font = pygame.font.SysFont("notosanscjkjp", 36)

        text_mode = font.render(f"Mode: {self.mode}", True, (0, 0, 0))
        text_mode_rect = text_mode.get_rect()
        text_mode_rect.center = (width / 6, height / 2)
        surface.blit(text_mode, text_mode_rect)

        self.screen.blit(surface, (0, 0))

    def footer_render(self):
        width = self.screen.get_width() / 2
        height = self.screen.get_height() - 100

        surface = pygame.Surface((width, height))
        surface.fill((255, 255, 255))

        font = pygame.font.SysFont("notosanscjkjp", 36)

        # render title
        text_footer = font.render("footer", True, (0, 0, 0))
        text_footer_rect = text_footer.get_rect()
        text_footer_rect.topleft = (50, 50)
        surface.blit(text_footer, text_footer_rect)

        # render body

        rect_body = pygame.Rect(0, 0, 150, 200)
        rect_body.center = (width / 2, height / 2)
        pygame.draw.rect(surface, (200, 200, 150), rect_body)

        # render left caterpillars

        rect_left_front = pygame.Rect(0, 0, 50, 100)
        rect_left_front.bottomright = (rect_body.left - 5, rect_body.top - 5)
        pygame.draw.rect(surface, (50, 50, 50), rect_left_front, border_radius=5)

        rect_left_center = pygame.Rect(0, 0, 50, 200)
        rect_left_center.midright = (rect_body.left - 5, rect_body.centery)
        pygame.draw.rect(surface, (50, 50, 50), rect_left_center, border_radius=5)

        rect_left_back = pygame.Rect(0, 0, 50, 100)
        rect_left_back.topright = (rect_body.left - 5, rect_body.bottom + 5)
        pygame.draw.rect(surface, (50, 50, 50), rect_left_back, border_radius=5)

        # render right caterpillars

        rect_right_front = pygame.Rect(0, 0, 50, 100)
        rect_right_front.bottomleft = (rect_body.right + 5, rect_body.top - 5)
        pygame.draw.rect(surface, (50, 50, 50), rect_right_front, border_radius=5)

        rect_right_center = pygame.Rect(0, 0, 50, 200)
        rect_right_center.midleft = (rect_body.right + 5, rect_body.centery)
        pygame.draw.rect(surface, (50, 50, 50), rect_right_center, border_radius=5)

        rect_right_back = pygame.Rect(0, 0, 50, 100)
        rect_right_back.topleft = (rect_body.right + 5, rect_body.bottom + 5)
        pygame.draw.rect(surface, (50, 50, 50), rect_right_back, border_radius=5)

        # render flipper angles

        text_left_front = font.render(
            f"{rad_to_deg(self.footer_state.left_front_flipper):.0f}°", True, (0, 0, 0)
        )
        text_left_front_rect = text_left_front.get_rect()
        text_left_front_rect.center = (
            rect_left_front.centerx - 60,
            rect_left_front.centery,
        )
        surface.blit(text_left_front, text_left_front_rect)

        text_left_back = font.render(
            f"{rad_to_deg(self.footer_state.left_back_flipper):.0f}°", True, (0, 0, 0)
        )
        text_left_back_rect = text_left_back.get_rect()
        text_left_back_rect.center = (
            rect_left_back.centerx - 60,
            rect_left_back.centery,
        )
        surface.blit(text_left_back, text_left_back_rect)

        text_right_front = font.render(
            f"{rad_to_deg(self.footer_state.right_front_flipper):.0f}°", True, (0, 0, 0)
        )
        text_right_front_rect = text_right_front.get_rect()
        text_right_front_rect.center = (
            rect_right_front.centerx + 60,
            rect_right_front.centery,
        )
        surface.blit(text_right_front, text_right_front_rect)

        text_right_back = font.render(
            f"{rad_to_deg(self.footer_state.right_back_flipper):.0f}°", True, (0, 0, 0)
        )
        text_right_back_rect = text_right_back.get_rect()
        text_right_back_rect.center = (
            rect_right_back.centerx + 60,
            rect_right_back.centery,
        )
        surface.blit(text_right_back, text_right_back_rect)

        # render speed

        text_left_speed = font.render(
            f"{self.footer_state.left_speed:.2f}",
            True,
            (
                200 if self.footer_state.left_speed > 0.1 else 0,
                200 if self.footer_state.left_speed == 0 else 0,
                200 if self.footer_state.left_speed < -0.1 else 0,
            ),
        )
        text_left_speed_rect = text_left_speed.get_rect()
        text_left_speed_rect.center = (
            rect_left_center.centerx - 80,
            rect_left_center.centery,
        )
        surface.blit(text_left_speed, text_left_speed_rect)

        text_right_speed = font.render(
            f"{self.footer_state.right_speed:.2f}",
            True,
            (
                200 if self.footer_state.right_speed > 0.1 else 0,
                200 if self.footer_state.right_speed == 0 else 0,
                200 if self.footer_state.right_speed < -0.1 else 0,
            ),
        )
        text_right_speed_rect = text_right_speed.get_rect()
        text_right_speed_rect.center = (
            rect_right_center.centerx + 80,
            rect_right_center.centery,
        )
        surface.blit(text_right_speed, text_right_speed_rect)

        # render rotate

        text_rotate = font.render(
            f"{rad_to_deg(self.arm_state.rotate):.0f}°", True, (0, 0, 0)
        )
        text_rotate_rect = text_rotate.get_rect()
        text_rotate_rect.center = (rect_body.centerx, rect_body.centery + 70)
        surface.blit(text_rotate, text_rotate_rect)

        pygame.draw.line(
            surface,
            (50, 50, 50),
            (rect_body.centerx, rect_body.centery),
            (
                rect_body.centerx + 50 * math.cos(self.arm_state.rotate + math.pi / 2),
                rect_body.centery - 50 * math.sin(self.arm_state.rotate + math.pi / 2),
            ),
            width=10,
        )
        pygame.draw.circle(
            surface,
            (255, 255, 255),
            (rect_body.centerx, rect_body.centery),
            radius=10,
        )
        pygame.draw.circle(
            surface,
            (150, 150, 150),
            (
                rect_body.centerx + 50 * math.cos(self.arm_state.rotate + math.pi / 2),
                rect_body.centery - 50 * math.sin(self.arm_state.rotate + math.pi / 2),
            ),
            radius=10,
        )

        # push to screen
        self.screen.blit(surface, (0, 100))

    def arm_render(self):
        width = self.screen.get_width() / 2
        height = (self.screen.get_height() - 100) / 2

        surface = pygame.Surface((width, height))
        surface.fill((255, 255, 255))

        font = pygame.font.SysFont("notosanscjkjp", 36)

        # render title
        text_arm = font.render("footer", True, (0, 0, 0))
        text_arm_rect = text_arm.get_rect()
        text_arm_rect.topleft = (50, 50)
        surface.blit(text_arm, text_arm_rect)

        # render arm

        joint_point = [(0, -50), (0, -20)]
        joint_point.append(
            (
                joint_point[-1][0]
                + self.arm_ik.base * math.cos(self.arm_state.base_angle),
                joint_point[-1][1]
                + self.arm_ik.base * math.sin(self.arm_state.base_angle),
            )
        )
        joint_point.append(
            (
                joint_point[-1][0]
                + self.arm_ik.mid * math.cos(self.arm_state.mid_angle),
                joint_point[-1][1]
                + self.arm_ik.mid * math.sin(self.arm_state.mid_angle),
            )
        )
        joint_point.append(
            (
                joint_point[-1][0]
                + self.arm_ik.tip * math.cos(self.arm_state.tip_angle),
                joint_point[-1][1]
                + self.arm_ik.tip * math.sin(self.arm_state.tip_angle),
            )
        )

        for i in range(1, len(joint_point)):
            pygame.draw.line(
                surface,
                (50, 50, 50),
                (
                    joint_point[i - 1][0] + width * 0.3,
                    height - joint_point[i - 1][1] - 100,
                ),
                (
                    joint_point[i][0] + width * 0.3,
                    height - joint_point[i][1] - 100,
                ),
                15,
            )
            pygame.draw.circle(
                surface,
                (150, 150, 150),
                (
                    joint_point[i - 1][0] + width * 0.3,
                    height - joint_point[i - 1][1] - 100,
                ),
                radius=10,
            )
        upper_finger = (
            self.arm_state.tip_angle
            + math.pi / 8
            + math.pi / 8 * self.arm_state.gripper_speed
        )
        lower_finger = (
            self.arm_state.tip_angle
            - math.pi / 8
            - math.pi / 8 * self.arm_state.gripper_speed
        )
        pygame.draw.polygon(
            surface,
            (50, 50, 50),
            (
                (
                    joint_point[-1][0] + width * 0.3,
                    height - joint_point[-1][1] - 100,
                ),
                (
                    (joint_point[-1][0] + math.cos(upper_finger) * 40) + width * 0.3,
                    height - (joint_point[-1][1] + math.sin(upper_finger) * 40) - 100,
                ),
                (
                    (joint_point[-1][0] + math.cos(upper_finger + 90) * 20)
                    + width * 0.3,
                    height
                    - (joint_point[-1][1] + math.sin(upper_finger + 90) * 20)
                    - 100,
                ),
            ),
        )
        pygame.draw.polygon(
            surface,
            (50, 50, 50),
            (
                (
                    joint_point[-1][0] + width * 0.3,
                    height - joint_point[-1][1] - 100,
                ),
                (
                    (joint_point[-1][0] + math.cos(lower_finger) * 40) + width * 0.3,
                    height - (joint_point[-1][1] + math.sin(lower_finger) * 40) - 100,
                ),
                (
                    (joint_point[-1][0] + math.cos(lower_finger - 90) * 20)
                    + width * 0.3,
                    height
                    - (joint_point[-1][1] + math.sin(lower_finger - 90) * 20)
                    - 100,
                ),
            ),
        )
        pygame.draw.circle(
            surface,
            (150, 150, 150),
            (
                joint_point[-1][0] + width * 0.3,
                height - joint_point[-1][1] - 100,
            ),
            radius=10,
        )

        # push to screen
        self.screen.blit(surface, (self.screen.get_width() / 2, 100))

    def collect_render(self):
        width = self.screen.get_width() / 2
        height = (self.screen.get_height() - 100) / 2

        surface = pygame.Surface((width, height))
        surface.fill((255, 255, 255))

        font = pygame.font.SysFont("notosanscjkjp", 36)

        # render title
        text_col = font.render("collection", True, (0, 0, 0))
        text_col_rect = text_col.get_rect()
        text_col_rect.topleft = (50, 0)
        surface.blit(text_col, text_col_rect)

        # render gripper
        gripper_center = (
            width / 2,
            height / 3,
        )
        gripper_center_left = (
            width / 2 + 5,
            height / 3,
        )
        gripper_center_right = (
            width / 2 - 5,
            height / 3,
        )
        pygame.draw.polygon(
            surface,
            (50, 50, 50),
            [
                gripper_center_right,
                (
                    gripper_center_right[0]
                    + math.cos(self.col_state.angle + math.pi / 2) * 120,
                    gripper_center_right[1]
                    + math.sin(self.col_state.angle + math.pi / 2) * 120,
                ),
                (
                    gripper_center_right[0]
                    + math.cos(self.col_state.angle + math.pi) * 50,
                    gripper_center_right[1]
                    + math.sin(self.col_state.angle + math.pi) * 50,
                ),
            ],
        )
        pygame.draw.polygon(
            surface,
            (50, 50, 50),
            [
                gripper_center_left,
                (
                    gripper_center_left[0]
                    - math.cos(self.col_state.angle + math.pi / 2) * 120,
                    gripper_center_left[1]
                    + math.sin(self.col_state.angle + math.pi / 2) * 120,
                ),
                (
                    gripper_center_left[0]
                    - math.cos(self.col_state.angle + math.pi) * 50,
                    gripper_center_left[1]
                    + math.sin(self.col_state.angle + math.pi) * 50,
                ),
            ],
        )
        pygame.draw.circle(
            surface,
            (150, 150, 150),
            gripper_center,
            radius=20,
        )
        text_col_angle = font.render(
            f"{rad_to_deg(self.col_state.angle):.0f}°", True, (0, 0, 0)
        )
        text_col_angle_rect = text_col_angle.get_rect()
        text_col_angle_rect.center = (
            gripper_center[0],
            gripper_center[1] + 150,
        )
        surface.blit(text_col_angle, text_col_angle_rect)

        self.screen.blit(surface, (self.screen.get_width() / 2, 100 + height))
