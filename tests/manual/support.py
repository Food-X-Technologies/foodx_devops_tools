#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.
import asyncio
import contextlib
import logging
import typing
import uuid

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

log = logging.getLogger(__name__)


@pytest.fixture()
def prexisting_resource_group(user_subscription):
    @contextlib.asynccontextmanager
    async def _apply(group_name: str) -> typing.Generator[None, None, None]:
        await create_resource_group(group_name, "West US 2", user_subscription)
        assert await check_resource_group_exists(group_name, user_subscription)

        yield

        # clean up any created resource group on context close
        await asyncio.shield(
            delete_resource_group(group_name, user_subscription)
        )

    return _apply


@pytest.fixture()
def unique_group_name():
    return str(uuid.uuid4())


@pytest.fixture()
def clean_teardown(user_subscription):
    @contextlib.asynccontextmanager
    async def _apply(group_name: str) -> typing.Generator[None, None, None]:
        yield

        await delete_resource_group(group_name, user_subscription)

    return _apply
