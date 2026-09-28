from pathlib import Path

import moderngl
import OpenGL.GL as gl
from moderngl import Buffer, Context, VertexArray
from objloader import Obj
from pyglm import glm

from satpos_opengl.color_material import ColorMaterial
from satpos_opengl.texture_material import TextureMaterial


def flatten_comp(matrix):
    return [item for row in matrix for item in row]

def calc_transform(position, scale, rotation):
    transform_matrix = glm.mat4(1.0)
    transform_matrix = glm.translate(transform_matrix, glm.vec3(position))
    transform_matrix = transform_matrix * rotation
    transform_matrix = glm.scale(transform_matrix, glm.vec3(scale))
    return flatten_comp(transform_matrix.to_tuple())


class ModelGeometry:
    def __init__(self, path: Path) -> None:
        self.ctx: Context = moderngl.get_context()

        obj: Obj = Obj.open(path)
        self.vbo: Buffer = self.ctx.buffer(obj.pack('vx vy vz nx ny nz tx ty'))


class Mesh:
    def __init__(self, material, obj_path: Path,
                 picking_color: tuple = (1.0, 1.0, 1.0)) -> None:
        self.ctx: Context = moderngl.get_context()
        self.geometry: ModelGeometry = ModelGeometry(obj_path)
        self.vao: VertexArray = material.vertex_array(self.geometry.vbo)
        self.material: ColorMaterial | TextureMaterial = material
        self.picking_material = ColorMaterial()
        self.picking_vao = self.picking_material.vertex_array(self.geometry.vbo)

        self.picking_color = picking_color
        self._pos = 0
        self._scale= 0
        self.is_highlighted = False

        self.rotation_quat: glm.quat = glm.quat(0, 0, 0, 0)
        self.angular_velocity: glm.vec3 = glm.vec3(0, 0, 0)
        self.rotation_matrix: glm.mat4x4 = glm.mat4(1.0)

    def render(self, position, scale, wire: bool = True):
        self.material.use()
        self._pos = position
        self._scale = scale
        if wire:
            self.ctx.wireframe = True
        else:
            self.ctx.wireframe = False
        if self.is_highlighted:
            gl.glEnable(gl.GL_STENCIL_TEST)
            gl.glStencilFunc(gl.GL_ALWAYS, 1, 0xFF)
            gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_REPLACE)

        self.vao.program['transform'] = calc_transform(position, scale,
                                                       self.rotation_matrix)
        self.vao.render()
        # if self.is_highlighted:
        #     self.draw_outline(position, scale)
        gl.glDisable(gl.GL_STENCIL_TEST)

    def draw_outline(self, position, scale):
        self.picking_material.use()
        self.picking_material.color = (1.0, 0.5, 0.0)
        self.picking_vao.program['transform'] = calc_transform(position, scale * 1.02,
                                                       self.rotation_matrix)
        gl.glDisable(gl.GL_DEPTH_TEST)
        # self.ctx.disable(self.ctx.DEPTH_TEST)
        gl.glEnable(gl.GL_STENCIL_TEST)
        gl.glStencilFunc(gl.GL_NOTEQUAL, 1, 0xFF)
        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_KEEP)
        self.picking_vao.render()
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_STENCIL_TEST)

    def draw_id_only(self):
        self.picking_material.use()
        self.picking_material.color = self.picking_color
        self.picking_vao.program['transform'] = calc_transform(self._pos, self._scale,
                                                       self.rotation_matrix)
        self.picking_vao.render()

    def update_rotation(self, dt: float):
        euler_delta: glm.vec3 = glm.vec3(self.angular_velocity.x,
                                         self.angular_velocity.y,
                                         self.angular_velocity.z) * dt
        if glm.length(euler_delta) > 0:
            delta:glm.quat = glm.angleAxis(glm.length(euler_delta),
                                           glm.normalize(euler_delta))
            self.rotation_quat = delta * self.rotation_quat
            self.rotation_quat = glm.normalize(self.rotation_quat)
        self.rotation_matrix = glm.mat4_cast(self.rotation_quat)
