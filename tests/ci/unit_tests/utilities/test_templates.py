#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

import pytest

from foodx_devops_tools.utilities.templates import (
    ArmTemplateParameters,
    ArmTemplates,
    TemplateFiles,
    prepare_deployment_files,
)


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
        mock_templates = TemplateFiles(
            arm_template=ArmTemplates(
                source=mock_path,
                target=mock_path,
            ),
            arm_template_parameters=ArmTemplateParameters(
                source_puff=mock_path,
                templated_puff=mock_path,
                target=mock_path,
            ),
        )
        mock_puff, _ = mock_run

        result = await prepare_deployment_files(
            mock_templates, self.MOCK_PARAMETERS
        )

        assert result.arm_template == mock_path
        assert result.parameters == mock_path
        mock_puff.assert_called_once_with(
            mock_path,
            False,
            False,
            disable_ascii_art=True,
            output_dir=pathlib.Path("some"),
        )

    @pytest.mark.asyncio
    async def test_jinja2_puff(self, mock_run):
        mock_puff, mock_template = mock_run
        mock_templates = TemplateFiles(
            arm_template=ArmTemplates(
                source=pathlib.Path("some/source/file"),
                target=pathlib.Path("some/source/file"),
            ),
            arm_template_parameters=ArmTemplateParameters(
                source_puff=pathlib.Path("some/jinja2.path.yml"),
                templated_puff=pathlib.Path("some/target/path.yml"),
                target=pathlib.Path("some/target/generated.json"),
            ),
        )

        result = await prepare_deployment_files(
            mock_templates,
            self.MOCK_PARAMETERS,
        )

        assert result.arm_template == mock_templates.arm_template.target
        assert (
            result.parameters == mock_templates.arm_template_parameters.target
        )
        mock_puff.assert_called_once_with(
            mock_templates.arm_template_parameters.templated_puff,
            False,
            False,
            disable_ascii_art=True,
            output_dir=pathlib.Path("some/target"),
        )
        mock_template.assert_called_once_with(
            mock_templates.arm_template_parameters.source_puff.name,
            mock_templates.arm_template_parameters.templated_puff,
            self.MOCK_PARAMETERS,
        )

    @pytest.mark.asyncio
    async def test_jinja2_arm(self, mock_run):
        mock_puff, mock_template = mock_run
        mock_templates = TemplateFiles(
            arm_template=ArmTemplates(
                source=pathlib.Path("some/jinja2.path"),
                target=pathlib.Path("some/target/path"),
            ),
            arm_template_parameters=ArmTemplateParameters(
                source_puff=pathlib.Path("some/path.yml"),
                templated_puff=pathlib.Path("some/path.yml"),
                target=pathlib.Path("some/target/generated.json"),
            ),
        )

        result = await prepare_deployment_files(
            mock_templates,
            self.MOCK_PARAMETERS,
        )

        assert result.arm_template == mock_templates.arm_template.target
        assert (
            result.parameters == mock_templates.arm_template_parameters.target
        )
        mock_puff.assert_called_once_with(
            mock_templates.arm_template_parameters.templated_puff,
            False,
            False,
            disable_ascii_art=True,
            output_dir=pathlib.Path("some/target"),
        )
        mock_template.assert_called_once_with(
            mock_templates.arm_template.source.name,
            mock_templates.arm_template.target,
            self.MOCK_PARAMETERS,
        )
