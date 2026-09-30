from pathlib import Path

import imageio
import moderngl
import numpy as np
from PIL import Image, ImageOps

from satpos_opengl.materials.base import Material

imageio.plugins.freeimage.download()

class ImageTexture:
    def __init__(self, path: Path):
        self.ctx = moderngl.get_context()
        if str(path).endswith('.hdr'):
            img = imageio.imread(str(path))
            if img.shape[2] == 3:
                rgba = np.zeros((img.shape[0], img.shape[1], 4), dtype=np.float32)
                rgba[:, :, :3] = img
                rgba[:, :, 3] = 1.0
                img_data = rgba
            else:
                img_data = img

            self.texture = self.ctx.texture(
                (img.shape[1], img.shape[0]),
                4,
                img_data.tobytes(),
                dtype='f4'
            )
        else:
            img = ImageOps.flip(Image.open(path).convert('RGBA'))
            self.texture = self.ctx.texture(img.size, 4, img.tobytes())
        self.sampler = self.ctx.sampler(texture=self.texture)

    def use(self):
        self.sampler.use()



class TextureMaterial(Material):
    def __init__(self, texture_path: Path):
        super().__init__('vertex.glsl', 'texture_fragment.glsl')
        self.texture = ImageTexture(texture_path)

    def use(self):
        self.texture.use()

    def vertex_array(self, buffer):
        return self.ctx.vertex_array(self.program, [(buffer, '3f 3f 2f', 'in_vertex', 'in_normal', 'in_uv')])

