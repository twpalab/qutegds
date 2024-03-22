"""resonator module."""

from typing import Optional

import gdsfactory as gf
import numpy as np
from gdsfactory import Component
from gdsfactory.routing.manhattan import round_corners
from gdsfactory.typings import ComponentSpec, CrossSectionSpec, LayerSpec
from shapely.geometry.polygon import Polygon

from qutegds.components.cpw_base import cpw, cpw_with_ports


@gf.cell()
def resonator(
    length: float = 400.0,
    L0: float = 30.0,
    n: int = 1,
    bend: ComponentSpec = "bend_euler",
    cross_section: CrossSectionSpec = "xs_sc",
    width: float = 2,
    radius: float = 10,
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
        radius=radius,
    )

    if dy < 0:
        raise ValueError("dy must be > 0")
    if dy < radius:
        raise ValueError("dy must be > radius")

    curve = bend90.info[
        "length"
    ]  # sligthly different from a "perfect circle"(p=0) because p=0.5 by default
    lc = dx - radius + curve + dc  # coupling termination
    DL = (length + L0 + 4 * n * (2 * radius - curve - dy) - lc) / (2 * n + 1)
    L2 = DL - L0
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

    path += [(L2 + dx, y), (L2 + dx, y + radius + dc)]
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
    dt: float = 3,
    r: float = 4,
    layer: LayerSpec = "WG",
) -> Component:
    """Generate a close termination for a cpw.

    Args:
        width: of the terminated cpw.
        angle_resolution: number of degrees per point.
        gap: of the terminated cpw.
        dt: termination longitudinal extension.
        r: radius of the termination curvatures.
        layer: layer.
    """
    if width <= 0:
        raise ValueError(f"width={width} must be > 0")
    if r > (width / 2 + gap):
        raise ValueError(f"radius={r} must be < (width/2 + gap)")
    c = Component()
    t = np.linspace(0, 180, int(360 / angle_resolution) + 1) * np.pi / 180
    xpts = (width / 2 * np.cos(t)).tolist()
    ypts = (width / 2 * np.sin(t)).tolist()
    xpts2 = [-width / 2 - gap, -width / 2 - gap, width / 2 + gap, width / 2 + gap]
    ypts2 = [0, width / 2 + dt, width / 2 + dt, 0]
    t3 = np.linspace(0, 90, int(360 / angle_resolution) + 1) * np.pi / 180
    xpts3 = (width / 2 + gap - r + r * np.cos(t3)).tolist()
    ypts3 = (width / 2 + dt - r + r * np.sin(t3)).tolist()
    xpts3.append(width / 2 + gap)
    ypts3.append(width / 2 + dt)
    xpts4 = (-1 * np.array(xpts3)).tolist()
    c1 = Polygon(zip(xpts, ypts))
    c2 = Polygon(zip(xpts2, ypts2))
    c3 = Polygon(zip(xpts3, ypts3))
    c4 = Polygon(zip(xpts4, ypts3))
    c_diff = c2 - c1 - c3 - c4
    c.add_polygon(c_diff, layer=layer)
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
    return c


@gf.cell()
def resonator_cpw(
    width: float = 2.0, gap: float = 1.0, lambda_4: bool = True, **resonator_kwargs
) -> Component:
    """Generate a cpw resonator.

    Args:
        width: of the cpw.
        gap: of the cpw.
        resonator_kwargs: resonator kwargs.
    """
    c = gf.Component()
    cpw_comp = c << cpw("resonator", gap=gap, width=width, **resonator_kwargs)

    t1 = c << termination_close(width=width, gap=gap)
    if lambda_4:
        t2 = c << termination_open(width=width, gap=gap)
    else:
        t2 = c << termination_close(width=width, gap=gap)
    t1.connect("o1", cpw_comp.ports["o1"])
    t2.connect("o1", cpw_comp.ports["o2"])

    c.add_ports(cpw_comp.ports)
    c.info.update(dict(width=width, gap=gap))
    return c


@gf.cell()
def resonator_array(
    resonator_attrs: dict,
    central_cpw: ComponentSpec = cpw_with_ports,
    spacing: float = 1000.0,
    start_x: Optional[float] = None,
    distance: float = 5.0,
    **resonator_kwargs,
) -> Component:
    """Place alternated resonators along a central cpw line."""
    c = gf.Component()
    central = c << gf.get_component(central_cpw)
    N = len(list(resonator_attrs.values())[0])
    if start_x is None:
        start_x = (central.info["cpw_length"] - spacing * (N - 1)) / 2

    dy_central = central.info["width"] / 2 + central.info["gap"]
    for i in range(N):
        specific_attrs = {key: item[i] for key, item in resonator_attrs.items()}
        res = c << resonator_cpw(**specific_attrs, **resonator_kwargs)
        dy_resonator = res.info["width"] / 2 + res.info["gap"]
        res.rotate(-90)
        res.move(
            origin=res.ports["o2"],
            destination=[
                i * spacing + start_x - specific_attrs["dc"],
                dy_central + dy_resonator + distance,
            ],
        )
        if i % 2 == 0:
            res.mirror_y()
    return c
