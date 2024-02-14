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
    """
    Return straight section connected with taper.

    Args:
        straight (ComponentSpec): straight section of the component
        taper (ComponentFactory): trapezoid section of the component

    """
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
    space_pad: float = SPACE_PAD,
    **kwargs,
) -> Component:
    """Return rf port.

    Args:
        width1 (float): width of the connection to the cpw
        width2 (float): width of the port at the beginning
        gap1 (float): gap of the final cpw
        gap2 (float): gap of the bonding pad
        len_taper (float): length of the
        len_rect (float): length of the bonding pad
        space_pad (float): gap at the side of the bonding pad

    .. jupyter-execute::

        from qutegds import rf_port
        c = rf_port()
        c.plot()
    """
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
    gap: float = GAP,
    width: float = WIDTH,
    length: float = 1000,
    straight: ComponentFactory = cpw,
    launcher: ComponentFactory = rf_port,
) -> Component:
    """
    CPW with ports at extremities.

    gap (float): gap of the cpw line
    width (float): width of the cpw line
    length (float): length of the cpw line
    straight (ComponentFactory): cpw component
    launcher (ComponentFactory): port component

    .. jupyter-execute::

        from qutegds import cpw_with_ports
        c = cpw_with_ports()
        c.plot()
    """
    launch = launcher(gap1=gap, width1=width)
    c = gf.Component()
    lref = c << launch
    lref2 = c << launch
    stref = c << straight(gap=gap, width=width, length=length)

    lref.connect("o1", stref.ports["o2"])
    lref2.connect("o1", stref.ports["o1"])
    return c
