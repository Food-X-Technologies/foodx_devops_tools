#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.pipeline_config.exceptions import (
    PipelineConfigurationError,
)
from foodx_devops_tools.validate_configuration import ExitState, _main
from tests.ci.support.click_runner import (  # noqa: F401
    click_runner,
    isolated_filesystem,
)
from tests.ci.support.pipeline_config import (
    CLEAN_SPLIT,
    MOCK_SECRET,
    NOT_SPLIT,
    split_directories,
)


class TestMain:
    def test_help(self, click_runner, mock_run_puff_check):
        with split_directories(NOT_SPLIT.copy()) as (
            client_config,
            system_config,
        ):
            result = click_runner.invoke(
                _main,
                ["--help"],
            )

            assert result.exit_code == 0
            assert "Validate pipeline configuration files." in result.output

    def test_default(self, click_runner, mock_run_puff_check):
        with split_directories(NOT_SPLIT.copy()) as (
            client_config,
            system_config,
        ):
            result = click_runner.invoke(
                _main,
                [str(client_config), str(system_config), "-"],
                input=MOCK_SECRET,
            )

            assert result.exit_code == 0

    def test_missing_input_ignored(self, click_runner, mock_run_puff_check):
        """--disable-vaults option doesn't read from stdin."""
        with split_directories(NOT_SPLIT.copy()) as (
            client_config,
            system_config,
        ):
            result = click_runner.invoke(
                _main,
                [
                    str(client_config),
                    str(system_config),
                    "-",
                    "--disable-vaults",
                ],
            )

            assert result.exit_code == 0

    def test_split_files(self, click_runner, mock_run_puff_check):
        with split_directories(CLEAN_SPLIT.copy()) as (
            client_config,
            system_config,
        ):
            result = click_runner.invoke(
                _main,
                [
                    str(client_config),
                    str(system_config),
                    "-",
                ],
                input=MOCK_SECRET,
            )

            assert result.exit_code == 0

    def test_configuration_error_exits_dirty(
        self, click_runner, mocker, mock_run_puff_check
    ):
        mocker.patch(
            "foodx_devops_tools.validate_configuration"
            ".PipelineConfiguration.from_files",
            side_effect=PipelineConfigurationError("some error"),
        )

        with split_directories(CLEAN_SPLIT.copy()) as (
            client_config,
            system_config,
        ):
            result = click_runner.invoke(
                _main,
                [
                    str(client_config),
                    str(system_config),
                    "-",
                ],
                input=MOCK_SECRET,
            )

            assert result.exit_code == ExitState.MISSING_GITREF.value

    def test_unknown_error_exits_dirty(
        self, click_runner, mocker, mock_run_puff_check
    ):
        mocker.patch(
            "foodx_devops_tools.validate_configuration"
            ".PipelineConfiguration.from_files",
            side_effect=RuntimeError("some error"),
        )

        with split_directories(CLEAN_SPLIT.copy()) as (
            client_config,
            system_config,
        ):
            result = click_runner.invoke(
                _main,
                [
                    str(client_config),
                    str(system_config),
                    "-",
                ],
                input=MOCK_SECRET,
            )

            assert result.exit_code == ExitState.UNKNOWN.value
