#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

import pytest

from foodx_devops_tools.utilities.templates import (
    TemplateFiles,
    TemplatePaths,
    _apply_template,
    _construct_arm_template_parameter_paths,
    json_inlining,
    prepare_deployment_files,
)


@pytest.fixture()
def mock_run(mock_async_method, mocker):
    mock_puff = mock_async_method(
        "foodx_devops_tools.utilities.templates.run_puff"
    )
    mock_template = mock_async_method(
        "foodx_devops_tools.utilities.templates.FrameTemplates"
        ".apply_template"
    )
    mocker.patch("pathlib.Path.is_file", return_value=True)

    return mock_puff, mock_template


class TestPrepareArmTemplateParameterPaths:
    def test_clean(self):
        mock_data = TemplatePaths(
            source=pathlib.Path("source/puff/file.yml"),
            target=pathlib.Path("target/json/file.json"),
        )

        result = _construct_arm_template_parameter_paths(mock_data)

        assert (
            result == mock_data.target.parent / f"jinjad."
            f"{mock_data.target.name}"
        )


class TestPrepareDeploymentFiles:
    MOCK_PARAMETERS = {
        "k1": "v1",
        "k2": "v2",
    }

    @pytest.mark.asyncio
    async def test_clean(self, mock_run):
        mock_path = pathlib.Path("some/file")
        mock_templates = TemplateFiles(
            arm_template=TemplatePaths(
                source=mock_path,
                target=mock_path,
            ),
            arm_template_parameters=TemplatePaths(
                source=mock_path,
                target=mock_path,
            ),
        )
        mock_puff, _ = mock_run

        result = await prepare_deployment_files(
            mock_templates, self.MOCK_PARAMETERS
        )

        assert result.arm_template == mock_path
        assert result.parameters == pathlib.Path("some/jinjad.file")
        mock_puff.assert_called_once_with(
            mock_path,
            False,
            False,
            disable_ascii_art=True,
            output_dir=pathlib.Path("some"),
        )

    @pytest.mark.asyncio
    async def test_jinja2_puff(self, mock_run, mocker):
        mock_puff, mock_template = mock_run
        mock_templates = TemplateFiles(
            arm_template=TemplatePaths(
                source=pathlib.Path("some/source/file"),
                target=pathlib.Path("some/target/file"),
            ),
            arm_template_parameters=TemplatePaths(
                source=pathlib.Path("some/path.yml"),
                target=pathlib.Path("some/target/generated.json"),
            ),
        )

        result = await prepare_deployment_files(
            mock_templates,
            self.MOCK_PARAMETERS,
        )

        assert result.arm_template == mock_templates.arm_template.target
        assert result.parameters == pathlib.Path(
            "some/target/jinjad.generated.json"
        )
        mock_puff.assert_called_once_with(
            mock_templates.arm_template_parameters.source,
            False,
            False,
            disable_ascii_art=True,
            output_dir=pathlib.Path("some/target"),
        )
        mock_template.assert_has_calls(
            [
                mocker.call(
                    mock_templates.arm_template_parameters.target.name,
                    pathlib.Path("some/target/jinjad.generated.json"),
                    self.MOCK_PARAMETERS,
                ),
                mocker.call(
                    mock_templates.arm_template.source.name,
                    mock_templates.arm_template.target,
                    self.MOCK_PARAMETERS,
                ),
            ],
            any_order=True,
        )

    @pytest.mark.asyncio
    async def test_jinja2_arm(self, mock_run, mocker):
        mock_puff, mock_template = mock_run
        mock_templates = TemplateFiles(
            arm_template=TemplatePaths(
                source=pathlib.Path("some/jinja2.path"),
                target=pathlib.Path("some/target/path"),
            ),
            arm_template_parameters=TemplatePaths(
                source=pathlib.Path("some/path.yml"),
                target=pathlib.Path("some/target/generated.json"),
            ),
        )

        result = await prepare_deployment_files(
            mock_templates,
            self.MOCK_PARAMETERS,
        )

        assert result.arm_template == mock_templates.arm_template.target
        assert result.parameters == pathlib.Path(
            "some/target/jinjad.generated.json"
        )
        mock_puff.assert_called_once_with(
            mock_templates.arm_template_parameters.source,
            False,
            False,
            disable_ascii_art=True,
            output_dir=pathlib.Path("some/target"),
        )
        mock_template.assert_has_calls(
            [
                mocker.call(
                    mock_templates.arm_template_parameters.target.name,
                    pathlib.Path("some/target/jinjad.generated.json"),
                    self.MOCK_PARAMETERS,
                ),
                mocker.call(
                    mock_templates.arm_template.source.name,
                    mock_templates.arm_template.target,
                    self.MOCK_PARAMETERS,
                ),
            ],
            any_order=True,
        )
