#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

from foodx_devops_tools.pipeline_config import PipelineConfigurationPaths


class TestPipelineConfigurationPaths:
    def test_template_context(self, mocker):
        mock_config = pathlib.Path("mock_config")
        mock_system = pathlib.Path("mock_system")
        mocker.patch(
            "foodx_devops_tools.pipeline_config"
            "._paths.PipelineConfigurationPaths"
            "._PipelineConfigurationPaths__acquire_static_secrets"
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config"
            "._paths.PipelineConfigurationPaths"
            "._PipelineConfigurationPaths__acquire_client_files"
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config"
            "._paths.PipelineConfigurationPaths"
            "._PipelineConfigurationPaths__acquire_system_files"
        )
        mock_paths = [
            {pathlib.Path("one")},
            {pathlib.Path("two")},
        ]
        mocker.patch(
            "foodx_devops_tools.pipeline_config"
            "._paths.PipelineConfigurationPaths"
            "._PipelineConfigurationPaths__acquire_subdir_files",
            side_effect=mock_paths,
        )

        under_test = PipelineConfigurationPaths.from_paths(
            mock_config, mock_system
        )

        expected_context = mock_paths[0].union(mock_paths[1])
        assert under_test.context == expected_context
