"""
Chip with straight stripes for DC characterization.

.. module:: simple_strip.py
"""

import math

import gdsfactory as gf
from gdsfactory import Component, logger
from gdsfactory.typings import ComponentSpec, LayerSpec


@gf.cell
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

    .. jupyter-execute::

        from qutegds import strip_with_pads
        c = strip_with_pads()
        c.plot()
    """
    if length % width != 0:
        logger.warning("Non integer number of squares")
    pad_y = min_pad_size  # max(min_pad_size, width + 2 * min_pad_buffer)
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


@gf.cell
def stripes_array(
    stripes: ComponentSpec = "strip_with_pads",
    target: str = "width",
    values: float | list = 1,
    spacing: float = 2000,
    centered: bool = True,
    **kwargs
) -> Component:
    """Return array of evenly spaced stripes with pads.

    Args:
        widths (float | list): list of widths of the array stripes
        spacing (float): space between stripes
    """
    c = gf.Component()
    if not isinstance(values, list):
        values = [values]
    for value in values:
        kwargs.update({target: value, "component": stripes})
        c.add_ref(gf.get_component(**kwargs))
    c.distribute(
        elements="all",
        direction="y",
        spacing=spacing,
        separation=True,
    )
    if centered:
        c.align(elements="all", alignment="x")
    return c


@gf.cell
def meandering_u_sharp(
    length: float = 2e3,
    size: tuple[float, float] = (400, 100),
    width: float = 2,
    layer: LayerSpec = (1, 0),
) -> Component:
    """Return meandering U line with sharp turns.

    Args:
        length (float): Total length of the meandering line.
        size (tuple[float, float]): (max_length, height) of the U shape.
        width (float): Width of the line.
        layer (LayerSpec): Layer specification for the line.

    Returns:
        Component: A gdsfactory component containing the meandering U line.

    Raises:
        ValueError: If the provided parameters cannot generate a valid meandering line.
    """
    c = Component()
    max_length, height = size
    if 2 * max_length - height > length:
        raise ValueError("Line too short.")

    n_meanders = math.floor((length - height) / (2 * max_length))
    meander_length = (
        ((length - height) / 2 - max_length) / n_meanders if n_meanders > 0 else 0
    )

    if height + (n_meanders + 1) * 2 * meander_length > length:
        raise ValueError("Cannot generate line with provided parameters.")

    m_xmin, m_xmax = max_length - meander_length, max_length
    points = [(0.0, 0.0), (m_xmax, 0.0)]
    add_h = height / (2 * n_meanders + 1)

    for _ in range(1, n_meanders + 1):
        previous_h = points[-1][1]
        points.extend(
            [
                (m_xmax, previous_h + add_h),
                (m_xmin, previous_h + add_h),
                (m_xmin, previous_h + 2 * add_h),
                (m_xmax, previous_h + 2 * add_h),
            ]
        )
    points.extend([(m_xmax, height), (0.0, height)])

    P = gf.Path(points)
    _ = c << gf.path.extrude(P, width=width, layer=layer)
    return c


@gf.cell
def u_strip_with_pads(
    length: float = 3e3,
    u_length: float = 700,
    width: float = 2,
    min_pad_size: float = 200,
    min_pad_buffer: float = 100,
    annotate_squares: float = 0,
    **kwargs
) -> Component:
    """Return U-shaped strip with square bonding pads on the same side.

    Args:
        length (float): Total length of the meandering strip.
        width (float): Width of the central strip.
        min_pad_size (float): Minimum side length of the bonding pads.
        min_pad_buffer (float): Minimum additional width of the pads w.r.t the strip.
        u_size (tuple[float, float]): (max_length, height) of the U shape.
        annotate_squares (float): Size of text to plot number of squares in the central strip (0 for no annotation).
        layer (LayerSpec): Layer specification for the component.
        **kwargs: Additional keyword arguments.

    Returns:
        Component: A gdsfactory component containing the U-shaped strip with pads.
    """
    c = Component()
    pad_y = min_pad_size  # , width + 2 * min_pad_buffer)

    # Create meandering U strip
    strip = c << meandering_u_sharp(
        length=length, size=(u_length, pad_y + min_pad_buffer), width=width, **kwargs
    )

    # Create pads
    pad = gf.components.rectangle(size=(min_pad_size, pad_y))
    pad_top = c << pad
    pad_bot = c << pad

    pad_top.movey(pad_y + min_pad_buffer)
    strip.move(destination=(min_pad_size, min_pad_size / 2))

    # Add information
    c.info["squares"] = length / width
    c.info["length"] = length

    # Add annotation if requested
    if annotate_squares:
        squares = c << gf.components.text(
            str(int(length / width)), size=annotate_squares
        )
        squares.move(destination=(0, 2 * pad_y + 2 * min_pad_buffer))

    return c
