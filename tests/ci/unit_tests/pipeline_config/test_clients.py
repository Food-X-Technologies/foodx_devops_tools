#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with foodx_devops_tools.
#  If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.pipeline_config import load_clients
from foodx_devops_tools.pipeline_config.exceptions import ClientsDefinitionError


@pytest.fixture
def apply_clients_test(apply_pipeline_config_test):
    def _apply(mock_content: str):
        result = apply_pipeline_config_test(mock_content, load_clients)
        return result

    return _apply


def test_single_default(apply_clients_test):
    file_text = """---
clients:
  somename:
    release_states:
      - std
      - prd
    system: egms
"""

    result = apply_clients_test(file_text)

    assert len(result.clients) == 1
    assert result.clients["somename"].depends_on is None
    assert result.clients["somename"].pseudonym is None
    assert result.clients["somename"].release_states == ["std", "prd"]
    assert result.clients["somename"].system == "egms"


def test_pseudonym(apply_clients_test):
    file_text = """---
clients:
  somename:
    pseudonym: really long name
    release_states:
      - std
      - prd
    system: egms
"""

    result = apply_clients_test(file_text)

    assert len(result.clients) == 1
    assert result.clients["somename"].pseudonym == "really long name"


def test_depends_on_default(apply_clients_test):
    file_text = """---
clients:
  name1:
    release_states:
      - dev
      - qa
    system: sys1
  name2:
    depends_on: 
      name1:
    release_states:
      - stg
      - prd
    system: sys2
"""

    result = apply_clients_test(file_text)

    assert len(result.clients) == 2
    assert result.clients["name2"].depends_on["name1"] == "qa"


def test_depends_on(apply_clients_test):
    file_text = """---
clients:
  name1:
    release_states:
      - dev
      - qa
      - stg
    system: sys1
  name2:
    depends_on: 
      name1: qa
    release_states:
      - stg
      - prd
    system: sys2
"""

    result = apply_clients_test(file_text)

    assert len(result.clients) == 2
    assert result.clients["name2"].depends_on["name1"] == "qa"


def test_multiple(apply_clients_test):
    file_text = """---
clients:
  name1:
    release_states:
      - dev
      - qa
    system: sys1
  name2:
    release_states:
      - stg
      - prd
    system: sys2
"""

    result = apply_clients_test(file_text)

    assert len(result.clients) == 2
    assert result.clients["name1"].system == "sys1"
    assert result.clients["name2"].system == "sys2"


def test_multiple_depends_on_single(apply_clients_test):
    file_text = """---
clients:
  name1:
    release_states:
      - dev
      - qa
    system: sys1
  name2:
    depends_on: 
      name1:
    release_states:
      - stg
      - prd
    system: sys2
  name3:
    depends_on: 
      name1:
    release_states:
      - stg
      - prd
    system: sys3
"""

    result = apply_clients_test(file_text)

    assert len(result.clients) == 3
    assert result.clients["name2"].depends_on["name1"] == "qa"
    assert result.clients["name3"].depends_on["name1"] == "qa"


def test_missing_dependency_raises(apply_clients_test):
    file_text = """---
clients:
  somename:
    depends_on: 
      othername:
    release_states:
      - stg
      - prd
    system: egms
"""

    with pytest.raises(
        ClientsDefinitionError, match=r"Error validating clients definition"
    ):
        apply_clients_test(file_text)


def test_none_raises(apply_clients_test):
    file_text = """---
"""

    with pytest.raises(
        ClientsDefinitionError, match=r"Error validating clients definition"
    ):
        apply_clients_test(file_text)


def test_empty_raises(apply_clients_test):
    file_text = """---
clients:
"""

    with pytest.raises(
        ClientsDefinitionError, match=r"Error validating clients definition"
    ):
        apply_clients_test(file_text)
