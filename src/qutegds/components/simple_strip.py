"""Chip with straigth stripes for DC characterization."""

import gdsfactory as gf
from gdsfactory import Component, logger
from gdsfactory.typings import ComponentSpec, LayerSpec


@gf.cell()
def strip_with_pads(
    length: float = 2e3,
    width: float = 2,
    min_pad_size: float = 500,
    min_pad_buffer: float = 100,
    annotate_squares: bool = True,
    **kwargs
) -> Component:
    """Return straigth with square bonding pads and annotated number of squares.

    Args:
        length (float): length of the central strip
        width (float): width of the central strip
        min_pad_size (float): minimum side length of the bonding pads
        min_pad_buffer (float): minimum additional width of the pads w.r.t the strip
        annotate_squares (bool): plot numer of squares in the central strip
    """
    if length % width != 0:
        logger.warning("Non integer number of squares")
    pad_y = max(min_pad_size, width + 2 * min_pad_buffer)
    c = gf.Component()
    strip = gf.components.straight(length=length, width=width, **kwargs)
    pad = gf.components.straight(length=min_pad_size, width=pad_y, **kwargs)
    st_ref = c << strip
    pad_left = c << pad
    pad_right = c << pad
    st_ref.connect("o1", pad_left.ports["o2"])
    pad_right.connect("o1", st_ref.ports["o2"])
    c.info["squares"] = length / width
    c.info["length"] = length + 2 * min_pad_size
    if annotate_squares:
        squares = c << gf.components.text(str(int(length / width)), size=min_pad_buffer)
        squares.move(destination=(0, min_pad_size))
    c.add_port(pad_left.ports["o1"])
    c.add_port(pad_right.ports["o2"])
    return c


@gf.cell()
def stripes_array(
    widths: float | list = 1, spacing: float = 2000, **kwargs
) -> Component:
    """Return array of evenly spaced stripes with pads.

    Args:
        widths (float | list): list of widths of the array stripes
        spacing (float): space between stripes
    """
    c = gf.Component()
    if not isinstance(widths, list):
        widths = [widths]
    [c.add_ref(strip_with_pads(width=w, **kwargs)) for w in widths]
    c.distribute(
        elements="all",
        direction="y",
        spacing=spacing,
        separation=True,
    )
    c.align(elements="all", alignment="x")
    return c


@gf.cell()
def centered_chip(
    array: ComponentSpec = stripes_array,
    size: tuple = (2e4, 2e4),
    layer: LayerSpec = (2, 0),
    **chip_kwargs
) -> Component:
    """Return chip with centered component.

    Args:
        array (float): ComponentSpec: component to be centered and arguments
        size tuple(float, float): chip size
        layer (LayerSpec): chip layer
    """
    c = gf.Component("on chip")
    _ = c << gf.get_component(array)
    _ = c << gf.components.rectangle(size=size, layer=layer, **chip_kwargs)
    c.distribute
    c.align(elements="all", alignment="x")
    c.align(elements="all", alignment="y")
    return c


@gf.cell()
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
    c = Component("demo title")
    strip = gf.components.straight(length=length, width=width)
    text = gf.components.text(
        title,
        size=width - border_top - border_title,
        position=(border_left + border_title, -width / 2),
    )
    inv = gf.geometry.invert(text, border=border_title)
    c.add_ref(gf.geometry.boolean(strip, inv, "not"))
    return c
