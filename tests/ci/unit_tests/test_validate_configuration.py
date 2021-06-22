#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.validate_configuration import (
    ExitState,
    PipelineConfigurationError,
    _main,
)
from tests.ci.support.click_runner import (  # noqa: F401
    click_runner,
    isolated_filesystem,
)


class TestMain:
    def test_default(self, click_runner, mocker):
        expected_dir = "some/path"

        mocker.patch(
            "foodx_devops_tools.validate_configuration"
            ".PipelineConfiguration.from_files"
        )

        with isolated_filesystem(expected_dir, click_runner):
            result = click_runner.invoke(_main, [expected_dir])

            assert result.exit_code == 0

    def test_configuration_error_exits_dirty(self, click_runner, mocker):
        expected_dir = "some/path"

        mocker.patch(
            "foodx_devops_tools.validate_configuration"
            ".PipelineConfiguration.from_files",
            side_effect=PipelineConfigurationError("some error"),
        )

        with isolated_filesystem(expected_dir, click_runner):
            result = click_runner.invoke(_main, [expected_dir])

            assert result.exit_code == ExitState.MISSING_GITREF.value

    def test_unknown_error_exits_dirty(self, click_runner, mocker):
        expected_dir = "some/path"

        mocker.patch(
            "foodx_devops_tools.validate_configuration"
            ".PipelineConfiguration.from_files",
            side_effect=RuntimeError("some error"),
        )

        with isolated_filesystem(expected_dir, click_runner):
            result = click_runner.invoke(_main, [expected_dir])

            assert result.exit_code == ExitState.UNKNOWN.value
