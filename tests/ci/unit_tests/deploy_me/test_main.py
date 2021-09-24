#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy
import enum
import logging

import pytest

from foodx_devops_tools.deploy_me._deployment import DeploymentState
from foodx_devops_tools.deploy_me._main import (
    ConfigurationPathsError,
    PipelineCliOptions,
    _report_results,
)
from foodx_devops_tools.deploy_me_entry import deploy_me
from tests.ci.support.click_runner import click_runner  # noqa: F401
from tests.ci.support.pipeline_config import (
    CLEAN_SPLIT,
    MOCK_SECRET,
    split_directories,
)


class TestReportResults:
    def test_success(self, capsys):
        mock_result = DeploymentState.ResultType.success
        number_iterations = 1

        _report_results(mock_result, number_iterations)

        captured = capsys.readouterr()
        assert "success: Deployment succeeded" in captured.out

    def test_skipped(self, capsys):
        mock_result = DeploymentState.ResultType.success
        number_iterations = 0

        _report_results(mock_result, number_iterations)

        captured = capsys.readouterr()
        assert "skipped: Deployment skipped" in captured.out

    def test_failed(self, capsys):
        mock_result = DeploymentState.ResultType.failed
        number_iterations = 1

        with pytest.raises(SystemExit):
            _report_results(mock_result, number_iterations)

        captured = capsys.readouterr()
        assert (
            "FAILED: Deployment failed. Check log for details" in captured.out
        )


@pytest.fixture()
def mock_getsha(mocker):
    def _apply(output: str = ""):
        mocker.patch(
            "foodx_devops_tools.deploy_me._main.get_sha",
            return_value=output,
        )

    return _apply


class TestDeployMe:
    EXPECTED_DEFAULT_OPTIONS = PipelineCliOptions(
        enable_validation=False,
        monitor_sleep_seconds=30,
        wait_timeout_seconds=(15 * 60),
    )

    class MockReleaseState(enum.Enum):
        r1 = enum.auto()

    def test_help(
        self, caplog, click_runner, mocker, mock_async_method, mock_getsha
    ):
        mock_input = [
            "--help",
        ]
        mock_getsha()
        mocker.patch(
            "foodx_devops_tools.deploy_me._main.identify_release_state",
            return_value=TestDeployMe.MockReleaseState.r1,
        )
        mock_deploy = mock_async_method(
            "foodx_devops_tools.deploy_me._main.do_deploy",
            return_value=DeploymentState(
                code=DeploymentState.ResultType.success
            ),
        )
        with split_directories(CLEAN_SPLIT.copy()) as (
            client_path,
            system_path,
        ):
            with caplog.at_level(logging.DEBUG):
                result = click_runner.invoke(
                    deploy_me, mock_input, input=MOCK_SECRET
                )

            assert result.exit_code == 0
            assert "Deploy system resources." in result.output

    def test_default(
        self,
        click_runner,
        caplog,
        mock_async_method,
        mock_getsha,
        mocker,
    ):
        mock_input = list()

        result, mock_deploy = self._run_test(
            mock_input,
            caplog,
            click_runner,
            mock_async_method,
            mock_getsha,
            mocker,
        )

        assert result.exit_code == 0
        mock_deploy.assert_has_calls(
            [
                mocker.call(
                    mocker.ANY, mocker.ANY, self.EXPECTED_DEFAULT_OPTIONS
                ),
                mocker.call(
                    mocker.ANY, mocker.ANY, self.EXPECTED_DEFAULT_OPTIONS
                ),
            ]
        )

    def test_pipeline_id(
        self,
        click_runner,
        caplog,
        mock_async_method,
        mock_getsha,
        mocker,
    ):
        mock_input = [
            "--pipeline-id",
            "refs/heads/main",
        ]

        result, mock_deploy = self._run_test(
            mock_input,
            caplog,
            click_runner,
            mock_async_method,
            mock_getsha,
            mocker,
        )

        assert result.exit_code == 0
        mock_deploy.assert_has_calls(
            [
                mocker.call(
                    mocker.ANY, mocker.ANY, self.EXPECTED_DEFAULT_OPTIONS
                ),
                mocker.call(
                    mocker.ANY, mocker.ANY, self.EXPECTED_DEFAULT_OPTIONS
                ),
            ]
        )

    def _run_test(
        self,
        mock_input,
        caplog,
        click_runner,
        mock_async_method,
        mock_getsha,
        mocker,
    ):
        mock_getsha()
        mocker.patch(
            "foodx_devops_tools.deploy_me._main.identify_release_state",
            return_value=TestDeployMe.MockReleaseState.r1,
        )
        mock_deploy = mock_async_method(
            "foodx_devops_tools.deploy_me._main.do_deploy",
            return_value=DeploymentState(
                code=DeploymentState.ResultType.success
            ),
        )
        with split_directories(CLEAN_SPLIT.copy()) as (
            client_path,
            system_path,
        ):
            mock_input += [
                str(client_path),
                str(system_path),
                "-",
                # --git-ref is mandatory, for now
                "--git-ref",
                "refs/heads/main",
            ]
            with caplog.at_level(logging.DEBUG):
                result = click_runner.invoke(
                    deploy_me, mock_input, input=MOCK_SECRET
                )

        return result, mock_deploy

    def test_validation(
        self,
        caplog,
        click_runner,
        mock_async_method,
        mock_getsha,
        mocker,
    ):
        mock_input = [
            "--validation",
        ]

        result, mock_deploy = self._run_test(
            mock_input,
            caplog,
            click_runner,
            mock_async_method,
            mock_getsha,
            mocker,
        )

        assert result.exit_code == 0
        expected_options = copy.deepcopy(self.EXPECTED_DEFAULT_OPTIONS)
        expected_options.enable_validation = True
        mock_deploy.assert_has_calls(
            [
                mocker.call(mocker.ANY, mocker.ANY, expected_options),
                mocker.call(mocker.ANY, mocker.ANY, expected_options),
            ]
        )

    def test_monitor_sleep(
        self,
        click_runner,
        caplog,
        mock_async_method,
        mock_getsha,
        mocker,
    ):
        mock_input = [
            "--monitor-sleep",
            "120",
        ]

        result, mock_deploy = self._run_test(
            mock_input,
            caplog,
            click_runner,
            mock_async_method,
            mock_getsha,
            mocker,
        )

        assert result.exit_code == 0
        expected_options = PipelineCliOptions(
            enable_validation=False,
            monitor_sleep_seconds=120,
            wait_timeout_seconds=(15 * 60),
        )
        mock_deploy.assert_has_calls(
            [
                mocker.call(mocker.ANY, mocker.ANY, expected_options),
                mocker.call(mocker.ANY, mocker.ANY, expected_options),
            ]
        )

    def test_wait_timeout(
        self,
        click_runner,
        caplog,
        mock_async_method,
        mock_getsha,
        mocker,
    ):
        mock_input = [
            "--wait-timeout",
            "30",
        ]

        result, mock_deploy = self._run_test(
            mock_input,
            caplog,
            click_runner,
            mock_async_method,
            mock_getsha,
            mocker,
        )

        assert result.exit_code == 0
        expected_options = PipelineCliOptions(
            enable_validation=False,
            monitor_sleep_seconds=30,
            wait_timeout_seconds=(30 * 60),
        )
        mock_deploy.assert_has_calls(
            [
                mocker.call(mocker.ANY, mocker.ANY, expected_options),
                mocker.call(mocker.ANY, mocker.ANY, expected_options),
            ]
        )
