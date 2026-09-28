import moderngl

from satpos_opengl.utils import load_shader


class PickingMaterial:
    def __init__(self):
        self.ctx = moderngl.get_context()
        self.program = self.ctx.program(
            load_shader('vertex.glsl'),
            load_shader('picking_fragment.glsl')
        )
        self.color = (1.0, 1.0, 1.0)

    def use(self):
        self.program['color'] = self.color

    def vertex_array(self, buffer):
        return self.ctx.vertex_array(self.program, [(buffer, '3f 12x 8x', 'in_vertex')])
