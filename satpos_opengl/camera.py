import math
import struct

import moderngl
from moderngl import Buffer, Context
from pyglm import glm


class UniformBuffer:
    def __init__(self):
        self.ctx: Context = moderngl.get_context()
        self.data = bytearray(1024)
        self.ubo: Buffer = self.ctx.buffer(self.data)

    def set_camera(self, pos: glm.vec3, target: glm.vec3, aspect_ratio: float = 1):
        # Проекция
        proj = glm.perspective(45.0, aspect_ratio, 0.001, 135.0)
        # Матрица вида
        camera = proj * glm.lookAt(pos, target, (0.0, 1.0, 0.0))
        # Записываем матрицу (4x4 float = 64 байта)
        self.data[0:64] = camera.to_bytes()
        self.data[80:92] = pos.to_bytes()

    def set_light_pos(self, x, y, z):
        self.data[64:80] = struct.pack('4f', x, y, z, 0.0)

    def use(self):
        self.ubo.write(self.data)
        self.ubo.bind_to_uniform_block()


class Camera:
    def __init__(self) -> None:
        self.uniform_buffer = UniformBuffer()
        self.cam_pos = glm.vec3(0.0, 0.0, 5.0)
        self.cam_target = glm.vec3(0.0, 0.0, 0.0)
        self.cam_yaw = 0.0
        self.cam_pitch = 0.0
        self.aspect_radio = 1.0
        self.is_rotating = False
        self.is_flying = False
        self.keys_pressed = set()
        # Настройки полета
        self.move_speed = 0.1
        self.look_sensitivity = 0.2
        self.orbit_distance = 2.01
        self.wheel_delta = 0.1


    def render(self, target_pos: glm.vec3 | None = None):
        if target_pos is not None:
            self.cam_target = target_pos

        if target_pos is not None:
            radius = self.orbit_distance
            rad_y = math.radians(self.cam_pitch)
            rad_x = math.radians(self.cam_yaw)

            # Смещение камеры относительно цели
            offset = glm.vec3(
                radius * math.cos(rad_y) * math.sin(rad_x),
                radius * math.sin(rad_y),
                radius * math.cos(rad_y) * math.cos(rad_x)
            )
            self.cam_pos = target_pos + offset
            self.cam_target = target_pos

        self.uniform_buffer.set_camera(self.cam_pos, self.cam_target, self.aspect_radio)
        self.uniform_buffer.set_light_pos(10.0, 0, 10.0)
        self.uniform_buffer.use()

    def resizeGL(self, w, h):
        self.aspect_radio = w / h

    def on_mouse_move(self, x, y):
        if self.is_rotating:
            # Вращение вокруг центра (0,0,0) - режим Blender
            sensitivity = 0.2
            self.cam_yaw -= x * sensitivity
            self.cam_pitch += y * sensitivity

            # Ограничиваем Pitch, чтобы не перевернуться
            self.cam_pitch = max(-89.0, min(89.0, self.cam_pitch))

            # Обновляем позицию камеры на сфере (Orbit)
            radius = glm.length(self.cam_pos) # Радиус орбиты
            rad_y = math.radians(self.cam_pitch)
            rad_x = math.radians(self.cam_yaw)

            self.cam_pos.x = radius * math.cos(rad_y) * math.sin(rad_x)
            self.cam_pos.y = radius * math.sin(rad_y)
            self.cam_pos.z = radius * math.cos(rad_y) * math.cos(rad_x)


        elif self.is_flying:
            # В режиме полета мышь вращает только направление взгляда
            sensitivity = 0.1
            self.cam_yaw += x * sensitivity
            self.cam_pitch += y * sensitivity
            self.cam_pitch = max(-89.0, min(89.0, self.cam_pitch))

            # При полете цель - это точка перед камерой
            rad_y = math.radians(self.cam_pitch)
            rad_x = math.radians(self.cam_yaw)
            fwd = glm.vec3(
                math.sin(rad_x) * math.cos(rad_y),
                math.sin(rad_y),
                math.cos(rad_x) * math.cos(rad_y)
            )
            self.cam_target = self.cam_pos + glm.normalize(fwd)

    def on_wheel(self, delta: int):
        # if self.cam_target != glm.vec3(0.0, 0.0, 0.0):
        if delta < 0:
            if self.orbit_distance - self.wheel_delta < 0.001:
                return
            self.orbit_distance -= self.wheel_delta
        else:
            self.orbit_distance += self.wheel_delta
        if self.is_rotating:
            # В режиме орбиты меняем радиус (расстояние до центра)
            # Для упрощения: просто двигаем камеру по вектору к центру
            direction = glm.normalize(self.cam_pos - self.cam_target)
            if delta < 0: # Wheel Up -> Zoom In
                self.cam_pos -= direction * self.wheel_delta
            else: # Wheel Down -> Zoom Out
                self.cam_pos += direction * self.wheel_delta
        else:
            # В свободном полете просто двигаем вперед/назад
            rad_y = math.radians(self.cam_pitch)
            rad_x = math.radians(self.cam_yaw)
            fwd = glm.vec3(math.sin(rad_x)*math.cos(rad_y),
                           math.sin(rad_y),
                           math.cos(rad_x)*math.cos(rad_y))
            self.cam_pos += fwd * (delta * 0.001)

    def toggle_fly_mode(self):
        self.is_flying = not self.is_flying
        print(f"Free Cam: {self.is_flying}")

    def handle_fly_movement(self):
        """ Логика управления WASD в свободном полете """
        # forward = glm.vec3(0, 0, -1)
        # Упрощенно: движение относительно взгляда камеры
        # Для полноценного полета нужно учитывать yaw/pitch камеры
        # Здесь реализуем базовый WASD
        # direction = glm.vec3(0, 0, 0)

        # Рассчитываем вектор направления взгляда
        rad_y = math.radians(self.cam_pitch)
        rad_x = math.radians(self.cam_yaw)

        # Вектор направления взгляда (Forward vector)
        fwd = glm.vec3(
            math.sin(rad_x) * math.cos(rad_y),
            math.sin(rad_y),
            math.cos(rad_x) * math.cos(rad_y)
        )
        fwd = glm.normalize(fwd)

        right = glm.normalize(glm.cross(fwd, glm.vec3(0, 1, 0)))

        if 'W' in self.keys_pressed: self.cam_pos += fwd * self.move_speed
        if 'S' in self.keys_pressed: self.cam_pos -= fwd * self.move_speed
        if 'A' in self.keys_pressed: self.cam_pos -= right * self.move_speed
        if 'D' in self.keys_pressed: self.cam_pos += right * self.move_speed
        if 'Q' in self.keys_pressed: self.cam_pos += glm.vec3(0, 1, 0) * self.move_speed # Вверх
        if 'E' in self.keys_pressed: self.cam_pos -= glm.vec3(0, 1, 0) * self.move_speed # Вниз

    def on_key_pressed(self, key: str):
        self.keys_pressed.add(key)
        print(self.keys_pressed)
        if key == 'ESCAPE': # Выход из полета/сброс
            self.is_flying = False

    def on_key_release(self, key: str):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
