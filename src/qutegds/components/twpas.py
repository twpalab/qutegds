"""Draw cells of kinetic inductance twpas."""

from functools import partial

import gdsfactory as gf
from gdsfactory import Component


@gf.cell
def fingers_cell(
    width: float = 1, line_length: float = 5, finger_length: float = 20, **kwargs
) -> Component:
    """Return base cell of transmission line with fingers."""
    c = Component()
    w2 = width / 2
    st_fn = partial(gf.components.straight, width=width, **kwargs)
    line = c << st_fn(length=line_length)
    finger_top = c << st_fn(length=finger_length - w2)
    finger_bot = c << st_fn(length=finger_length - w2)
    finger_top.rotate(-90)
    finger_top.move(origin=finger_top.ports["o1"], destination=(line_length / 2, -w2))
    finger_bot.rotate(90)
    finger_bot.move(origin=finger_bot.ports["o1"], destination=(line_length / 2, w2))
    c.add_ports(line.ports)
    c.info.update({"length": line.info["length"]})
    return c
