#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy
import pathlib


class TestConstructDeploymentPaths:
    MOCK_CONTEXT = "some_context"

    def test_none_arm_file_puff_file(self, mock_flattened_deployment):
        under_test = copy.deepcopy(mock_flattened_deployment[0])
        under_test.context.application_name = "this_app"
        under_test.context.frame_name = "f1"
        under_test.context.frame_name = "f1"
        under_test.data.frame_folder = pathlib.Path("frame/folder")

        mock_arm_file = None
        mock_puff_file = None
        mock_target_arm_parameters_file = pathlib.Path(
            "some/arm_parameters.json"
        )

        (
            result_source_arm_template,
            result_target_arm_template,
            result_puff,
            result_parameters,
        ) = under_test.construct_deployment_paths(
            mock_arm_file,
            mock_puff_file,
            mock_target_arm_parameters_file,
        )

        assert result_source_arm_template == pathlib.Path(
            "frame/folder/this_app.json"
        )
        assert result_puff == pathlib.Path("frame/folder/this_app.yml")

        assert result_target_arm_template == pathlib.Path(
            "frame/folder/this_app.json"
        )
        assert result_parameters == pathlib.Path(
            "frame/folder/some/arm_parameters.json"
        )

    def test_arm_file_none_puff_file(self, mock_flattened_deployment):
        under_test = copy.deepcopy(mock_flattened_deployment[0])
        under_test.context.application_name = "this_app"
        under_test.context.frame_name = "f1"
        under_test.data.frame_folder = pathlib.Path("frame/folder")

        mock_arm_file = pathlib.Path("arm_file.json")
        mock_puff_file = None
        mock_target_arm_parameters_file = pathlib.Path(
            "some.generated.puff.file.json"
        )

        (
            result_source_arm_template,
            result_target_arm_template,
            result_puff,
            result_parameters,
        ) = under_test.construct_deployment_paths(
            mock_arm_file,
            mock_puff_file,
            mock_target_arm_parameters_file,
        )

        assert result_source_arm_template == pathlib.Path(
            "frame/folder/arm_file.json"
        )
        assert result_puff == pathlib.Path("frame/folder/arm_file.yml")

        assert result_target_arm_template == pathlib.Path(
            "frame/folder/arm_file.json"
        )
        assert result_parameters == pathlib.Path(
            "frame/folder/some.generated.puff.file.json"
        )

    def test_independent_arm_file_puff_file(self, mock_flattened_deployment):
        under_test = copy.deepcopy(mock_flattened_deployment[0])
        under_test.context.application_name = "this_app"
        under_test.context.frame_name = "f1"
        under_test.data.frame_folder = pathlib.Path("frame/folder")

        mock_arm_file = pathlib.Path("arm_file.json")
        mock_puff_file = pathlib.Path("puff_file.yml")
        mock_target_arm_parameters_file = pathlib.Path("some.puff.file.json")

        (
            result_source_arm_template,
            result_target_arm_template,
            result_puff,
            result_parameters,
        ) = under_test.construct_deployment_paths(
            mock_arm_file,
            mock_puff_file,
            mock_target_arm_parameters_file,
        )

        assert result_source_arm_template == pathlib.Path(
            "frame/folder/arm_file.json"
        )
        assert result_puff == pathlib.Path("frame/folder/puff_file.yml")

        assert result_target_arm_template == pathlib.Path(
            "frame/folder/arm_file.json"
        )
        assert result_parameters == pathlib.Path(
            "frame/folder/some.puff.file.json"
        )
