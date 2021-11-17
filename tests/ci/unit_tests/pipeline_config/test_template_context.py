#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib
import pathlib
import tempfile
import typing

from foodx_devops_tools.pipeline_config import load_template_context


@contextlib.contextmanager
def context_files(
    content: typing.Dict[str, typing.Dict[str, str]]
) -> typing.Generator[typing.List[pathlib.Path], None, None]:
    dir_paths = set()
    file_paths = set()
    with tempfile.TemporaryDirectory() as base_path:
        for this_dir, file_data in content.items():
            dir_path = pathlib.Path(base_path) / this_dir
            dir_path.mkdir(parents=True)
            dir_paths.add(dir_path)
            for file_name, file_content in file_data.items():
                this_file = dir_path / file_name
                with this_file.open("w") as f:
                    f.write(file_content)

                file_paths.add(this_file)

        yield dir_paths, file_paths


def test_load_files():
    file_text = {
        "a": {
            "f1": """---
context:
  s1:
    s1k1: s1k1v
    s1k2: s1k2v
  s2:
    s2k1: s2k1v
""",
            "f2": """---
context:
  s3:
    s3k1: s3k1v
""",
        },
    }
    with context_files(file_text) as (dir_paths, file_paths):
        result = load_template_context(file_paths)

    assert len(result.context) == 3
    assert result.context == {
        "s1": {
            "s1k1": "s1k1v",
            "s1k2": "s1k2v",
        },
        "s2": {"s2k1": "s2k1v"},
        "s3": {"s3k1": "s3k1v"},
    }


def test_load_dirs():
    file_text = {
        "a": {
            "f1": """---
context:
  s1:
    s1k1: s1k1v
    s1k2: s1k2v
  s2:
    s2k1: s2k1v
""",
            "f2": """---
context:
  s3:
    s3k1: s3k1v
""",
        },
        "b": {
            "f1": """---
context:
  s1:
    s1k3: s1k3v
  s4:
    s4k1: s4k1v
""",
        },
    }
    with context_files(file_text) as (dir_paths, file_paths):
        result = load_template_context(file_paths)

    assert len(result.context) == 4
    assert result.context == {
        "s1": {
            "s1k1": "s1k1v",
            "s1k2": "s1k2v",
            "s1k3": "s1k3v",
        },
        "s2": {"s2k1": "s2k1v"},
        "s3": {"s3k1": "s3k1v"},
        "s4": {"s4k1": "s4k1v"},
    }


def test_deep_merge():
    """yaml object data should be merged across all levels in the data."""
    file_text = {
        "a": {
            "f1": """---
context:
  s1:
    s1k1: 
      s1k1kk1: v1
""",
            "f2": """---
context:
  s1:
    s1k1: 
      s1k1kk2: 
        s1k1kkk1: v2
""",
        },
        "b": {
            "f1": """---
context:
  s1:
    s1k1: 
      s1k1kk2: 
        s1k1kkk2: v3
""",
        },
    }
    with context_files(file_text) as (dir_paths, file_paths):
        result = load_template_context(file_paths)

    assert result.context == {
        "s1": {
            "s1k1": {
                "s1k1kk1": "v1",
                "s1k1kk2": {
                    "s1k1kkk1": "v2",
                    "s1k1kkk2": "v3",
                },
            },
        },
    }
