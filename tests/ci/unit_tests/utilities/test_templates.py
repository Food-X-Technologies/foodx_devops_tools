#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

import pytest

from foodx_devops_tools.utilities.templates import prepare_deployment_files


@pytest.fixture()
def mock_run(mock_async_method):
    mock_puff = mock_async_method(
        "foodx_devops_tools.utilities.templates.run_puff"
    )
    mock_template = mock_async_method(
        "foodx_devops_tools.utilities.templates.FrameTemplates"
        ".apply_template"
    )

    return mock_puff, mock_template


class TestPrepareDeploymentFiles:
    MOCK_PARAMETERS = {
        "k1": "v1",
        "k2": "v2",
    }

    @pytest.mark.asyncio
    async def test_clean(self, mock_run):
        mock_path = pathlib.Path("some/path")
        mock_puff, _ = mock_run

        actual_arm, actual_puff = await prepare_deployment_files(
            mock_path, mock_path, mock_path, self.MOCK_PARAMETERS
        )

        assert actual_puff == mock_path
        assert actual_arm == mock_path
        mock_puff.assert_called_once_with(
            mock_path, False, False, disable_ascii_art=True
        )

    @pytest.mark.asyncio
    async def test_jinja2_puff(self, mock_run):
        mock_puff, mock_template = mock_run

        mock_other_paths = pathlib.Path("some/file")
        mock_puff_path = pathlib.Path("some/jinja2.path")
        expected_target = pathlib.Path("some/path")

        actual_arm, actual_puff = await prepare_deployment_files(
            mock_puff_path,
            mock_other_paths,
            mock_other_paths,
            self.MOCK_PARAMETERS,
        )

        assert actual_puff == expected_target
        assert actual_arm == mock_other_paths
        mock_puff.assert_called_once_with(
            expected_target, False, False, disable_ascii_art=True
        )
        mock_template.assert_called_once_with(
            mock_puff_path.name, expected_target, self.MOCK_PARAMETERS
        )

    @pytest.mark.asyncio
    async def test_jinja2_arm(self, mock_run):
        mock_puff, mock_template = mock_run

        mock_other_paths = pathlib.Path("some/file")
        mock_arm_path = pathlib.Path("some/jinja2.path")
        expected_target = pathlib.Path("some/path")

        actual_arm, actual_puff = await prepare_deployment_files(
            mock_other_paths,
            mock_arm_path,
            mock_other_paths,
            self.MOCK_PARAMETERS,
        )

        assert actual_arm == expected_target
        assert actual_puff == mock_other_paths
        mock_puff.assert_called_once_with(
            mock_other_paths, False, False, disable_ascii_art=True
        )
        mock_template.assert_called_once_with(
            mock_arm_path.name, expected_target, self.MOCK_PARAMETERS
        )
