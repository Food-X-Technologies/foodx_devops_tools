#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with foodx_devops_tools.
#  If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import load_release_states
from foodx_devops_tools.pipeline_config.exceptions import (
    ReleaseStatesDefinitionError,
)


@pytest.fixture
def apply_release_states_test(apply_pipeline_config_test):
    def _apply(mock_content: str):
        result = apply_pipeline_config_test(mock_content, load_release_states)
        return result

    return _apply


def test_single(apply_release_states_test):
    file_text = """
---
release_states:
  - name
"""

    result = apply_release_states_test(file_text)

    assert len(result.release_states) == 1
    assert result.release_states[0] == "name"


def test_multiple(apply_release_states_test):
    file_text = """
---
release_states:
  - name1
  - name2
  - name3
"""

    result = apply_release_states_test(file_text)

    assert len(result.release_states) == 3
    assert result.release_states[0] == "name1"
    assert result.release_states[1] == "name2"
    assert result.release_states[2] == "name3"


def test_duplicate_raises(apply_release_states_test):
    file_text = """
---
release_states:
  - name
  - name
"""

    with pytest.raises(
        ReleaseStatesDefinitionError,
        match=r"Error validating release states definition",
    ):
        apply_release_states_test(file_text)


def test_none_raises(apply_release_states_test):
    file_text = """
---
"""

    with pytest.raises(
        ReleaseStatesDefinitionError,
        match=r"Error validating release states definition",
    ):
        apply_release_states_test(file_text)


def test_empty_list_raises(apply_release_states_test):
    file_text = """
---
release_states:
"""

    with pytest.raises(
        ReleaseStatesDefinitionError,
        match=r"Error validating release states definition",
    ):
        apply_release_states_test(file_text)
