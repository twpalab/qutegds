"""List of coplanar waveguide elements."""

from functools import partial

import gdsfactory as gf
from gdsfactory.typings import ComponentFactory, ComponentSpec

from qutegds.geometry import subtract


@gf.cell()
def cpw(component_name: str, gap: float = 1, width=2, **kwargs):
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


straight = partial(cpw, component_name="straight")
snake = partial(cpw, component_name="delay_snake")


@gf.cell()
def straight_taper(
    straight: ComponentSpec = gf.components.straight,
    taper: ComponentFactory = gf.components.taper,
):
    """Return straight section connected with taper."""
    st = gf.get_component(straight)
    return gf.add_tapers(
        st,
        taper=taper,
        ports=[st["o1"]],
    )


@gf.cell()
def rf_port(
    width1: float = 2,
    width2: float = 4,
    gap1: float = 1,
    gap2: float = 2,
    len_taper: float = 4,
    len_rect: float = 4,
    **kwargs
):
    """Return rf port."""
    cpw = gf.Component()
    straight = partial(gf.components.straight, length=len_rect, **kwargs)
    taper = partial(gf.components.taper, length=len_taper, **kwargs)

    outer = straight_taper(
        straight=partial(straight, width=width2 + 2 * gap2),
        taper=partial(taper, width1=width1 + 2 * gap1, width2=width2 + 2 * gap2),
    )
    inner = straight_taper(
        straight=partial(straight, width=width2),
        taper=partial(taper, width1=width1, width2=width2),
    )
    _ = cpw << subtract(outer, inner)
    cpw.add_ports(outer.ports)
    return cpw
