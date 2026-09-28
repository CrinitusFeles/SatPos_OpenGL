import moderngl

from satpos_opengl.utils import load_shader


class ColorMaterial:
    def __init__(self):
        self.ctx = moderngl.get_context()
        self.program = self.ctx.program(
            load_shader('vertex.glsl'),
            load_shader('color_fragment.glsl')
        )
        self.color = (1.0, 1.0, 1.0)
        self.ambient = (1.0, 1.0, 1.0)
        self.diffuse = (1.0, 1.0, 1.0)
        self.specular = (1.0, 1.0, 1.0)
        self.shininess = 32.0

    def use(self):
        # self.program['material.ambient'] = self.ambient
        # self.program['material.diffuse'] = self.diffuse
        # self.program['material.specular'] = self.specular
        # self.program['material.shininess'] = self.shininess
        # self.program['lightColor'] = (1.0, 1.0, 1.0)
        self.program['color'] = self.color

    def vertex_array(self, buffer):
        return self.ctx.vertex_array(self.program, [(buffer, '3f 3f 8x', 'in_vertex', 'in_normal')])
