#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib
import pathlib
import tempfile
import typing

import pytest
import ruamel.yaml

from foodx_devops_tools.utilities.jinja2 import FrameTemplates

MOCK_TEMPLATE = """---
this_field: {{ this_parameter }}
"""


@contextlib.contextmanager
def mock_template_dir(
    template_content: str,
    template_name: str = "mock_template",
) -> typing.Generator[pathlib.Path, None, None]:
    with tempfile.TemporaryDirectory() as dir:
        this_dir = pathlib.Path(dir)
        template_file = this_dir / template_name

        with template_file.open(mode="w") as f:
            f.write(template_content)

        yield template_file


def load_yaml(file: pathlib.Path) -> dict:
    yaml = ruamel.yaml.YAML(typ="safe")
    with file.open("r") as f:
        result = yaml.load(f)

    return result


@pytest.mark.asyncio
async def test_clean():
    parameters = {"this_parameter": "this_value"}
    with mock_template_dir(MOCK_TEMPLATE) as template_file_path:
        target_file = template_file_path.parent / "this_target"

        assert not target_file.is_file()

        under_test = FrameTemplates([template_file_path.parent])
        await under_test.apply_template(
            "mock_template", target_file, parameters
        )

        assert target_file.is_file()
        target_data = load_yaml(target_file)
        assert target_data == {"this_field": "this_value"}
