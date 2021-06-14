#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with foodx_devops_tools.
#  If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import (
    SubscriptionsDefinitionError,
    load_subscriptions,
)


@pytest.fixture
def apply_subscriptions_test(apply_pipeline_config_test):
    def _apply(mock_content: str):
        result = apply_pipeline_config_test(mock_content, load_subscriptions)
        return result

    return _apply


def test_single(apply_subscriptions_test):
    file_text = """
---
subscriptions:
  name:
    locations:
      - loc1
      - loc2
    ado_service_connection: some-name
"""

    result = apply_subscriptions_test(file_text)

    assert len(result.subscriptions) == 1
    assert "name" in result.subscriptions
    assert result.subscriptions["name"].locations == ["loc1", "loc2"]
    assert result.subscriptions["name"].ado_service_connection == "some-name"


def test_multiple(apply_subscriptions_test):
    file_text = """
---
subscriptions:
  name1:
    locations:
      - loc1
      - loc2
    ado_service_connection: some-name
  name2:
    locations:
      - loc1
      - loc3
    ado_service_connection: some-name
  name3:
    locations:
      - loc1
      - loc3
      - loc4
    ado_service_connection: other-name
"""

    result = apply_subscriptions_test(file_text)

    assert len(result.subscriptions) == 3
    assert "name1" in result.subscriptions
    assert "name2" in result.subscriptions
    assert "name3" in result.subscriptions
    # Assume that name2 data is correct if name1, name3 are correct.
    assert result.subscriptions["name1"].locations == ["loc1", "loc2"]
    assert result.subscriptions["name1"].ado_service_connection == "some-name"
    assert result.subscriptions["name3"].locations == ["loc1", "loc3", "loc4"]
    assert result.subscriptions["name3"].ado_service_connection == "other-name"


def test_bad_field_raises(apply_subscriptions_test):
    file_text = """
---
subscriptions:
  name:
    bad_field:
      - loc1
      - loc2
    ado_service_connection: some-name
"""

    with pytest.raises(
        SubscriptionsDefinitionError,
        match=r"Error validating subscriptions definition",
    ):
        apply_subscriptions_test(file_text)


def test_none_raises(apply_subscriptions_test):
    file_text = """
---
"""

    with pytest.raises(
        SubscriptionsDefinitionError,
        match=r"Error validating subscriptions definition",
    ):
        apply_subscriptions_test(file_text)


def test_empty_list_raises(apply_subscriptions_test):
    file_text = """
---
subscriptions:
"""

    with pytest.raises(
        SubscriptionsDefinitionError,
        match=r"Error validating subscriptions definition",
    ):
        apply_subscriptions_test(file_text)
