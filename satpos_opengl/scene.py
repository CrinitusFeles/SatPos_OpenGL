# import math
import struct
from pathlib import Path

import moderngl
import OpenGL.GL as gl
from moderngl import Context
from pyglm import glm
from PyQt6 import QtCore, QtGui, QtOpenGLWidgets, QtWidgets

from satpos_opengl.camera import Camera
from satpos_opengl.earth_material import EarthMaterial
from satpos_opengl.mesh import ColorMaterial, Mesh
from satpos_opengl.sat_path import calc_sat
from satpos_opengl.texture_material import TextureMaterial

assets_path = Path(__file__).parent / 'assets'
objects_path = Path(__file__).parent / 'objects'

class Scene:
    def __init__(self) -> None:
        self.ctx: Context = moderngl.get_context()
        self.camera = Camera()
        self.earth_texture = EarthMaterial({
            'day': assets_path / '8k_earth_daymap.jpg',
            'night': assets_path / '8k_earth_nightmap.jpg',
            'normal': assets_path / '8k_earth_normal_map.tif',
            'specular': assets_path / '8k_earth_specular_map.tif',
            'clouds': assets_path / '8k_earth_clouds.jpg',
        })
        self.sun_texture = TextureMaterial(assets_path / '8k_sun.jpg')
        self.space_texture = TextureMaterial(assets_path / 'HDR_galactic_plane_2.hdr')
        self.moon_texture = TextureMaterial(assets_path / 'moon_8k.tif')
        self.cubesat_material = ColorMaterial()

        self.earth = Mesh(self.earth_texture, objects_path / 'sphere.obj',
                          picking_color=(1.0, 0, 0))
        self.sun = Mesh(self.sun_texture, objects_path / 'sphere.obj',
                          picking_color=(0.0, 0, 0))
        self.space = Mesh(self.space_texture, objects_path / 'sphere.obj',
                          picking_color=(0, 0, 0))
        self.moon = Mesh(self.moon_texture, objects_path / 'sphere.obj',
                         picking_color=(0, 1.0, 0))
        self.cubesat = Mesh(self.cubesat_material, objects_path / 'griphon2.obj',
                            picking_color=(0, 0, 1.0))
        self.sphere = Mesh(self.cubesat_material, objects_path / 'sphere.obj',
                          picking_color=(1.0, 0, 1.0))
        self.cubesat.angular_velocity = (glm.vec3(-1, 0.2, 1))
        self.wire_mode = False
        self.time: float = 0
        self.picking_fbo = self.ctx.framebuffer(
            color_attachments=[self.ctx.texture(self.ctx.screen.size, 3)],
            depth_attachment=self.ctx.depth_renderbuffer(self.ctx.screen.size)
        )
        self.sat_path = calc_sat()
        self.i = 0

    def render(self, wire: bool = False):
        self.camera.render(glm.vec3(0, 0, 3))
        # self.camera.render(glm.vec3(self.sat_path[self.i]))

        self.space.render((0, 0, 0), 20, False)
        self.earth.render((0, 0, 0), 1, wire)
        self.sun.render((10, 0, 10), 0.5, wire)
        self.moon.render((15, 0, 0), 0.3, wire)
        # self.sphere.render((0, 0, 3), 1, wire)
        self.cubesat.render(self.sat_path[self.i], 0.01, wire)
        self.cubesat.update_rotation(1/60)
        if self.earth.is_highlighted:
            self.earth.draw_outline(self.earth._pos, self.earth._scale)
        elif self.moon.is_highlighted:
            self.moon.draw_outline(self.moon._pos, self.moon._scale)
        elif self.cubesat.is_highlighted:
            self.cubesat.draw_outline(self.cubesat._pos, self.cubesat._scale)

    def get_object_at(self, x, y) -> tuple[int, int, int]:
        self.picking_fbo.use()
        self.ctx.clear(0, 0, 0, 0)
        self.earth.draw_id_only()
        self.moon.draw_id_only()
        self.cubesat.draw_id_only()
        pixel = self.picking_fbo.read(viewport=(x, y, 1, 1), components=3)
        self.ctx.screen.use()
        return struct.unpack('>BBB', pixel)



class Canvas(QtOpenGLWidgets.QOpenGLWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timer = self.startTimer(int(1000/60))

        fmt = QtGui.QSurfaceFormat()
        fmt.setVersion(4, 1)
        fmt.setProfile(QtGui.QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setDepthBufferSize(24)
        fmt.setStencilBufferSize(8)
        self.grabKeyboard()
        QtGui.QSurfaceFormat.setDefaultFormat(fmt)

        self.last_mouse_pos = QtCore.QPoint()
        self.sh_wire = QtGui.QShortcut(QtGui.QKeySequence('Shift+Z'), self, self.toggle_wire_mode)
        self.wire_mode = False

    def toggle_wire_mode(self):
        self.wire_mode = not self.wire_mode

    def initializeGL(self) -> None:
        self.ctx = moderngl.create_context()
        self.ctx.clear()
        self.ctx.enable(self.ctx.DEPTH_TEST)
        self.scene = Scene()
        self.sh_fly = QtGui.QShortcut(QtGui.QKeySequence('F'), self, self.scene.camera.toggle_fly_mode)

    def resizeGL(self, w, h):
        super().resizeGL(w, h)
        self.ctx.viewport = (0, 0, w, h)
        self.scene.camera.resizeGL(w, h)
        self.scene.picking_fbo = self.scene.ctx.framebuffer(
            color_attachments=[self.scene.ctx.texture((w, h), 3)],
            depth_attachment=self.scene.ctx.depth_renderbuffer((w, h))
        )

    def paintGL(self):
        super().paintGL()
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT | gl.GL_STENCIL_BUFFER_BIT)  # type: ignore
        self.scene.render(self.wire_mode)

    def timerEvent(self, a0):
        self.scene.time += (1 / 60)
        self.scene.i += 1
        if self.scene.camera.is_flying:
            self.scene.camera.handle_fly_movement()
        self.update()

    # --- Обработка мыши ---

    def read_pixel_pos(self, pos: QtCore.QPoint):
        pixel_value: bytes = gl.glReadPixels(
            pos.x(),  # x-координата
            self.height() - pos.y() - 1,  # y-координата (в PyQt ось Y направлена вниз)
            1, 1,  # ширина и высота считываемого фрагмента
            gl.GL_RGB,  # формат (один компонент, например GL_RED)
            gl.GL_UNSIGNED_BYTE  # тип данных (unsigned byte)
        )  # type: ignore
        return struct.unpack('>BBB', pixel_value)

    def mousePressEvent(self, a0):
        super().mousePressEvent(a0)
        if not a0:
            return
        if a0.button() == QtCore.Qt.MouseButton.RightButton:
            self.scene.camera.is_rotating = True
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
        elif a0.button() == QtCore.Qt.MouseButton.LeftButton:
            # 1. Получаем координаты клика
            pos = a0.pos()
            self.makeCurrent()
            color = self.scene.get_object_at(pos.x(), self.height() - pos.y())
            self.doneCurrent()
            print(color)
            # 3. Определяем, какой это объект
            if color[0] > 0:
                self.scene.earth.is_highlighted = True
                self.scene.moon.is_highlighted = False
                self.scene.cubesat.is_highlighted = False
            elif color[1] > 0:
                self.scene.earth.is_highlighted = False
                self.scene.moon.is_highlighted = True
                self.scene.cubesat.is_highlighted = False
            elif color[2] > 0:
                self.scene.earth.is_highlighted = False
                self.scene.moon.is_highlighted = False
                self.scene.cubesat.is_highlighted = True
            else:
                self.scene.earth.is_highlighted = False
                self.scene.moon.is_highlighted = False
        self.last_mouse_pos = a0.pos()

    def mouseReleaseEvent(self, a0):
        super().mouseReleaseEvent(a0)
        if not a0:
            return
        if a0.button() == QtCore.Qt.MouseButton.RightButton:
            self.scene.camera.is_rotating = False
            self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)

    def mouseMoveEvent(self, a0):
        super().mouseMoveEvent(a0)
        if not a0:
            return
        delta = a0.pos() - self.last_mouse_pos
        self.last_mouse_pos = a0.pos()

        self.scene.camera.on_mouse_move(delta.x(), delta.y())

    def wheelEvent(self, a0):
        if not a0:
            return
        delta: int = -a0.angleDelta().y()
        self.scene.camera.on_wheel(delta)

    def keyPressEvent(self, a0):
        super().keyPressEvent(a0)
        if not a0:
            return
        self.scene.camera.on_key_pressed(a0.text().upper())

    def keyReleaseEvent(self, a0):
        super().keyReleaseEvent(a0)
        if not a0:
            return
        self.scene.camera.on_key_release(a0.text().upper())


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize(1000, 1000)
        self._canvas = Canvas(self)
        self.setCentralWidget(self._canvas)


if __name__ == '__main__':
    try:
        app = QtWidgets.QApplication([])
        main_window = MainWindow()
        main_window.show()
        app.exec()
    except KeyboardInterrupt:
        ...