"""This code tests all your cells in the PDK

it will test 3 things:

1. difftest: will test the GDS geometry of a new GDS compared to a reference. Thanks to Klayout fast booleans.add()
2. settings test: will compare the settings in YAML with a reference YAML file.add()
3. ensure ports are on grid, to avoid port snapping errors that can create 1nm gaps later on when you build circuits.

"""
import pathlib

import pytest
from gdsfactory.component import Component
from gdsfactory.difftest import difftest
from pytest_regressions.data_regression import DataRegressionFixture

from qutegds import cells

skip_test = {"subtract"}
cell_names = set(cells.keys()) - set(skip_test)
dirpath = pathlib.Path(__file__).absolute().parent / "gds_ref"


@pytest.fixture(params=cell_names, scope="function")
def component(request) -> Component:
    return cells[request.param]()


def test_pdk_gds(component: Component) -> None:
    """Avoid regressions in GDS geometry shapes and layers."""
    difftest(component, dirpath=dirpath)


def test_pdk_settings(
    component: Component, data_regression: DataRegressionFixture
) -> None:
    """Avoid regressions when exporting settings."""
    data_regression.check(component.to_dict())


def test_assert_ports_on_grid(component: Component):
    component.assert_ports_on_grid()
