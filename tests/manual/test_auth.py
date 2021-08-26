#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Run authentication tests against an actual Azure Cloud instance"""

import json
import logging

import pytest

from foodx_devops_tools.azure.cloud import (
    AzureCredentials,
    login_service_principal,
)
from foodx_devops_tools.azure.cloud.exceptions import AzureAuthenticationError

log = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_clean(service_principal_credentials):
    await login_service_principal(service_principal_credentials)


@pytest.mark.asyncio
async def test_failed():
    MOCK_CREDENTIALS = AzureCredentials(
        name="mock_user",
        userid="123abc",
        secret="verysecret",
        subscription="this_subscription",
        tenant="this_tenant",
    )
    with pytest.raises(AzureAuthenticationError):
        await login_service_principal(MOCK_CREDENTIALS)
