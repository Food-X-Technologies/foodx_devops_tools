#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import (
    ServicePrincipals,
    load_service_principals,
)


@pytest.fixture
def apply_service_principals_test(apply_pipeline_config_test):
    def _apply(mock_content: str) -> ServicePrincipals:
        result = apply_pipeline_config_test(
            mock_content, load_service_principals
        )
        return result

    return _apply


def test_simple(apply_service_principals_test):
    file_text = """
---
service_principals:
  sub1_name:
    id: 12345-id
    name: principal-name1
    secret: verysecret
  sub2_name:
    id: 123456-id
    name: principal-name2
    secret: verysecret
"""

    result = apply_service_principals_test(file_text)

    assert len(result.service_principals) == 2
    assert result.service_principals["sub1_name"].id == "12345-id"
    assert result.service_principals["sub1_name"].name == "principal-name1"
    assert result.service_principals["sub1_name"].secret == "verysecret"

    assert result.service_principals["sub2_name"].id == "123456-id"
