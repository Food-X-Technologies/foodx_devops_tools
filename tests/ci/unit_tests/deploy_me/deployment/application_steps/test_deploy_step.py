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
from foodx_devops_tools.deploy_me.application_steps import deploy_step


@pytest.mark.asyncio
async def test_clean(
    mock_apply_template,
    mock_deploystep_context,
    mock_rg_deploy,
    mock_run_puff,
    mock_verify_puff_target,
):
    await deploy_step(**mock_deploystep_context)

    mock_rg_deploy.assert_called_once()


@pytest.mark.asyncio
async def test_default_override_parameters(
    default_override_parameters,
    mock_apply_template,
    mock_deploystep_context,
    mock_rg_deploy,
    mock_run_puff,
    mock_verify_puff_target,
    mocker,
):
    this_context = copy.deepcopy(mock_deploystep_context)
    this_context["this_step"].static_secrets = False

    await deploy_step(**this_context)

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
    mock_apply_template,
    mock_deploystep_context,
    mock_rg_deploy,
    mock_run_puff,
    mock_verify_puff_target,
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

    await deploy_step(**this_context)

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
async def test_step_skip(caplog, mock_deploystep_context, mock_rg_deploy):
    with caplog.at_level(logging.DEBUG):
        mock_deploystep_context["deployment_data"].data.to = StructuredTo(
            frame="f1", application="a1", step="other_step"
        )

        await deploy_step(**mock_deploystep_context)

        mock_rg_deploy.assert_not_called()

        assert (
            "application step skipped using deployment specifier" in caplog.text
        )
