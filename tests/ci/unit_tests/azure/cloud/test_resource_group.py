#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import re

import pytest

from foodx_devops_tools.azure.cloud import AzureSubscriptionConfiguration
from foodx_devops_tools.azure.cloud.exceptions import ResourceGroupError
from foodx_devops_tools.azure.cloud.resource_group import AZURE_GROUP_ID_PATTERN
from foodx_devops_tools.azure.cloud.resource_group import (
    check_exists as resource_group_exists,
)
from foodx_devops_tools.azure.cloud.resource_group import (
    create as create_resource_group,
)
from foodx_devops_tools.utilities import CapturedStreams

MOCK_SUBSCRIPTION = AzureSubscriptionConfiguration(
    subscription_id="123-abc", tenant_id="abc-123"
)

MOCKING_PATHS = {
    "group_exists": "foodx_devops_tools.azure.cloud.resource_group"
    ".check_exists",
    "json_loads": "foodx_devops_tools.azure.cloud.resource_group.json.loads",
    "run_async": "foodx_devops_tools.azure.cloud.resource_group"
    ".run_async_command",
}


class TestResourceGroupIdRegex:
    def test_clean(self):
        expected = {
            "subscription_id": "9aaa123-c1ba-4e79-a9af-dbexamplecb",
            "group_name": "some-name",
        }
        data = "/subscriptions/{0}/resourceGroups/{1}".format(
            expected["subscription_id"], expected["group_name"]
        )

        result = re.match(AZURE_GROUP_ID_PATTERN, data)

        assert result
        assert result.group("subscription_id") == expected["subscription_id"]
        assert result.group("group_name") == expected["group_name"]


class TestResourceGroupExists:
    MOCK_SUBSCRIPTION = AzureSubscriptionConfiguration(
        subscription_id="123-abc", tenant_id="abc-123"
    )
    MOCK_RETURN = CapturedStreams(
        out="""[
  {
    "id": "/subscriptions/9aaa123-c1ba-4e79-a9af-dbexamplecb/resourceGroups/some-name",
    "location": "canadacentral",
    "managedBy": null,
    "name": "some-name",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null,
    "type": "Microsoft.Resources/resourceGroups"
  }
]
""",
        error="",
    )

    @pytest.mark.asyncio
    async def test_clean(self, mock_async_method):
        mock_async_method(
            MOCKING_PATHS["run_async"],
            return_value=self.MOCK_RETURN,
        )

        assert not await resource_group_exists("notagroup", MOCK_SUBSCRIPTION)
        result = await resource_group_exists("some-name", MOCK_SUBSCRIPTION)

        assert result == {
            "id": "/subscriptions/9aaa123-c1ba-4e79-a9af-dbexamplecb/resourceGroups/some-name",
            "location": "canadacentral",
            "managedBy": None,
            "name": "some-name",
            "properties": {"provisioningState": "Succeeded"},
            "tags": None,
            "type": "Microsoft.Resources/resourceGroups",
        }

    @pytest.mark.asyncio
    async def test_raises(self, mock_async_method, mocker):
        mock_async_method(
            MOCKING_PATHS["run_async"],
            return_value=self.MOCK_RETURN,
        )
        mocker.patch(
            MOCKING_PATHS["json_loads"],
            side_effect=RuntimeError("some error"),
        )

        with pytest.raises(
            ResourceGroupError,
            match=r"^Problem acquiring resource group data",
        ):
            await resource_group_exists("some-name", MOCK_SUBSCRIPTION)

    @pytest.mark.asyncio
    async def test_async_cancelled_raises(self, mock_async_method, mocker):
        mock_async_method(
            MOCKING_PATHS["run_async"],
            return_value=self.MOCK_RETURN,
        )
        mocker.patch(
            MOCKING_PATHS["json_loads"],
            side_effect=asyncio.CancelledError(),
        )

        with pytest.raises(asyncio.CancelledError):
            await resource_group_exists("some-name", MOCK_SUBSCRIPTION)


class TestCreateResourceGroup:
    MOCK_RETURN = CapturedStreams(out="good run", error="")
    MOCK_GROUP_DATA = {
        "id": "/subscriptions/9aaa123-c1ba-4e79-a9af-dbexamplecb/resourceGroups/some-name",
        "location": "canadacentral",
        "managedBy": None,
        "name": "some-name",
        "properties": {"provisioningState": "Succeeded"},
        "tags": None,
        "type": "Microsoft.Resources/resourceGroups",
    }

    @pytest.mark.asyncio
    async def test_not_exists_created(self, mock_async_method, mocker):
        mock_run = mock_async_method(
            MOCKING_PATHS["run_async"],
            return_value=self.MOCK_RETURN,
        )
        mock_async_method(
            MOCKING_PATHS["group_exists"],
            return_value=None,
        )

        await create_resource_group(
            "some-name", "canadacentral", MOCK_SUBSCRIPTION
        )

        mock_run.assert_has_calls(
            [
                mocker.call(
                    [
                        "az",
                        "group",
                        "create",
                        "--resource-group",
                        "some-name",
                        "--location",
                        "canadacentral",
                    ]
                )
            ]
        )

    @pytest.mark.asyncio
    async def test_exists_do_nothing(self, mock_async_method):
        mock_run = mock_async_method(
            MOCKING_PATHS["run_async"],
            return_value=self.MOCK_RETURN,
        )
        mock_async_method(
            MOCKING_PATHS["group_exists"],
            return_value=self.MOCK_GROUP_DATA.copy(),
        )

        await create_resource_group(
            "some-name", "canadacentral", MOCK_SUBSCRIPTION
        )

        mock_run.assert_not_called()


# class TestDeployResourceGroup:
#     MOCK_SUBSCRIPTION = AzureSubscriptionConfiguration(
#         subscription_id="123-abc", tenant_id="abc-123")
#     MOCK_RETURN=CapturedStreams(out="good run", error="")
#     @pytest.mark.asyncio
#     async def test_clean(self,mock_async_method):
#         mock_run=mock_async_method("foodx_devops_tools.cli.run_async_command",
#                                    return_value=self.MOCK_RETURN)
#         await deploy_resource_group(,,self.MOCK_SUBSCRIPTION)
#         assert False
