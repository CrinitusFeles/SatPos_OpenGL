import moderngl

from satpos_opengl.texture_material import ImageTexture, TextureMaterial
from satpos_opengl.utils import load_shader


class EarthMaterial(TextureMaterial):
    def __init__(self, paths: dict):
        self.textures = {
            'day_texture': ImageTexture(paths['day']),
            'night_texture': ImageTexture(paths['night']),
            'cloud_texture': ImageTexture(paths['clouds']),
            'normal_map': ImageTexture(paths['normal']),
            'specular_map': ImageTexture(paths['specular']),
        }
        self.ctx = moderngl.get_context()
        self.program = self.ctx.program(
            load_shader('vertex.glsl'),
            load_shader('earth_fragment.glsl')
        )

    def use(self):
        # Активируем все текстуры на разных юнитах
        for i, (name, tex_obj) in enumerate(self.textures.items()):
            tex_obj.sampler.use(i)
            self.program[name] = i
