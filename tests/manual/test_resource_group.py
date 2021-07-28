#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Run resource group tests against an actual Azure Cloud subscription."""

import logging

import pytest

from foodx_devops_tools.azure.cloud.resource_group import (
    check_exists as check_resource_group_exists,
)
from foodx_devops_tools.azure.cloud.resource_group import (
    create as create_resource_group,
)
from foodx_devops_tools.azure.cloud.resource_group import (
    delete as delete_resource_group,
)

from .support import (  # noqa: F401
    clean_teardown,
    prexisting_resource_group,
    unique_group_name,
)

log = logging.getLogger(__name__)


class TestCheckResourceGroupExists:
    @pytest.mark.asyncio
    async def test_clean(
        self, prexisting_resource_group, unique_group_name, user_subscription
    ):
        expected_name = unique_group_name
        assert not await check_resource_group_exists(
            expected_name, user_subscription
        )
        async with prexisting_resource_group(expected_name):
            result = await check_resource_group_exists(
                expected_name, user_subscription
            )

            assert result["name"] == expected_name


class TestCreateResourceGroup:
    @pytest.mark.asyncio
    async def test_clean(
        self, clean_teardown, unique_group_name, user_subscription
    ):
        expected_name = unique_group_name
        async with clean_teardown(expected_name):
            await create_resource_group(
                expected_name, "West US 2", user_subscription
            )

            assert await check_resource_group_exists(
                expected_name, user_subscription
            )


class TestDeleteResourceGroup:
    @pytest.mark.asyncio
    async def test_clean(
        self, prexisting_resource_group, unique_group_name, user_subscription
    ):
        expected_name = unique_group_name
        async with prexisting_resource_group(expected_name):
            await delete_resource_group(expected_name, user_subscription)

            assert not await check_resource_group_exists(
                expected_name, user_subscription
            )
