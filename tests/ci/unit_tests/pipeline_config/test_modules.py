#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with foodx_devops_tools.
#  If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import (
    ModuleDefinitionsError,
    load_modules,
)


@pytest.fixture
def apply_applications_test(apply_pipeline_config_test):
    def _apply(mock_content: str):
        result = apply_pipeline_config_test(mock_content, load_modules)
        return result

    return _apply


def test_single_default(apply_applications_test):
    file_text = """---
modules:
  - a1:
      applications:
        - m1
        - m2
"""

    result = apply_applications_test(file_text)

    assert len(result.modules) == 1
    assert result.modules[0]["a1"].applications == ["m1", "m2"]


def test_multiple_sequenced(apply_applications_test):
    file_text = """---
modules:
  - a1:
      applications:
        - m1
        - m2
  - a2:
      applications:
        - m3
        - m4
"""

    result = apply_applications_test(file_text)

    assert len(result.modules) == 2
    assert result.modules[0]["a1"].applications == ["m1", "m2"]
    assert result.modules[1]["a2"].applications == ["m3", "m4"]


def test_multiple_unsequenced(apply_applications_test):
    file_text = """---
modules:
  - a1:
      applications:
        - m1
        - m2
    a3:
      applications:
        - m5
        - m6
  - a2:
      applications:
        - m3
        - m4
"""

    result = apply_applications_test(file_text)

    assert len(result.modules) == 2
    assert result.modules[0]["a1"].applications == ["m1", "m2"]
    assert result.modules[0]["a3"].applications == ["m5", "m6"]
    assert result.modules[1]["a2"].applications == ["m3", "m4"]


def test_none_raises(apply_applications_test):
    file_text = """---
"""

    with pytest.raises(
        ModuleDefinitionsError, match=r"Error validating modules definition"
    ):
        apply_applications_test(file_text)


def test_empty_raises(apply_applications_test):
    file_text = """---
modules:
"""

    with pytest.raises(
        ModuleDefinitionsError, match=r"Error validating modules definition"
    ):
        apply_applications_test(file_text)
