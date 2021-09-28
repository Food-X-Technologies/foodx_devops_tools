#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy
import logging

import pytest

from foodx_devops_tools._to import StructuredTo
from foodx_devops_tools.deploy_me._deployment import _deploy_step


@pytest.fixture()
def mock_run_puff(mock_async_method):
    this_mock = mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.run_puff"
    )
    return this_mock


@pytest.fixture()
def mock_do_snippets(mock_async_method):
    this_mock = mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.do_snippet_substitution"
    )
    return this_mock


@pytest.fixture()
def mock_rg_deploy(mock_async_method):
    this_mock = mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.deploy_resource_group"
    )
    return this_mock


@pytest.fixture()
def mock_login(mock_async_method):
    mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.login_service_principal"
    )


@pytest.mark.asyncio
async def test_clean(
    mock_deploystep_context,
    mock_login,
    mock_rg_deploy,
    mock_run_puff,
    mock_do_snippets,
):
    await _deploy_step(**mock_deploystep_context)

    mock_rg_deploy.assert_called_once()


@pytest.mark.asyncio
async def test_default_override_parameters(
    default_override_parameters,
    mock_deploystep_context,
    mock_login,
    mock_rg_deploy,
    mock_run_puff,
    mock_do_snippets,
    mocker,
):
    this_context = copy.deepcopy(mock_deploystep_context)
    this_context["this_step"].static_secrets = False

    await _deploy_step(**this_context)

    expected_defaults = default_override_parameters(
        mock_deploystep_context["deployment_data"]
    )
    mock_rg_deploy.assert_called_once_with(
        mocker.ANY,
        mocker.ANY,
        mocker.ANY,
        mocker.ANY,
        mocker.ANY,
        mocker.ANY,
        deployment_name="app-name_this-step_12345",
        override_parameters=expected_defaults,
        validate=mocker.ANY,
    )


@pytest.mark.asyncio
async def test_secrets_enabled(
    default_override_parameters,
    mock_deploystep_context,
    mock_login,
    mock_rg_deploy,
    mock_run_puff,
    mock_do_snippets,
    mocker,
):
    this_context = copy.deepcopy(mock_deploystep_context)
    this_context["this_step"].static_secrets = True

    this_context["deployment_data"].data.static_secrets = {
        "one": 1,
        "two": "2",
    }
    expected_parameters = default_override_parameters(
        mock_deploystep_context["deployment_data"]
    )
    expected_parameters.update(
        {
            "staticSecrets": [
                {
                    "enabled": True,
                    "key": "one",
                    "value": 1,
                },
                {
                    "enabled": True,
                    "key": "two",
                    "value": "2",
                },
            ],
        }
    )

    await _deploy_step(**this_context)

    mock_rg_deploy.assert_called_once_with(
        mocker.ANY,
        mocker.ANY,
        mocker.ANY,
        mocker.ANY,
        mocker.ANY,
        mocker.ANY,
        deployment_name="app-name_this-step_12345",
        override_parameters=expected_parameters,
        validate=mocker.ANY,
    )


@pytest.mark.asyncio
async def test_step_skip(
    caplog, mock_deploystep_context, mock_login, mock_rg_deploy
):
    with caplog.at_level(logging.DEBUG):
        mock_deploystep_context["deployment_data"].data.to = StructuredTo(
            frame="f1", application="a1", step="other_step"
        )

        await _deploy_step(**mock_deploystep_context)

        mock_rg_deploy.assert_not_called()

        assert (
            "application step skipped using deployment specifier" in caplog.text
        )
