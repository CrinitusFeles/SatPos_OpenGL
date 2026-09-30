import moderngl

from satpos_opengl.utils import load_shader


class Material:
    def __init__(self, vertex_shader: str, fragment_shader: str,
                 geometry_shader: str | None = None):
        self.ctx = moderngl.get_context()
        self.program = self.ctx.program(
            load_shader(vertex_shader),
            load_shader(fragment_shader),
            load_shader(geometry_shader) if geometry_shader else None
        )

    def use(self):
        raise NotImplementedError

    def vertex_array(self, buffer):
        raise NotImplementedError
