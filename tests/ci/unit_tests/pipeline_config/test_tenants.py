#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with foodx_devops_tools.
#  If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import load_tenants
from foodx_devops_tools.pipeline_config.exceptions import TenantsDefinitionError


@pytest.fixture
def apply_tenants_test(apply_pipeline_config_test):
    def _apply(mock_content: str):
        result = apply_pipeline_config_test(mock_content, load_tenants)
        return result

    return _apply


def test_single(apply_tenants_test):
    file_text = """---
tenants:
  name:
    azure_id: abc123
"""

    result = apply_tenants_test(file_text)

    assert len(result.tenants) == 1
    assert "name" in result.tenants
    assert result.tenants["name"].azure_id == "abc123"
    assert result.tenants["name"].azure_name is None


def test_name(apply_tenants_test):
    file_text = """---
tenants:
  name:
    azure_id: abc123
    azure_name: some name
"""

    result = apply_tenants_test(file_text)

    assert len(result.tenants) == 1
    assert "name" in result.tenants
    assert result.tenants["name"].azure_id == "abc123"
    assert result.tenants["name"].azure_name == "some name"


def test_multiple(apply_tenants_test):
    file_text = """---
tenants:
  name1:
    azure_id: abc123
  name2:
    azure_id: abc1234
  name3:
    azure_id: abc12345
"""

    result = apply_tenants_test(file_text)

    assert len(result.tenants) == 3
    assert all([x in result.tenants for x in ["name1", "name2", "name3"]])
    assert result.tenants["name1"].azure_id == "abc123"


def test_none_raises(apply_tenants_test):
    file_text = """---
"""

    with pytest.raises(
        TenantsDefinitionError,
        match=r"Error validating tenants definition",
    ):
        apply_tenants_test(file_text)


def test_empty_raises(apply_tenants_test):
    file_text = """---
tenants:
"""

    with pytest.raises(
        TenantsDefinitionError,
        match=r"Error validating tenants definition",
    ):
        apply_tenants_test(file_text)
