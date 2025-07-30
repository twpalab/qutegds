"""
Components to mark or draw the chip boundaries.

.. module:: chip_layout.py
"""

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import ComponentSpec, LayerSpec

from qutegds.components.simple_strip import stripes_array
from qutegds.geometry import subtract


@gf.cell
def centered_chip(
    center_comp: ComponentSpec = stripes_array,
    size: tuple = (2e4, 2e4),
    layer: LayerSpec = (2, 0),
    negative: bool = False,
    **chip_kwargs,
) -> Component:
    """Return chip with centered component.

    Args:
        array (float): ComponentSpec: component to be centered
        size tuple(float, float): chip size
        layer (LayerSpec): chip layer
        negative (bool): return difference between component and chip as top layer.
    """
    c = gf.Component()
    top = c << gf.get_component(center_comp)
    chip = c << gf.components.rectangle(size=size, layer=layer, **chip_kwargs)
    c.align(elements="all", alignment="x")
    c.align(elements="all", alignment="y")
    if negative:
        _ = c << subtract(chip, top)
        c.remove([top])
    c.add_ports(chip.ports)
    return c


@gf.cell
def squares_at_corner_chip(
    center_comp: ComponentSpec = stripes_array,
    size: tuple = (2e4, 2e4),
    square_size: float = 500,
    layer: LayerSpec = (2, 0),
    l_corners=True,
    **chip_kwargs,
) -> Component:
    """Return chip marked by squares with centered component.

    Args:
        array (float): ComponentSpec: component to be centered
        size tuple(float, float): chip size
        square_size (float): length of the squares' sides
        layer (LayerSpec): chip layer
    """
    c = gf.Component()
    comp = c << gf.get_component(center_comp)
    square = gf.components.rectangle(
        size=(square_size, square_size), layer=layer, **chip_kwargs
    )
    square_upleft = c << square
    square_lowleft = c << square
    square_upright = c << square

    square_upleft.move(destination=(0, size[1] - square_size))
    square_lowleft.move(destination=(0, 0))
    square_upright.move(destination=(size[0] - square_size, size[1] - square_size))
    ycomp = comp.ymax - comp.ymin
    xcomp = comp.xmax - comp.xmin
    comp.movex(abs(comp.xmin) + (size[0] - xcomp) / 2)
    comp.movey(abs(comp.ymin) + (size[1] - ycomp) / 2)

    return c


@gf.cell
def square_L(width: float = 1, layer: LayerSpec = (1, 0)):
    """Return L shape enclosed by a square."""
    c = gf.Component()
    c.add_polygon(
        [
            (0, 0),
            (2 * width, 0),
            (2 * width, width),
            (width, width),
            (width, 2 * width),
            (0, 2 * width),
            (0, 0),
        ],
        layer=layer,
    )
    return c


@gf.cell
def chip_corners(
    chip_size: tuple = (2e4, 2e4),
    width: float = 50,
    layer: LayerSpec = (1, 0),
) -> Component:
    """Return chip corners markers."""
    c = gf.Component()
    corner = square_L(width=width, layer=layer)
    corner_upleft = c << corner
    corner_lowleft = c << corner
    corner_lowright = c << corner
    corner_upright = c << corner

    corner_lowleft.move(destination=(0, 0))
    corner_lowright.mirror_x()
    corner_lowright.move(destination=(chip_size[0] + 2 * width, 0))
    corner_upleft.mirror_y()
    corner_upleft.move(destination=(0, chip_size[1]))
    corner_upright.mirror_y()
    corner_upright.mirror_x()
    corner_upright.move(destination=(chip_size[0] + 2 * width, chip_size[1]))
    return c


@gf.cell
def chip_title(
    title: str = "TITLE",
    length: float = 12e3,
    width: float = 500,
    border_left: float = 30,
    border_top: float = 10,
    border_title: float = 100,
) -> Component:
    """Return rectangle strip with padded title.

    Args:
        title (str): title to be plotted
        length (float): length of the top bar
        width (float): width of the top bar
        border_left (float): fill left border of title
        border_top (float): fill top border of title
        border_title (float): space around title

    """
    c = Component()
    strip = gf.components.straight(length=length, width=width)
    text = gf.components.text(
        title,
        size=width - border_top - border_title,
        position=(border_left + border_title, -width / 2),
    )
    inv = gf.geometry.invert(text, border=border_title)
    c.add_ref(gf.geometry.boolean(strip, inv, "not"))
    c.add_ports(strip.ports)
    return c
