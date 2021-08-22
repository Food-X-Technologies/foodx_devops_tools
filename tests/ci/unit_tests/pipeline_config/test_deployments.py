#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with foodx_devops_tools.
#  If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import load_deployments
from foodx_devops_tools.pipeline_config.exceptions import (
    DeploymentsDefinitionError,
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
    subscriptions: 
      some-name:
        locations:
          - primary: ploc1
            secondary: sloc1
          - primary: ploc2
"""

    result = apply_deployments_test(file_text)

    assert len(result.deployments) == 1
    assert "name" in result.deployments
    assert "some-name" in result.deployments["name"].subscriptions
    assert (
        result.deployments["name"]
        .subscriptions["some-name"]
        .locations[0]
        .primary
        == "ploc1"
    )
    assert (
        result.deployments["name"]
        .subscriptions["some-name"]
        .locations[0]
        .secondary
        == "sloc1"
    )
    assert (
        result.deployments["name"]
        .subscriptions["some-name"]
        .locations[1]
        .primary
        == "ploc2"
    )


def test_multiple(apply_deployments_test):
    file_text = """
---
deployments:
  name1:
    subscriptions: 
      some-name:
        locations:
          - primary: loc1
          - primary: loc2
  name2:
    subscriptions: 
      some-name:
        locations:
          - primary: loc1
          - primary: loc3
  name3:
    subscriptions: 
      other-name:
        locations:
          - primary: loc1
          - primary: loc3
          - primary: loc4
"""

    result = apply_deployments_test(file_text)

    assert len(result.deployments) == 3
    assert "name1" in result.deployments
    assert "name2" in result.deployments
    assert "name3" in result.deployments
    # Assume that name2 data is correct if name1, name3 are correct.
    assert "some-name" in result.deployments["name1"].subscriptions
    assert "other-name" in result.deployments["name3"].subscriptions
    assert (
        result.deployments["name1"]
        .subscriptions["some-name"]
        .locations[0]
        .primary
        == "loc1"
    )
    assert (
        result.deployments["name1"]
        .subscriptions["some-name"]
        .locations[1]
        .primary
        == "loc2"
    )
    assert (
        result.deployments["name3"]
        .subscriptions["other-name"]
        .locations[0]
        .primary
        == "loc1"
    )
    assert (
        result.deployments["name3"]
        .subscriptions["other-name"]
        .locations[1]
        .primary
        == "loc3"
    )
    assert (
        result.deployments["name3"]
        .subscriptions["other-name"]
        .locations[2]
        .primary
        == "loc4"
    )


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
