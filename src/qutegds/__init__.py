"""qutegds module."""

import importlib.metadata as im
import sys

__version__ = im.version(__package__)

import gdsfactory as gf
from gdsfactory.generic_tech import get_generic_pdk
from gdsfactory.get_factories import get_cells

from qutegds.components.chip_layout import (
    centered_chip,
    chip_title,
    squares_at_corner_chip,
)
from qutegds.components.cpw_base import (
    cpw,
    cpw_with_ports,
    rf_port,
    snake,
    straight_taper,
)
from qutegds.components.simple_strip import strip_with_pads, stripes_array

generic_pdk = get_generic_pdk()
cells = get_cells(sys.modules[__name__])
qute_pdk = gf.Pdk(
    name="qute",
    cells=cells,
    base_pdk=generic_pdk,
    layers=generic_pdk.layers,
    layer_views=generic_pdk.layer_views,
    cross_sections=generic_pdk.cross_sections,
)
qute_pdk.activate()
