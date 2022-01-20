#  Copyright (c) 2022 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.deploy_me.application_steps import script_step
from foodx_devops_tools.deploy_me.application_steps._script import (
    run_async_command,
)


@pytest.fixture()
def mock_run_async_command(mock_async_method):
    this_mock = mock_async_method(
        "foodx_devops_tools.deploy_me.application_steps._script"
        ".run_async_command"
    )
    return this_mock


@pytest.fixture()
def mock_apply_dynamic_template(mocker):
    this_mock = mocker.patch(
        "foodx_devops_tools.deploy_me.application_steps._script"
        ".apply_dynamic_template"
    )
    return this_mock


@pytest.mark.asyncio
async def test_clean(mock_shellstep_context, mock_run_async_command):
    await script_step(**mock_shellstep_context)

    mock_run_async_command.assert_called_once_with(
        [
            "/bin/bash",
            "-c",
            # NOTE: jinja2 strips trailing whitespace by default. this can be
            # disabled but it isn't very important here, so just need to note
            # the apparent discrepancy.
            """do something
make f1""",
        ]
    )


@pytest.mark.asyncio
async def test_bash_script():
    this_command = [
        "/bin/bash",
        "-c",
        """echo 123
echo "o\nn\ne" | grep "o"
""",
    ]
    results = await run_async_command(this_command)

    assert "123" in results.out
    assert "o" in results.out
    assert "n" not in results.out
    assert "e" not in results.out
