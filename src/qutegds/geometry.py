"""Geometry related functions."""

from functools import partial

import gdsfactory as gf

subtract = partial(gf.geometry.boolean, operation="not")
