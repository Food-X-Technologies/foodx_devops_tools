#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with foodx_devops_tools.
#  If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import (
    DeploymentsDefinitionError,
    load_deployments,
)


@pytest.fixture
def apply_deployments_test(apply_pipeline_config_test):
    def _apply(mock_content: str):
        result = apply_pipeline_config_test(mock_content, load_deployments)
        return result

    return _apply


def test_single(apply_deployments_test):
    file_text = """
---
deployments:
  name:
    locations:
      - loc1
      - loc2
    subscription: some-name
"""

    result = apply_deployments_test(file_text)

    assert len(result.deployments) == 1
    assert "name" in result.deployments
    assert result.deployments["name"].locations == ["loc1", "loc2"]
    assert result.deployments["name"].subscription == "some-name"


def test_multiple(apply_deployments_test):
    file_text = """
---
deployments:
  name1:
    locations:
      - loc1
      - loc2
    subscription: some-name
  name2:
    locations:
      - loc1
      - loc3
    subscription: some-name
  name3:
    locations:
      - loc1
      - loc3
      - loc4
    subscription: other-name
"""

    result = apply_deployments_test(file_text)

    assert len(result.deployments) == 3
    assert "name1" in result.deployments
    assert "name2" in result.deployments
    assert "name3" in result.deployments
    # Assume that name2 data is correct if name1, name3 are correct.
    assert result.deployments["name1"].locations == ["loc1", "loc2"]
    assert result.deployments["name1"].subscription == "some-name"
    assert result.deployments["name3"].locations == ["loc1", "loc3", "loc4"]
    assert result.deployments["name3"].subscription == "other-name"


def test_bad_field_raises(apply_deployments_test):
    file_text = """
---
deployments:
  name:
    bad_field:
      - loc1
      - loc2
    subscription: some-name
"""

    with pytest.raises(
        DeploymentsDefinitionError,
        match=r"Error validating deployments definition",
    ):
        apply_deployments_test(file_text)


def test_none_raises(apply_deployments_test):
    file_text = """
---
"""

    with pytest.raises(
        DeploymentsDefinitionError,
        match=r"Error validating deployments definition",
    ):
        apply_deployments_test(file_text)


def test_empty_list_raises(apply_deployments_test):
    file_text = """
---
deployments:
"""

    with pytest.raises(
        DeploymentsDefinitionError,
        match=r"Error validating deployments definition",
    ):
        apply_deployments_test(file_text)
