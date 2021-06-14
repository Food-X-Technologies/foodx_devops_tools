#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with foodx_devops_tools.
#  If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import (
    ClientsDefinitionError,
    load_clients,
)


@pytest.fixture
def apply_clients_test(apply_pipeline_config_test):
    def _apply(mock_content: str):
        result = apply_pipeline_config_test(mock_content, load_clients)
        return result

    return _apply


def test_single(apply_clients_test):
    file_text = """
---
clients:
  - name
"""

    result = apply_clients_test(file_text)

    assert len(result.clients) == 1
    assert result.clients[0] == "name"


def test_multiple(apply_clients_test):
    file_text = """
---
clients:
  - name1
  - name2
  - name3
"""

    result = apply_clients_test(file_text)

    assert len(result.clients) == 3
    assert result.clients[0] == "name1"
    assert result.clients[1] == "name2"
    assert result.clients[2] == "name3"


def test_duplicate_raises(apply_clients_test):
    file_text = """
---
clients:
  - name
  - name
"""

    with pytest.raises(
        ClientsDefinitionError, match=r"Error validating clients definition"
    ):
        apply_clients_test(file_text)


def test_none_raises(apply_clients_test):
    file_text = """
---
"""

    with pytest.raises(
        ClientsDefinitionError, match=r"Error validating clients definition"
    ):
        apply_clients_test(file_text)


def test_empty_list_raises(apply_clients_test):
    file_text = """
---
clients:
"""

    with pytest.raises(
        ClientsDefinitionError, match=r"Error validating clients definition"
    ):
        apply_clients_test(file_text)
