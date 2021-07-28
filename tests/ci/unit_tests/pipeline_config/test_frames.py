#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with foodx_devops_tools.
#  If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import (
    FrameDefinitionsError,
    load_frames,
)


@pytest.fixture
def apply_applications_test(apply_pipeline_config_test):
    def _apply(mock_content: str):
        result = apply_pipeline_config_test(mock_content, load_frames)
        return result

    return _apply


def test_single_default(apply_applications_test):
    file_text = """---
frames:
  f1:
    applications:
      - a1
      - a2
"""

    result = apply_applications_test(file_text)

    assert len(result.frames) == 1
    assert result.frames["f1"].applications == ["a1", "a2"]


def test_multiple_sequenced(apply_applications_test):
    file_text = """---
frames:
  f1:
    applications:
      - a1
      - a2
  f2:
    applications:
      - a3
      - a4
    depends_on:
      - f1
"""

    result = apply_applications_test(file_text)

    assert len(result.frames) == 2
    assert result.frames["f1"].applications == ["a1", "a2"]
    assert result.frames["f2"].applications == ["a3", "a4"]


def test_multiple_unsequenced(apply_applications_test):
    file_text = """---
frames:
  f1:
    applications:
      - a1
      - a2
  f3:
    applications:
      - a5
      - a6
  f2:
    applications:
      - a3
      - a4
"""

    result = apply_applications_test(file_text)

    assert len(result.frames) == 3
    assert result.frames["f1"].applications == ["a1", "a2"]
    assert result.frames["f3"].applications == ["a5", "a6"]
    assert result.frames["f2"].applications == ["a3", "a4"]


def test_none_raises(apply_applications_test):
    file_text = """---
"""

    with pytest.raises(
        FrameDefinitionsError, match=r"Error validating frames definition"
    ):
        apply_applications_test(file_text)


def test_empty_raises(apply_applications_test):
    file_text = """---
frames:
"""

    with pytest.raises(
        FrameDefinitionsError, match=r"Error validating frames definition"
    ):
        apply_applications_test(file_text)


def test_bad_dependency_raises(apply_applications_test):
    file_text = """---
frames:
  f1:
    applications:
      - a1
      - a2
  f2:
    applications:
      - a3
      - a4
    depends_on:
      - bad_value
"""

    with pytest.raises(
        FrameDefinitionsError, match=r"Error validating frames definition"
    ):
        apply_applications_test(file_text)
