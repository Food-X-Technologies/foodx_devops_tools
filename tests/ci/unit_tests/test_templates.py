#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import json
import pathlib
import tempfile

import pytest

from foodx_devops_tools.templates import do_snippet_substitution


async def do_check(source_file, target_file, expected_data):
    await do_snippet_substitution(source_file, target_file)

    with target_file.open(mode="r") as f:
        content = f.read()
        read_data = json.loads(content)

    assert read_data == expected_data


@pytest.mark.asyncio
async def test_no_change(mock_async_method):
    with tempfile.TemporaryDirectory() as dir:
        this_dir = pathlib.Path(dir)

        data = {
            "something": "some content",
        }
        content = json.dumps(data)

        source_file = this_dir / "this_file"
        with source_file.open(mode="w") as f:
            f.write(content)

        target_file = this_dir / "that_file"
        expected_data = {
            "something": "some content",
        }
        await do_check(source_file, target_file, expected_data)


@pytest.mark.asyncio
async def test_single(mock_async_method):
    snippet_content = "snippet content"
    with tempfile.TemporaryDirectory() as dir:
        this_dir = pathlib.Path(dir)

        snippet_file = this_dir / "this_snippet"
        data = {
            "something": "#{0}#".format(snippet_file),
        }
        content = json.dumps(data)

        source_file = this_dir / "this_file"
        with source_file.open(mode="w") as f:
            f.write(content)

        with snippet_file.open(mode="w") as f:
            f.write(snippet_content)

        target_file = this_dir / "that_file"
        expected_data = {
            "something": "snippet content",
        }
        await do_check(source_file, target_file, expected_data)


@pytest.mark.asyncio
async def test_multiline_snippet(mock_async_method):
    snippet_content = """snippet content
on multiple
lines
"""
    with tempfile.TemporaryDirectory() as dir:
        this_dir = pathlib.Path(dir)

        snippet_file = this_dir / "this_snippet"
        data = {
            "something": "#{0}#".format(snippet_file),
        }
        content = json.dumps(data)

        source_file = this_dir / "this_file"
        with source_file.open(mode="w") as f:
            f.write(content)

        with snippet_file.open(mode="w") as f:
            f.write(snippet_content)

        target_file = this_dir / "that_file"
        expected_data = {
            "something": "snippet content\non multiple\nlines\n",
        }
        await do_check(source_file, target_file, expected_data)


@pytest.mark.asyncio
async def test_quoted_snippet(mock_async_method):
    snippet_content = """snippet content="is quoted" lines"""
    with tempfile.TemporaryDirectory() as dir:
        this_dir = pathlib.Path(dir)

        snippet_file = this_dir / "this_snippet"
        data = {
            "something": "#{0}#".format(snippet_file),
        }
        content = json.dumps(data)

        source_file = this_dir / "this_file"
        with source_file.open(mode="w") as f:
            f.write(content)

        with snippet_file.open(mode="w") as f:
            f.write(snippet_content)

        target_file = this_dir / "that_file"
        expected_data = {
            "something": 'snippet content="is quoted" lines',
        }
        await do_check(source_file, target_file, expected_data)


@pytest.mark.asyncio
async def test_quoted_multiline_snippet(mock_async_method):
    snippet_content = """snippet content
"is quoted"
lines
"""
    with tempfile.TemporaryDirectory() as dir:
        this_dir = pathlib.Path(dir)

        snippet_file = this_dir / "this_snippet"
        data = {
            "something": "#{0}#".format(snippet_file),
        }
        content = json.dumps(data)

        source_file = this_dir / "this_file"
        with source_file.open(mode="w") as f:
            f.write(content)

        with snippet_file.open(mode="w") as f:
            f.write(snippet_content)

        target_file = this_dir / "that_file"
        expected_data = {
            "something": 'snippet content\n"is quoted"\nlines\n',
        }
        await do_check(source_file, target_file, expected_data)


@pytest.mark.asyncio
async def test_multiple_lines(mock_async_method):
    snippet1_content = "snippet1 content"
    snippet2_content = "more content"
    with tempfile.TemporaryDirectory() as dir:
        this_dir = pathlib.Path(dir)

        snippet1 = this_dir / "snippet1"
        snippet2 = this_dir / "snippet2"
        data = {
            "one": "#{0}#".format(snippet1),
            "none": "no change",
            "two": "#{0}#".format(snippet2),
        }
        content = json.dumps(data)

        source_file = this_dir / "this_file"
        with source_file.open(mode="w") as f:
            f.write(content)

        with snippet1.open(mode="w") as f:
            f.write(snippet1_content)
        with snippet2.open(mode="w") as f:
            f.write(snippet2_content)

        target_file = this_dir / "that_file"
        expected_data = {
            "one": "snippet1 content",
            "none": "no change",
            "two": "more content",
        }
        await do_check(source_file, target_file, expected_data)


@pytest.mark.asyncio
async def test_multiple_in_line(mock_async_method):
    snippet1_content = "snippet1 content"
    snippet2_content = "more content"
    with tempfile.TemporaryDirectory() as dir:
        this_dir = pathlib.Path(dir)

        snippet1 = this_dir / "snippet1"
        snippet2 = this_dir / "snippet2"
        data = {
            "one": "#{0}#joiner#{1}#".format(snippet1, snippet2),
            "none": "no change",
        }
        content = json.dumps(data)

        source_file = this_dir / "this_file"
        with source_file.open(mode="w") as f:
            f.write(content)

        with snippet1.open(mode="w") as f:
            f.write(snippet1_content)
        with snippet2.open(mode="w") as f:
            f.write(snippet2_content)

        target_file = this_dir / "that_file"
        expected_data = {
            "one": "snippet1 contentjoinermore content",
            "none": "no change",
        }
        await do_check(source_file, target_file, expected_data)
