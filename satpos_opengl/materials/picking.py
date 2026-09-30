from satpos_opengl.materials.base import Material


class PickingMaterial(Material):
    def __init__(self):
        super().__init__('vertex.glsl', 'picking_fragment.glsl')
        self.color = (1.0, 1.0, 1.0)

    def use(self):
        self.program['color'] = self.color

    def vertex_array(self, buffer):
        return self.ctx.vertex_array(self.program, [(buffer, '3f 12x 8x', 'in_vertex')])
