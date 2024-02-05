"""Chip with straight stripes for DC characterization."""

import gdsfactory as gf
from gdsfactory import Component, logger


@gf.cell()
def strip_with_pads(
    length: float = 2e3,
    width: float = 2,
    min_pad_size: float = 500,
    min_pad_buffer: float = 100,
    annotate_squares: float = 0,
    **kwargs
) -> Component:
    """Return straight with square bonding pads and annotated number of squares.

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
        squares = c << gf.components.text(
            str(int(length / width)), size=annotate_squares
        )
        squares.move(destination=(0, min_pad_size + min_pad_buffer))
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
    _ = [c.add_ref(strip_with_pads(width=w, **kwargs)) for w in widths]
    c.distribute(
        elements="all",
        direction="y",
        spacing=spacing,
        separation=True,
    )
    c.align(elements="all", alignment="x")
    return c
