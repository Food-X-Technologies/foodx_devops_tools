#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Run resource tests against an actual Azure Cloud instance"""

import json
import logging
import uuid

import pytest

from foodx_devops_tools.azure.cloud import deploy_resource_group
from foodx_devops_tools.azure.cloud.resource import (
    check_exists as check_resource_exists,
)

from .support import (  # noqa: F401
    clean_teardown,
    prexisting_resource_group,
    unique_group_name,
)

log = logging.getLogger(__name__)


class TestDeployResourceGroup:
    @pytest.mark.asyncio
    async def test_existing_resource_group_clean(
        self,
        prexisting_resource_group,
        unique_group_name,
        user_subscription,
        template_file,
        parameters_file,
    ):
        expected_group = unique_group_name
        expected_resource = str(uuid.uuid4()).replace("-", "")[0:20]
        expected_location = "eastus"
        with parameters_file.open(mode="r") as f:
            data = json.load(f)
        data["parameters"]["storageAccountName"]["value"] = expected_resource
        if isinstance(data["parameters"]["location"], str):
            data["parameters"]["location"] = {"value": expected_location}
        else:
            data["parameters"]["location"]["value"] = expected_location
        with parameters_file.open(mode="w") as f:
            json.dump(data, f)

        async with prexisting_resource_group(expected_group):
            await deploy_resource_group(
                expected_group,
                template_file,
                parameters_file,
                expected_location,
                user_subscription,
            )

            await self.do_check(expected_resource, user_subscription)

    async def do_check(self, resource_name: str, subscription):
        result = await check_resource_exists(resource_name, subscription)
        assert len(result) == 1
        assert result[0]["name"] == resource_name
        assert not await check_resource_exists(
            resource_name + "notaresource", subscription
        )
