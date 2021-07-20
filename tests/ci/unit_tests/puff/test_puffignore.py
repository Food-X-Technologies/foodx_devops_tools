#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib

import pytest

from foodx_devops_tools.puff.puffignore import BASE_IGNORE, load_puffignore
from tests.ci.support.isolation import simple_isolated_filesystem

MOCK_PUFFIGNORE_CONTENT = """
# a comment
**/some-file.yml
**/ignore-this-dir/*
  
# another comment
**/ignore_another_dir/

"""


@contextlib.contextmanager
def mock_puffignore(content: str):
    with simple_isolated_filesystem() as dir:
        puffignore_path = dir / ".puffignore"
        with open(puffignore_path, mode="w") as f:
            f.write(content)

        yield puffignore_path


@pytest.mark.asyncio
async def test_whitespace_dropped():
    with mock_puffignore(MOCK_PUFFIGNORE_CONTENT) as puffignore_path:
        result = await load_puffignore(puffignore_path)

    expected_result = BASE_IGNORE + [
        "**/some-file.yml",
        "**/ignore-this-dir/*",
        "**/ignore_another_dir/*",
    ]

    assert expected_result == result


@pytest.mark.asyncio
async def test_appended_wildcard():
    """.gitignore convention allows for implicit wildcard terminating
    directory."""
    with mock_puffignore(
        """
**/ignore_another_dir/
"""
    ) as puffignore_path:
        result = await load_puffignore(puffignore_path)

    expected_result = BASE_IGNORE + [
        "**/ignore_another_dir/*",
    ]

    assert expected_result == result


@pytest.mark.asyncio
async def test_empty_loads_clean():
    with mock_puffignore("") as puffignore_path:
        result = await load_puffignore(puffignore_path)

    expected_result = BASE_IGNORE

    assert expected_result == result


@pytest.mark.asyncio
async def test_functionally_empty_loads_clean():
    with mock_puffignore("# just a comment\n") as puffignore_path:
        result = await load_puffignore(puffignore_path)

    expected_result = BASE_IGNORE

    assert expected_result == result


@pytest.mark.asyncio
async def test_nonexistent_file_loads_clean():
    with simple_isolated_filesystem() as dir:
        puffignore_path = dir / ".puffignore"
        result = await load_puffignore(puffignore_path)

    expected_result = BASE_IGNORE

    assert expected_result == result
