#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib
import copy
import json
import pathlib
import tempfile

from foodx_devops_tools.puff_utility import _main
from tests.ci.support.click_runner import (  # noqa: F401
    click_runner,
    isolated_filesystem,
)

SAMPLE_DATA = """services:
  s1:
    p1: s1p1
    environments:
      e1:
        p1: s1e1p1
        regions:
          - r1:
              p1: s1e1r1p1
              p2:
                reference:
                  keyVault:
                    id: idv
                  secretName: sn
"""


@contextlib.contextmanager
def mock_file(
    file_name: str,
    content: str,
):
    with tempfile.TemporaryDirectory() as dir:
        expected_dir = pathlib.Path(dir)
        file_path = expected_dir / file_name
        with file_path.open(mode="w") as f:
            f.write(content)

        yield file_path


def test_generate_clean(click_runner):
    """Empty ignore patterns run acquires all YAML files."""
    expected_data = {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {
            "service": {"value": "s1"},
            "environment": {"value": "e1"},
            "region": {"value": "r1"},
            "p1": {"value": "s1e1r1p1"},
            "p2": {
                "reference": {
                    "keyVault": {
                        "id": "idv",
                    },
                    "secretName": "sn",
                },
            },
        },
    }

    with mock_file("some.yml", copy.deepcopy(SAMPLE_DATA)) as file_path:
        click_runner.invoke(_main, [str(file_path.parent)])

        expected_file = file_path.parent / "some.s1.e1.r1.json"
        with expected_file.open("r") as f:
            data = json.load(f)

        assert data == expected_data
