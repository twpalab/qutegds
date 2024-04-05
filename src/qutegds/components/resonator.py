"""resonator module."""

from typing import Dict, List, Optional

import gdsfactory as gf
import numpy as np
from gdsfactory import Component
from gdsfactory.routing.manhattan import round_corners
from gdsfactory.typings import ComponentSpec, CrossSectionSpec, LayerSpec

from qutegds.components.cpw_base import cpw, cpw_with_ports


@gf.cell()
def resonator(
    length: float = 400.0,
    L0: float = 30.0,
    n: int = 1,
    width: float = 2,
    dy: float = 15,
    dx: float = 40,
    dc: float = 5,
    radius: float = 10,
    p: float = 0.5,
    bend: ComponentSpec = "bend_euler",
    cross_section: CrossSectionSpec = "xs_sc",
    **kwargs,
) -> Component:
    """Return a meandering resonator.

    Args:
        length (float): Total length of the resonator.
        L0 (float): Length of the straight section.
        n (int): Number of meander loops.
        width (float): Width of the resonator's line.
        dy (float): Half-distance between bends.
        dx (float): Distance between the coupling section and the first bend.
        dc (float): Length of the final couplng section of the resonator.
        radius (float): Radius of the bends.
        p (float): Parameter controlling the curvature of bends (default is 0.5, 0 is circle).
        bend (ComponentSpec): Type of bend used for the resonator.
        cross_section (CrossSectionSpec): Cross section specification.
        **kwargs: Additional keyword arguments for gdsfactory.routing.manhattan.round_corners.


           | L0 |      L2       |

                 ->-------------|
                                |
                                | 2 * dy
            |-------------------|
            |                        ^
    2  * dy |                        | dc
            |------------------------|

            |                   | dx |
    """
    bend90 = gf.get_component(
        bend,
        p=p,
        cross_section=cross_section,
        width=width,
        with_arc_floorplan=True,
        radius=radius,
    )

    if radius < 0:
        raise ValueError("Radius must be positive.")
    if dy < radius:
        raise ValueError("dy must be >= radius.")

    curve = bend90.info[
        "length"
    ]  # sligthly different from a "perfect circle"(p=0) because p=0.5 by default
    lc = dx - radius + curve + dc  # coupling termination
    L2 = (length + L0 + 4 * n * (2 * radius - curve - dy) - lc) / (2 * n + 1) - L0
    if L2 < 0:
        raise ValueError(
            "Snake is too short: either reduce L0, dy, n or increase the total length."
        )

    y = 0
    path = [(0, y), (L2, y)]
    for _ in range(n):
        y -= 2 * dy
        path += [(L2, y), (-L0, y)]
        y -= 2 * dy
        path += [(-L0, y), (L2, y)]
    path += [(L2 + dx, y), (L2 + dx, y + radius + dc)]

    c = gf.Component()
    route = round_corners(
        points=list(np.array(path).round(2)),
        bend=bend90,
        cross_section=cross_section,
        width=width,
        **kwargs,
    )

    c.add(route.references)
    c.add_port("o1", port=route.ports[0])
    c.add_port("o2", port=route.ports[1])
    c.info.update({"length": route.length})
    return c


@gf.cell()
def termination_open(
    width: float = 10,
    angle_resolution: float = 1,
    gap: float = 5,
    dt: float = 3,
    r: float = 4,
    layer: LayerSpec = (1, 0),
) -> Component:
    """Generate an open-circuit termination for a cpw.

    Args:
        width (float): of the terminated cpw.
        angle_resolution (float): number of degrees per point.
        gap (float): of the terminated cpw.
        dt (float): termination longitudinal extension.
        r (float): radius of the termination curvatures.
        layer (LayerSpec): layer specification.
    """
    if width <= 0:
        raise ValueError(f"width={width} must be positive.")
    if r > (width / 2 + gap):
        raise ValueError(f"radius={r} must be < (width/2 + gap) = {width/2+gap}")
    c = Component()

    t_inner = np.linspace(0, np.pi, int(180 / angle_resolution) + 1)
    xpts = list(width / 2 * np.cos(t_inner))
    ypts = list(width / 2 * np.sin(t_inner))
    xpts.append(-width / 2 - gap)
    ypts.append(0)

    t_outer = np.linspace(0, np.pi / 2, int(90 / angle_resolution) + 1)
    xpts_aux = width / 2 + gap + r * (np.cos(t_outer) - 1)
    ypts_aux = list(width / 2 + dt + r * (np.sin(t_outer) - 1))

    xpts = xpts + list(-xpts_aux) + list(xpts_aux)[::-1]
    ypts = ypts + (ypts_aux + ypts_aux[::-1])
    xpts.append(width / 2 + gap)
    ypts.append(0)

    c.add_polygon(points=(xpts, ypts), layer=layer)
    c.add_port(
        name="o1",
        center=(0, 0),
        width=1,
        orientation=270,
        port_type="optical",
        cross_section="xs_sc",
    )
    return c


@gf.cell()
def termination_closed(
    width: float = 10,
    angle_resolution: float = 1,
    gap: float = 5,
    layer: LayerSpec = (1, 0),
) -> Component:
    """Generate an closed-circuit CPW termination.

    Args:
        width (float): of the terminated cpw.
        angle_resolution (float): number of degrees per point.
        gap (float): of the terminated cpw.
        layer (LayerSpec): layer specification.
    """
    if width <= 0:
        raise ValueError(f"width={width} must be > 0")
    c = Component()
    t = np.linspace(0, np.pi, int(360 / angle_resolution) + 1)
    xpts = -width / 2 - gap / 2 + gap / 2 * np.cos(t)
    ypts = gap / 2 * np.sin(t)
    p = c.add_polygon(points=(xpts, ypts), layer=layer)
    _ = c.add_polygon(points=(xpts, ypts), layer=layer)
    p.mirror()
    c.add_port(
        name="o1",
        center=(0, 0),
        width=1,
        orientation=270,
        port_type="optical",
        cross_section="xs_sc",
    )
    return c


@gf.cell()
def resonator_cpw(
    width: float = 6.0,
    gap: float = 3.0,
    termination_coupler: ComponentSpec = termination_closed,
    termination_end: ComponentSpec = termination_open,
    **resonator_kwargs,
) -> Component:
    """Generate a cpw resonator.

    Args:
        width (float): of the cpw.
        gap (float): of the cpw.
        termination_coupler (ComponentSpec): termination to use at the end of the coupling section.
        termination_open (ComponentSpec): termination to use at the end of the resonator.
        resonator_kwargs: keyword arguments for qutegds.components.resonator.
    """
    c = gf.Component()
    cpw_comp = c << cpw("resonator", gap=gap, width=width, **resonator_kwargs)

    t1 = c << gf.get_component(termination_end, width=width, gap=gap)
    t2 = c << gf.get_component(termination_coupler, width=width, gap=gap)
    t1.connect("o1", cpw_comp.ports["o1"])
    t2.connect("o1", cpw_comp.ports["o2"])

    c.add_ports(cpw_comp.ports)
    c.info.update({"width": width, "gap": gap})
    return c


@gf.cell()
def resonator_array(
    resonators_attrs: Dict[str, List],
    central_cpw: ComponentSpec = cpw_with_ports,
    spacing: float = 1000.0,
    shift_x_top_bot: float = 0,
    distance: float = 5.0,
    start_x: Optional[float] = None,
    resonator_indexes: Optional[list] = None,
    resonator_label: ComponentSpec = "text",
    labels_y_offset: Optional[float] = None,
    **resonator_kwargs,
) -> Component:
    """
    Place alternated resonators along a central CPW line.

    Args:
        resonators_attrs (Dict[str, List]): Dictionary containing lists of attributes specific for each resonator.
        central_cpw (ComponentSpec): Component representing the central CPW line.
        spacing (float): Spacing between resonators along the central CPW line.
        shift_x_top_bot (float): Shift in placement between the resonators above and below the central CPW line.
        distance (float): Distance between the central CPW and resonators coupling termination.
        start_x (Optional[float]): Starting x-coordinate for placing resonators.
        resonator_indexes (Optional[list]): List of indexes for reordering the resonators.
        resonator_label (ComponentSpec): Component to add labels for the resonators based on their order indexes.
        labels_y_offset (Optional[float]): If not None, add resonators labels at this distance from the central CPW line.
        **resonator_kwargs: additional keyword arguments for qutegds.components.resonator_cpw common to all resonators.
    """
    c = gf.Component()
    central = c << gf.get_component(central_cpw)
    n_res = len(list(resonators_attrs.values())[0])
    if start_x is None:
        start_x = (central.info["cpw_length"] - spacing * (n_res - 1)) / 2
    if resonator_indexes is None:
        resonator_indexes = list(range(n_res))
    assert len(resonator_indexes) == n_res

    dy_central = central.info["width"] / 2 + central.info["gap"]
    for i in resonator_indexes:
        specific_attrs = {key: item[i] for key, item in resonators_attrs.items()}
        res = c << resonator_cpw(**specific_attrs, **resonator_kwargs)
        res.rotate(-90)
        res.movey(-res.ymin + dy_central + distance)
        if i % 2 == 0:
            movex = i * spacing + start_x
            res.movex(movex)
            res.mirror_y()
        else:
            movex = i * spacing + start_x + shift_x_top_bot
            res.movex(movex)

        if resonator_label:
            lab = c << gf.get_component(resonator_label, text=f"R{i}")
            lab.movex(movex)
            lab.movey((lab.ymin + lab.ymax) / 2 + (-1) ** (i % 2 + 1) * labels_y_offset)

    return c
