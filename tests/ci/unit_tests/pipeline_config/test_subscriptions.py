#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with foodx_devops_tools.
#  If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import load_subscriptions
from foodx_devops_tools.pipeline_config.exceptions import (
    SubscriptionsDefinitionError,
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
    ado_service_connection: some-name
    azure_id: abc123
    tenant: 123abc
"""

    result = apply_subscriptions_test(file_text)

    assert len(result.subscriptions) == 1
    assert "name" in result.subscriptions
    assert result.subscriptions["name"].ado_service_connection == "some-name"
    assert result.subscriptions["name"].azure_id == "abc123"
    assert result.subscriptions["name"].tenant == "123abc"


def test_ado_default(apply_subscriptions_test):
    file_text = """
---
subscriptions:
  name:
    azure_id: abc123
    tenant: tname
"""

    result = apply_subscriptions_test(file_text)

    assert len(result.subscriptions) == 1
    assert "name" in result.subscriptions
    assert result.subscriptions["name"].ado_service_connection is None
    assert result.subscriptions["name"].azure_id == "abc123"
    assert result.subscriptions["name"].tenant == "tname"


def test_multiple(apply_subscriptions_test):
    file_text = """
---
subscriptions:
  name1:
    azure_id: abc123
    tenant: tname1
  name2:
    azure_id: abc1234
    tenant: tname2
  name3:
    azure_id: abc12345
    tenant: tname3
"""

    result = apply_subscriptions_test(file_text)

    assert len(result.subscriptions) == 3
    assert all([x in result.subscriptions for x in ["name1", "name2", "name3"]])
    assert result.subscriptions["name1"].azure_id == "abc123"
    assert result.subscriptions["name3"].azure_id == "abc12345"


def test_none_raises(apply_subscriptions_test):
    file_text = """
---
"""

    with pytest.raises(
        SubscriptionsDefinitionError,
        match=r"Error validating subscriptions definition",
    ):
        apply_subscriptions_test(file_text)


def test_empty_raises(apply_subscriptions_test):
    file_text = """
---
subscriptions:
"""

    with pytest.raises(
        SubscriptionsDefinitionError,
        match=r"Error validating subscriptions definition",
    ):
        apply_subscriptions_test(file_text)
