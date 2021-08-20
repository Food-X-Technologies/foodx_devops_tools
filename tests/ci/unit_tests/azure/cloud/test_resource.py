#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import json

import pytest

from foodx_devops_tools.azure.cloud.resource import (
    AzureSubscriptionConfiguration,
    ResourceError,
    check_exists,
    list_resources,
)
from foodx_devops_tools.utilities import CapturedStreams

MOCKING_PATHS = {
    "json_loads": "foodx_devops_tools.azure.cloud.resource.json.loads",
    "run_async": "foodx_devops_tools.azure.cloud.resource" ".run_async_command",
    "list_resources": "foodx_devops_tools.azure.cloud.resource"
    ".list_resources",
}
MOCK_SUBSCRIPTION = AzureSubscriptionConfiguration(
    subscription_id="123-abc", tenant_id="abc-123"
)

MOCK_DATA = [
    {
        "id": "some-id",
        "name": "some-name",
    },
    {
        "id": "another-id",
        "name": "other-name",
    },
]
MOCK_RETURN = CapturedStreams(out=json.dumps(MOCK_DATA), error="")


class TestListResources:
    @pytest.mark.asyncio
    async def test_name_clean(self, mock_async_method):
        mock_async_method(
            MOCKING_PATHS["run_async"],
            return_value=MOCK_RETURN,
        )

        result = await list_resources(MOCK_SUBSCRIPTION, name="resource-name")

        assert result == MOCK_DATA

    @pytest.mark.asyncio
    async def test_default(self, mock_async_method):
        mock_async_method(
            MOCKING_PATHS["run_async"],
            return_value=list(),
        )

        with pytest.raises(
            ResourceError,
            match=r"^Must specify at least one of name, location or tag",
        ):
            await list_resources(MOCK_SUBSCRIPTION)


class TestCheckExists:
    MOCK_MULTIPLE_DATA = [
        {
            "id": "some-id",
            "name": "some-name",
        },
        {
            "id": "other-id",
            "name": "some-name",
        },
        {
            "id": "another-id",
            "name": "other-name",
        },
    ]
    MOCK_MULTIPLE_RETURN = CapturedStreams(
        out=json.dumps(MOCK_MULTIPLE_DATA), error=""
    )

    @pytest.mark.asyncio
    async def test_resource_found(self, mock_async_method):
        mock_async_method(
            MOCKING_PATHS["run_async"],
            return_value=MOCK_RETURN,
        )

        result = await check_exists("some-name", MOCK_SUBSCRIPTION)

        assert len(result) == 1
        assert result[0]["name"] == "some-name"

    @pytest.mark.asyncio
    async def test_multiple_resources_found(self, mock_async_method):
        mock_async_method(
            MOCKING_PATHS["run_async"],
            return_value=self.MOCK_MULTIPLE_RETURN,
        )

        result = await check_exists("some-name", MOCK_SUBSCRIPTION)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_resource_not_found(self, mock_async_method):
        mock_async_method(
            MOCKING_PATHS["run_async"],
            return_value=MOCK_RETURN,
        )

        result = await check_exists("notvalid", MOCK_SUBSCRIPTION)
        assert not result

    @pytest.mark.asyncio
    async def test_async_cancelled_raises(self, mock_async_method, mocker):
        mock_async_method(
            MOCKING_PATHS["run_async"],
            return_value=MOCK_RETURN,
        )
        mocker.patch(
            MOCKING_PATHS["list_resources"],
            side_effect=asyncio.CancelledError(),
        )

        with pytest.raises(asyncio.CancelledError):
            await check_exists("some-name", MOCK_SUBSCRIPTION)
