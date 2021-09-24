#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.release_flow_entry import release_flow
from tests.ci.support.click_runner import click_runner  # noqa: F401


def test_help(click_runner):
    mock_input = ["--help"]

    result = click_runner.invoke(release_flow, mock_input)

    assert result.exit_code == 0
    assert "Release flow command group." in result.output
