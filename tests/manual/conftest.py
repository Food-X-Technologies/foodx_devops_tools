#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

import pytest

from foodx_devops_tools.azure.cloud import (
    AzureCredentials,
    AzureSubscriptionConfiguration,
)


def pytest_addoption(parser):
    parser.addoption(
        "--subscription",
        action="store",
        default=None,
        help="Azure Cloud subscription id or name",
    )
    parser.addoption(
        "--tenant",
        action="store",
        default=None,
        help="Azure Cloud tenant id or name",
    )
    parser.addoption(
        "--userid",
        action="store",
        default=None,
        help="Azure Cloud service principal id",
    )
    parser.addoption(
        "--secret",
        action="store",
        default=None,
        help="Azure Cloud service principal secret",
    )
    parser.addoption(
        "--parameters",
        action="store",
        default=None,
        help="Path to deployment ARM template parameters file",
    )
    parser.addoption(
        "--template",
        action="store",
        default=None,
        help="Path to deployment ARM template file",
    )


@pytest.fixture
def user_subscription(request) -> AzureSubscriptionConfiguration:
    this_id = request.config.getoption("--subscription")
    this_tenant = request.config.getoption("--tenant")
    this_sub = AzureSubscriptionConfiguration(
        subscription_id=this_id, tenant_id=this_tenant
    )
    return this_sub


@pytest.fixture
def service_principal_credentials(request) -> AzureCredentials:
    this_id = request.config.getoption("--userid")
    this_password = request.config.getoption("--secret")
    this_sub = request.config.getoption("--subscription")
    this_tenant = request.config.getoption("--tenant")
    this_creds = AzureCredentials(
        userid=this_id,
        secret=this_password,
        subscription=this_sub,
        tenant=this_tenant,
        name="mock-name",
    )
    return this_creds


@pytest.fixture
def template_file(request) -> pathlib.Path:
    return pathlib.Path(request.config.getoption("--template"))


@pytest.fixture
def parameters_file(request) -> pathlib.Path:
    return pathlib.Path(request.config.getoption("--parameters"))
