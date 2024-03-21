"""resonator module."""

import gdsfactory as gf
import numpy as np
from gdsfactory import Component
from gdsfactory.routing.manhattan import round_corners
from gdsfactory.typings import ComponentSpec, CrossSectionSpec, LayerSpec

from qutegds import cpw
from qutegds.geometry import subtract


@gf.cell()
def resonator(
    length: float = 400.0,
    L0: float = 30.0,
    n: int = 1,
    bend: ComponentSpec = "bend_euler",
    cross_section: CrossSectionSpec = "xs_sc",
    width: float = 2,
    r: float = 10,
    dy: float = 15,
    dx: float = 40,
    dc: float = 5,
) -> Component:
    """Generate a circle geometry.

    Args:
        radius: of the circle.
        angle_resolution: number of degrees per point.
        layer: layer.
    """
    epsilon = 0
    bend90 = gf.get_component(
        bend,
        cross_section=cross_section,
        width=width,
        with_arc_floorplan=True,
        radius=r,
    )
    curve = bend90.info[
        "length"
    ]  # sligthly different from a "perfect circle"(p=0) because p=0.5 by default
    lc = dx - r + curve + dc  # coupling termination
    DL = (length + L0 + 4 * n * (2 * r - curve - dy) - lc) / (2 * n + 1)
    L2 = DL - L0
    print("DL = " + str(DL))
    if L2 < 0:
        raise ValueError(
            """Snake is too short: either reduce L0, reduce dy, increase
            the total length, or decrease n \n
                 | L0 |      L2      |

                      ->-------------|
                                     |
                                     | 2 * dy
                 |-------------------|
                 |                        ^
         2  * dy |                        | dc
                 |------------------------|

                 |         DL        | dx |"""
        )

    y = 0
    path = [(0, y), (L2, y)]
    for _ in range(n):
        y -= 2 * dy + epsilon
        path += [(L2, y), (-L0, y)]
        y -= 2 * dy + epsilon
        path += [(-L0, y), (L2, y)]

    path += [(L2 + dx, y), (L2 + dx, y + r + dc)]
    path = [(round(_x, 3), round(_y, 3)) for _x, _y in path]

    c = gf.Component()
    route = round_corners(
        points=path, bend=bend90, cross_section=cross_section, width=width
    )

    c.add(route.references)
    c.add_port("o1", port=route.ports[0])
    c.add_port("o2", port=route.ports[1])
    return c


@gf.cell()
def termination_close(
    width: float = 10,
    angle_resolution: float = 0.5,
    gap: float = 5,
    layer: LayerSpec = "WG",
) -> Component:
    """Generate a close termination for a cpw.

    Args:
        width: of the terminated cpw.
        angle_resolution: number of degrees per point.
        gap: of the terminated cpw.
        layer: layer.
    """
    if width <= 0:
        raise ValueError(f"radius={width} must be > 0")
    c = Component()
    c1 = Component()
    c2 = Component()
    t = np.linspace(0, 180, int(360 / angle_resolution) + 1) * np.pi / 180
    xpts = (width / 2 * np.cos(t)).tolist()
    ypts = (width / 2 * np.sin(t)).tolist()
    xpts2 = ((width / 2 + gap) * np.cos(t)).tolist()
    ypts2 = ((width / 2 + gap) * np.sin(t)).tolist()

    c1.add_polygon(points=(xpts, ypts), layer=layer)
    c2.add_polygon(points=(xpts2, ypts2), layer=layer)
    _ = c << subtract(c2, c1)
    c.add_port(
        name="o1",
        center=[0, 0],
        width=1,
        orientation=270,
        port_type="optical",
        cross_section="xs_sc",
    )
    return c


@gf.cell()
def termination_open(
    width: float = 10,
    angle_resolution: float = 0.5,
    gap: float = 5,
    layer: LayerSpec = "WG",
) -> Component:
    """Generate a circle geometry.

    Args:
        width: of the terminated cpw.
        angle_resolution: number of degrees per point.
        gap: of the terminated cpw.
        layer: layer.
    """
    if width <= 0:
        raise ValueError(f"width={width} must be > 0")
    c = Component()
    t = np.linspace(0, 180, int(360 / angle_resolution) + 1) * np.pi / 180
    xpts = (-width / 2 - gap / 2 + gap / 2 * np.cos(t)).tolist()
    ypts = (gap / 2 * np.sin(t)).tolist()
    p = c.add_polygon(points=(xpts, ypts), layer=layer)
    c.add_polygon(points=(xpts, ypts), layer=layer)
    p.mirror()
    c.add_port(
        name="o1",
        center=[0, 0],
        width=1,
        orientation=270,
        port_type="optical",
        cross_section="xs_sc",
    )
    c.show()
    return c


@gf.cell()
def resonator_cpw(
    width: float = 2, gap: float = 1, lambda_4: bool = True, **resonator_kwargs
) -> Component:
    """Generate a circle geometry.

    Args:
        radius: of the circle.
        angle_resolution: number of degrees per point.
        layer: layer.
    """
    c = Component()
    cpw_comp = c << cpw("resonator", gap=gap, width=width, **resonator_kwargs)
    t1 = c << termination_close(radius=width / 2, gap=gap)
    t2 = c << termination_open(radius=width / 2, gap=gap)
    t1.connect("o1", cpw_comp.ports["o1"])
    t2.connect("o1", cpw_comp.ports["o2"])
    c.add_ports(cpw_comp.ports)
    return c
