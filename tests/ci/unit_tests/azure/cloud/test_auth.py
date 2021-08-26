#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.azure.cloud import (
    AzureCredentials,
    login_service_principal,
)
from foodx_devops_tools.azure.cloud.exceptions import AzureAuthenticationError
from foodx_devops_tools.utilities.exceptions import CommandError

MOCK_CREDENTIALS = AzureCredentials(
    name="mock_user",
    userid="123abc",
    secret="verysecret",
    subscription="this_subscription",
    tenant="this_tenant",
)


@pytest.mark.asyncio
async def test_clean(mock_async_method, mocker):
    mock_return = mocker.MagicMock()
    mock_return.out = """{
  "some": "json output"
}
"""

    mock_run = mock_async_method(
        "foodx_devops_tools.azure.cloud.auth.run_async_command",
        return_value=mock_return,
    )

    result = await login_service_principal(MOCK_CREDENTIALS)

    mock_run.assert_called_once_with(
        [
            "az",
            "login",
            "--service-principal",
            "--username",
            "123abc",
            "--password",
            "verysecret",
            "--tenant",
            "this_tenant",
        ]
    )

    assert result == {
        "some": "json output",
    }


@pytest.mark.asyncio
async def test_commanderror_raises(mocker):
    mock_return = mocker.MagicMock()
    mock_return.out = "some output"

    mocker.patch(
        "foodx_devops_tools.azure.cloud.auth.run_async_command",
        side_effect=CommandError(),
    )

    with pytest.raises(
        AzureAuthenticationError,
        match=r"^Service principal authentication failed",
    ):
        await login_service_principal(MOCK_CREDENTIALS)


@pytest.mark.asyncio
async def test_exception_raises(mocker):
    mock_return = mocker.MagicMock()
    mock_return.out = "some output"

    mocker.patch(
        "foodx_devops_tools.azure.cloud.auth.run_async_command",
        side_effect=RuntimeError(),
    )

    with pytest.raises(
        AzureAuthenticationError,
        match=r"^Service principal authentication failed",
    ):
        await login_service_principal(MOCK_CREDENTIALS)
