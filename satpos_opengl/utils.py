from pathlib import Path


def load_shader(name: str, folder: Path = Path(__file__).parent / 'shaders'):
    with open(folder / name, 'r+', encoding='utf-8') as file:
        shader = file.read()
        return shader