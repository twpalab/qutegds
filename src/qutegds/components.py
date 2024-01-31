"""List of coplanar waveguide elements."""
from functools import partial

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import ComponentFactory, ComponentSpec

from qutegds.geometry import subtract

WIDTH = 6
GAP = 3
WIDTH_PAD = 350
GAP_PAD = 70
SPACE_PAD = 10
LEN_CONNECT = 20


@gf.cell()
def cpw(
    component_name: str = "straight", gap: float = GAP, width: float = WIDTH, **kwargs
) -> Component:
    """
    Return simple coplanar waveguide from single component.

    By default, returns negative mask of the CPW trace.

    Args:
        component_name (str): name of the component to be used
        width (float): width of the central CPW trace
        gap (float): space in um between the CPW trace and ground
    """
    cpw = gf.Component()
    outer = gf.get_component(component_name, width=width + 2 * gap, **kwargs)
    inner = gf.get_component(component_name, width=width, **kwargs)
    _ = cpw << subtract(outer, inner)
    cpw.add_ports(outer.ports)
    return cpw


snake = partial(cpw, component_name="delay_snake")


@gf.cell()
def straight_taper(
    straight: ComponentSpec = gf.components.straight,
    taper: ComponentFactory = gf.components.taper,
) -> Component:
    """Return straight section connected with taper."""
    st = gf.get_component(straight)
    return gf.add_tapers(
        st,
        taper=taper,
        ports=[st["o1"]],
    )


@gf.cell()
def rf_port(
    width1: float = WIDTH,
    width2: float = WIDTH_PAD,
    gap1: float = GAP,
    gap2: float = GAP_PAD,
    len_taper: float = 200,
    len_rect: float = 100,
    space_pad=SPACE_PAD,
    len_connect=LEN_CONNECT,
    **kwargs,
) -> Component:
    """Return rf port."""
    cpw = gf.Component()
    straight = partial(gf.components.straight, **kwargs)
    taper = partial(gf.components.taper, length=len_taper, **kwargs)

    outer = straight_taper(
        straight=partial(
            straight, length=len_rect + space_pad, width=width2 + 2 * gap2
        ),
        taper=partial(taper, width1=width1 + 2 * gap1, width2=width2 + 2 * gap2),
    )
    inner = straight_taper(
        straight=partial(straight, length=len_rect, width=width2),
        taper=partial(taper, width1=width1, width2=width2),
    )
    _ = cpw << subtract(outer, inner)
    cpw.add_ports(outer.ports)
    return cpw


@gf.cell()
def cpw_with_ports(
    gap=GAP, width=WIDTH, length=1000, straight=cpw, launcher=rf_port
) -> Component:
    """CPW with ports at extremities."""
    launch = launcher(gap1=gap, width1=width)
    c = gf.Component()
    lref = c << launch
    lref2 = c << launch
    stref = c << straight(gap=gap, width=width, length=length)

    lref.connect("o1", stref.ports["o2"])
    lref2.connect("o1", stref.ports["o1"])
    return c


@gf.cell()
def cpw_with_rounded_ports(radius=10, **kwargs):
    """CPW with rounded ports at extremities."""
    cpw_ports = cpw_with_ports(**kwargs)
    c = gf.Component()
    c.add_polygon(
        gf.geometry.fillet(gf.geometry.union(cpw_ports), radius=radius),
        layer=cpw_ports.layers,
    )
    c.add_ports(cpw_ports.ports)
    return c
