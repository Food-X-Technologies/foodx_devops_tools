#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

import pytest

from foodx_devops_tools.azure.cloud import AzureSubscriptionConfiguration


def pytest_addoption(parser):
    parser.addoption(
        "--subscription",
        action="store",
        default=None,
        help="Azure Cloud subscription id or name",
    )
    parser.addoption(
        "--parameters",
        action="store",
        default=None,
        help="Path to deployment ARM " "template parameters file",
    )
    parser.addoption(
        "--template",
        action="store",
        default=None,
        help="Path to deployment " "ARM " "template file",
    )


@pytest.fixture
def user_subscription(request) -> AzureSubscriptionConfiguration:
    this_id = request.config.getoption("--subscription")
    this_sub = AzureSubscriptionConfiguration(subscription_id=this_id)
    return this_sub


@pytest.fixture
def template_file(request) -> pathlib.Path:
    return pathlib.Path(request.config.getoption("--template"))


@pytest.fixture
def parameters_file(request) -> pathlib.Path:
    return pathlib.Path(request.config.getoption("--parameters"))
