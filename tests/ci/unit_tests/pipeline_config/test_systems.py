#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with foodx_devops_tools.
#  If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import load_systems
from foodx_devops_tools.pipeline_config.exceptions import SystemsDefinitionError


@pytest.fixture
def apply_systems_test(apply_pipeline_config_test):
    def _apply(mock_content: str):
        result = apply_pipeline_config_test(mock_content, load_systems)
        return result

    return _apply


def test_single(apply_systems_test):
    file_text = """
---
systems:
  - name
"""

    result = apply_systems_test(file_text)

    assert len(result.systems) == 1
    assert result.systems[0] == "name"


def test_multiple(apply_systems_test):
    file_text = """
---
systems:
  - name1
  - name2
  - name3
"""

    result = apply_systems_test(file_text)

    assert len(result.systems) == 3
    assert result.systems[0] == "name1"
    assert result.systems[1] == "name2"
    assert result.systems[2] == "name3"


def test_duplicate_raises(apply_systems_test):
    file_text = """
---
systems:
  - name
  - name
"""

    with pytest.raises(
        SystemsDefinitionError, match=r"Error validating systems definition"
    ):
        apply_systems_test(file_text)


def test_none_raises(apply_systems_test):
    file_text = """
---
"""

    with pytest.raises(
        SystemsDefinitionError, match=r"Error validating systems definition"
    ):
        apply_systems_test(file_text)


def test_empty_list_raises(apply_systems_test):
    file_text = """
---
systems:
"""

    with pytest.raises(
        SystemsDefinitionError, match=r"Error validating systems definition"
    ):
        apply_systems_test(file_text)
