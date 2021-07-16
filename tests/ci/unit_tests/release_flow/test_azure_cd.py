# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.release_flow_entry import release_flow
from tests.ci.support.click_runner import click_runner  # noqa: F401


class TestAzureSubcommand:
    def test_azure_release_state(self, click_runner):
        mock_input = ["azure", "state", "refs/heads/feature/some/path"]

        result = click_runner.invoke(release_flow, mock_input)

        assert result.exit_code == 0
        assert result.output == "ftr"

    def test_azure_release_id(self, click_runner):
        mock_input = ["azure", "id", "refs/tags/3.14.159-alpha.13"]

        result = click_runner.invoke(release_flow, mock_input)

        assert result.exit_code == 0
        assert result.output == "3.14.159-alpha.13"
