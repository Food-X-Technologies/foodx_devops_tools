#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy
import pathlib

import pytest

from foodx_devops_tools.pipeline_config.views import FlattenedDeployment
from foodx_devops_tools.utilities.templates import (
    ArmTemplateParameters,
    ArmTemplates,
    TemplateFiles,
)


@pytest.fixture()
def mock_test_data(mock_flattened_deployment):
    under_test = copy.deepcopy(mock_flattened_deployment[0])
    under_test.context.application_name = "this_app"
    under_test.context.frame_name = "f1"
    under_test.data.frame_folder = pathlib.Path("frame/folder")

    return copy.deepcopy(under_test)


class TestConstructDeploymentPaths:
    MOCK_CONTEXT = "some_context"

    def _do_check(self, parameters: dict, under_test: FlattenedDeployment):
        labels = [
            "source_arm_template",
            "target_arm_template",
            "puff",
            "arm_parameters",
        ]
        result = under_test.construct_deployment_paths(*parameters["input"])

        assert result == parameters["expected"]

    def test_none_arm_file_puff_file(self, mock_test_data):
        parameters = {
            "input": [
                # arm_file
                None,
                # puff_file
                None,
                # target_arm_parameters_file
                pathlib.Path("some/arm_parameters.json"),
            ],
            "expected": TemplateFiles(
                arm_template=ArmTemplates(
                    source=pathlib.Path("frame/folder/this_app.json"),
                    target=pathlib.Path("frame/folder/this_app.json"),
                ),
                arm_template_parameters=ArmTemplateParameters(
                    source_puff=pathlib.Path("frame/folder/this_app.yml"),
                    templated_puff=pathlib.Path("frame/folder/this_app.yml"),
                    target=pathlib.Path(
                        "frame/folder/some/arm_parameters.json"
                    ),
                ),
            ),
        }

        self._do_check(parameters, mock_test_data)

    def test_arm_file_none_puff_file(self, mock_test_data):
        parameters = {
            "input": [
                # arm_file
                pathlib.Path("arm_file.json"),
                # puff_file
                None,
                # target_arm_parameters_file
                pathlib.Path("some.generated.puff.file.json"),
            ],
            "expected": TemplateFiles(
                arm_template=ArmTemplates(
                    source=pathlib.Path("frame/folder/arm_file.json"),
                    target=pathlib.Path("frame/folder/arm_file.json"),
                ),
                arm_template_parameters=ArmTemplateParameters(
                    source_puff=pathlib.Path("frame/folder/arm_file.yml"),
                    templated_puff=pathlib.Path("frame/folder/arm_file.yml"),
                    target=pathlib.Path(
                        "frame/folder/some.generated.puff.file.json"
                    ),
                ),
            ),
        }

        self._do_check(parameters, mock_test_data)

    def test_pathed_arm_file_none_puff_file(self, mock_test_data):
        parameters = {
            "input": [
                # arm_file
                pathlib.Path("sub/arm_file.json"),
                # puff_file
                None,
                # target_arm_parameters_file
                pathlib.Path("some.generated.puff.file.json"),
            ],
            "expected": TemplateFiles(
                arm_template=ArmTemplates(
                    source=pathlib.Path("frame/folder/sub/arm_file.json"),
                    target=pathlib.Path("frame/folder/sub/arm_file.json"),
                ),
                arm_template_parameters=ArmTemplateParameters(
                    source_puff=pathlib.Path("frame/folder/sub/arm_file.yml"),
                    templated_puff=pathlib.Path(
                        "frame/folder/sub/arm_file.yml"
                    ),
                    target=pathlib.Path(
                        "frame/folder/some.generated.puff.file.json"
                    ),
                ),
            ),
        }

        self._do_check(parameters, mock_test_data)

    def test_pathed_arm_parameters_file(self, mock_test_data):
        parameters = {
            "input": [
                # arm_file
                None,
                # puff_file
                None,
                # target_arm_parameters_file
                pathlib.Path("sub/some.generated.puff.file.json"),
            ],
            "expected": TemplateFiles(
                arm_template=ArmTemplates(
                    source=pathlib.Path("frame/folder/this_app.json"),
                    target=pathlib.Path("frame/folder/this_app.json"),
                ),
                arm_template_parameters=ArmTemplateParameters(
                    source_puff=pathlib.Path("frame/folder/this_app.yml"),
                    templated_puff=pathlib.Path("frame/folder/this_app.yml"),
                    target=pathlib.Path(
                        "frame/folder/sub/some.generated.puff.file.json"
                    ),
                ),
            ),
        }

        self._do_check(parameters, mock_test_data)

    def test_independent_arm_file_puff_file(self, mock_test_data):
        parameters = {
            "input": [
                # arm_file
                pathlib.Path("arm_file.json"),
                # puff_file
                pathlib.Path("puff_file.yml"),
                # target_arm_parameters_file
                pathlib.Path("some.puff.file.json"),
            ],
            "expected": TemplateFiles(
                arm_template=ArmTemplates(
                    source=pathlib.Path("frame/folder/arm_file.json"),
                    target=pathlib.Path("frame/folder/arm_file.json"),
                ),
                arm_template_parameters=ArmTemplateParameters(
                    source_puff=pathlib.Path("frame/folder/puff_file.yml"),
                    templated_puff=pathlib.Path("frame/folder/puff_file.yml"),
                    target=pathlib.Path("frame/folder/some.puff.file.json"),
                ),
            ),
        }

        self._do_check(parameters, mock_test_data)

    def test_pathed_independent_arm_file_puff_file(self, mock_test_data):
        parameters = {
            "input": [
                # arm_file
                pathlib.Path("arm_file.json"),
                # puff_file
                pathlib.Path("puff/puff_file.yml"),
                # target_arm_parameters_file
                pathlib.Path("some.puff.file.json"),
            ],
            "expected": TemplateFiles(
                arm_template=ArmTemplates(
                    source=pathlib.Path("frame/folder/arm_file.json"),
                    target=pathlib.Path("frame/folder/arm_file.json"),
                ),
                arm_template_parameters=ArmTemplateParameters(
                    source_puff=pathlib.Path("frame/folder/puff/puff_file.yml"),
                    templated_puff=pathlib.Path(
                        "frame/folder/puff/puff_file.yml"
                    ),
                    target=pathlib.Path("frame/folder/some.puff.file.json"),
                ),
            ),
        }

        self._do_check(parameters, mock_test_data)

    def test_out_of_frame_nonjinja_arm_file(self, mock_test_data):
        parameters = {
            "input": [
                # arm_file
                pathlib.Path("../common/files/arm_file.json"),
                # puff_file
                pathlib.Path("puff_file.yml"),
                # target_arm_parameters_file
                pathlib.Path("some.puff.file.json"),
            ],
            "expected": TemplateFiles(
                arm_template=ArmTemplates(
                    source=pathlib.Path(
                        "frame/folder/../common/files/arm_file.json"
                    ),
                    target=pathlib.Path(
                        "frame/folder/../common/files/arm_file.json"
                    ),
                ),
                arm_template_parameters=ArmTemplateParameters(
                    source_puff=pathlib.Path("frame/folder/puff_file.yml"),
                    templated_puff=pathlib.Path("frame/folder/puff_file.yml"),
                    target=pathlib.Path("frame/folder/some.puff.file.json"),
                ),
            ),
        }

        self._do_check(parameters, mock_test_data)

    def test_out_of_frame_jinja_arm_file(self, mock_test_data):
        parameters = {
            "input": [
                # arm_file
                pathlib.Path("../common/files/jinja2.arm_file.json"),
                # puff_file
                pathlib.Path("puff_file.yml"),
                # target_arm_parameters_file
                pathlib.Path("some.puff.file.json"),
            ],
            "expected": TemplateFiles(
                arm_template=ArmTemplates(
                    source=pathlib.Path(
                        "frame/folder/../common/files/jinja2.arm_file.json"
                    ),
                    target=pathlib.Path("frame/folder/arm_file.json"),
                ),
                arm_template_parameters=ArmTemplateParameters(
                    source_puff=pathlib.Path("frame/folder/puff_file.yml"),
                    templated_puff=pathlib.Path("frame/folder/puff_file.yml"),
                    target=pathlib.Path("frame/folder/some.puff.file.json"),
                ),
            ),
        }

        self._do_check(parameters, mock_test_data)

    def test_out_of_frame_nonjinja_puff_file(self, mock_test_data):
        parameters = {
            "input": [
                # arm_file
                None,
                # puff_file
                pathlib.Path("../common/files/puff_file.yml"),
                # target_arm_parameters_file
                pathlib.Path("some.puff.file.json"),
            ],
            "expected": TemplateFiles(
                arm_template=ArmTemplates(
                    source=pathlib.Path("frame/folder/this_app.json"),
                    target=pathlib.Path("frame/folder/this_app.json"),
                ),
                arm_template_parameters=ArmTemplateParameters(
                    source_puff=pathlib.Path(
                        "frame/folder/../common/files/puff_file.yml"
                    ),
                    templated_puff=pathlib.Path(
                        "frame/folder/../common/files/puff_file.yml"
                    ),
                    target=pathlib.Path("frame/folder/some.puff.file.json"),
                ),
            ),
        }

        self._do_check(parameters, mock_test_data)

    def test_out_of_frame_jinja_puff_file(self, mock_test_data):
        parameters = {
            "input": [
                # arm_file
                None,
                # puff_file
                pathlib.Path("../common/files/jinja2.puff_file.yml"),
                # target_arm_parameters_file
                pathlib.Path("some.puff.file.json"),
            ],
            "expected": TemplateFiles(
                arm_template=ArmTemplates(
                    source=pathlib.Path("frame/folder/this_app.json"),
                    target=pathlib.Path("frame/folder/this_app.json"),
                ),
                arm_template_parameters=ArmTemplateParameters(
                    source_puff=pathlib.Path(
                        "frame/folder/../common/files/jinja2.puff_file.yml"
                    ),
                    templated_puff=pathlib.Path(
                        "frame/folder/../common/files/puff_file.yml"
                    ),
                    target=pathlib.Path("frame/folder/some.puff.file.json"),
                ),
            ),
        }

        self._do_check(parameters, mock_test_data)

    def test_pathed_jinja_puff_file(self, mock_test_data):
        parameters = {
            "input": [
                # arm_file
                None,
                # puff_file
                pathlib.Path("sub/jinja2.puff_file.yml"),
                # target_arm_parameters_file
                pathlib.Path("some.puff.file.json"),
            ],
            "expected": TemplateFiles(
                arm_template=ArmTemplates(
                    source=pathlib.Path("frame/folder/this_app.json"),
                    target=pathlib.Path("frame/folder/this_app.json"),
                ),
                arm_template_parameters=ArmTemplateParameters(
                    source_puff=pathlib.Path(
                        "frame/folder/sub/jinja2.puff_file.yml"
                    ),
                    templated_puff=pathlib.Path(
                        "frame/folder/sub/puff_file.yml"
                    ),
                    target=pathlib.Path("frame/folder/some.puff.file.json"),
                ),
            ),
        }

        self._do_check(parameters, mock_test_data)
