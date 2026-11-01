"""The province's vegetation (2.W4 §a, 1.15 §e): the Black Marsh mods' forms, the region object lists, our placer."""


def render_layer(window, out=None, world=None):
    """Placements as points coloured by form class, for terrain/render.py (layer.py)."""
    from tools.argonia_world.vegetation.layer import render_layer as f
    return f(window, out=out, world=world)
