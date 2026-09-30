from satpos_opengl.materials.base import Material
from satpos_opengl.materials.texture import ImageTexture


class EarthMaterial(Material):
    def __init__(self, paths: dict):
        super().__init__('vertex.glsl', 'earth_fragment.glsl')
        self.textures = {
            'day_texture': ImageTexture(paths['day']),
            'night_texture': ImageTexture(paths['night']),
            'cloud_texture': ImageTexture(paths['clouds']),
            'normal_map': ImageTexture(paths['normal']),
            'specular_map': ImageTexture(paths['specular']),
        }

    def use(self):
        for i, (name, tex_obj) in enumerate(self.textures.items()):
            tex_obj.sampler.use(i)
            self.program[name] = i

    def vertex_array(self, buffer):
        return self.ctx.vertex_array(self.program, [(buffer, '3f 3f 2f', 'in_vertex', 'in_normal', 'in_uv')])