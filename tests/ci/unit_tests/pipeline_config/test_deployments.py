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
  deployment_tuples:
    name:
      subscriptions: 
        some-name:
          locations:
            - primary: ploc1
              secondary: sloc1
            - primary: ploc2
          root_fqdn: some.where
  url_endpoints: ["a","b"]
"""

    result = apply_deployments_test(file_text)

    assert len(result.deployments.deployment_tuples) == 1
    assert "name" in result.deployments.deployment_tuples
    assert (
        "some-name"
        in result.deployments.deployment_tuples["name"].subscriptions
    )
    assert (
        result.deployments.deployment_tuples["name"]
        .subscriptions["some-name"]
        .locations[0]
        .primary
        == "ploc1"
    )
    assert (
        result.deployments.deployment_tuples["name"]
        .subscriptions["some-name"]
        .locations[0]
        .secondary
        == "sloc1"
    )
    assert (
        result.deployments.deployment_tuples["name"]
        .subscriptions["some-name"]
        .locations[1]
        .primary
        == "ploc2"
    )
    assert (
        result.deployments.deployment_tuples["name"]
        .subscriptions["some-name"]
        .root_fqdn
        == "some.where"
    )
    assert result.deployments.url_endpoints == ["a", "b"]


def test_multiple(apply_deployments_test):
    file_text = """
---
deployments:
  deployment_tuples:
    name1:
      subscriptions: 
        some-name:
          locations:
            - primary: loc1
            - primary: loc2
          root_fqdn: some.where
    name2:
      subscriptions: 
        some-name:
          locations:
            - primary: loc1
            - primary: loc3
          root_fqdn: some.where
    name3:
      subscriptions: 
        other-name:
          locations:
            - primary: loc1
            - primary: loc3
            - primary: loc4
          root_fqdn: some.where
  url_endpoints: ["a","b"]
"""

    result = apply_deployments_test(file_text)

    assert len(result.deployments.deployment_tuples) == 3
    assert "name1" in result.deployments.deployment_tuples
    assert "name2" in result.deployments.deployment_tuples
    assert "name3" in result.deployments.deployment_tuples
    # Assume that name2 data is correct if name1, name3 are correct.
    assert (
        "some-name"
        in result.deployments.deployment_tuples["name1"].subscriptions
    )
    assert (
        "other-name"
        in result.deployments.deployment_tuples["name3"].subscriptions
    )
    assert (
        result.deployments.deployment_tuples["name1"]
        .subscriptions["some-name"]
        .locations[0]
        .primary
        == "loc1"
    )
    assert (
        result.deployments.deployment_tuples["name1"]
        .subscriptions["some-name"]
        .locations[1]
        .primary
        == "loc2"
    )
    assert (
        result.deployments.deployment_tuples["name1"]
        .subscriptions["some-name"]
        .root_fqdn
        == "some.where"
    )
    assert (
        result.deployments.deployment_tuples["name3"]
        .subscriptions["other-name"]
        .locations[0]
        .primary
        == "loc1"
    )
    assert (
        result.deployments.deployment_tuples["name3"]
        .subscriptions["other-name"]
        .locations[1]
        .primary
        == "loc3"
    )
    assert (
        result.deployments.deployment_tuples["name3"]
        .subscriptions["other-name"]
        .locations[2]
        .primary
        == "loc4"
    )


def test_bad_field_raises(apply_deployments_test):
    file_text = """
---
deployments:
  deployment_tuples:
    name:
      bad_field:
        - loc1
        - loc2
      subscription: some-name
  url_endpoints: ["a","b"]
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
  deployment_tuples:
  url_endpoints: ["a","b"]
"""

    with pytest.raises(
        DeploymentsDefinitionError,
        match=r"Error validating deployments definition",
    ):
        apply_deployments_test(file_text)


def test_branch_option_absent(apply_deployments_test):
    file_text = """
---
deployments:
  deployment_tuples:
    name:
      subscriptions: 
        some-name:
          locations:
            - primary: ploc1
              secondary: sloc1
            - primary: ploc2
          root_fqdn: some.where
  url_endpoints: ["a","b"]
"""

    result = apply_deployments_test(file_text)

    assert (
        result.deployments.deployment_tuples["name"]
        .subscriptions["some-name"]
        .gitref_patterns
        is None
    )


def test_branch_option_present(apply_deployments_test):
    file_text = """
---
deployments:
  deployment_tuples:
    name:
      subscriptions: 
        some-name:
          gitref_patterns:
            - main
          locations:
            - primary: ploc1
              secondary: sloc1
            - primary: ploc2
          root_fqdn: some.where
  url_endpoints: ["a","b"]
"""

    result = apply_deployments_test(file_text)

    assert (
        len(
            result.deployments.deployment_tuples["name"]
            .subscriptions["some-name"]
            .gitref_patterns
        )
        == 1
    )
    assert (
        result.deployments.deployment_tuples["name"]
        .subscriptions["some-name"]
        .gitref_patterns[0]
        == "main"
    )
