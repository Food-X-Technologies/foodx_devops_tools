# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""NPM CI release flow utility."""

import json
import pathlib
import re

import click

from ._simple_ci_release_id import acquire_release_id

MAX_COMMIT_SHA_LENGTH = 7

OUTPUT_TYPES = [
    "id",
    "package",
]

PACKAGE_EXTENSION = "tgz"


def apply_package_release_id(
    package_file: pathlib.Path, release_id: str
) -> str:
    """
    Apply calculated release id to ``package.json`` file.

    Args:
        package_file: ``package.json`` file to read and modify.
        release_id: release id to apply.

    Returns:
        Package name read from ``package.json`` file.
    """
    with package_file.open(mode="r") as f:
        content = json.load(f)

    content["version"] = release_id

    # write modified json
    with package_file.open(mode="w") as f:
        json.dump(content, f)

    return content["name"]


def normalize_package_name(original_name: str) -> str:
    """
    Convert the raw name from ``package.json`` into the ``npm pack`` style name.

    Args:
        original_name: Name acquired from ``package.json``.

    Returns:
        Normalized name.
    """
    regex = re.compile(r"^(@(?P<group>[0-9a-z\-]+)/)?(?P<package>[0-9a-z\-]+)$")
    result = regex.match(original_name)
    if result and result.group("group"):
        normalized = "{0}-{1}".format(
            result.group("group"), result.group("package")
        )
    elif result:
        normalized = result.group("package")
    else:
        raise RuntimeError(
            "Unable to normalize package name, {0}".format(original_name)
        )

    return normalized


def output_package_name(package_name_json: str, release_id: str) -> None:
    """
    Output to stdout the normalized package file name.

    Args:
        package_name_json: Package name acquired from ``package.json``.
        release_id: Calculated release id.
    """
    package_name_file = normalize_package_name(package_name_json)
    click.echo(
        "{0}-{1}.{2}".format(package_name_file, release_id, PACKAGE_EXTENSION),
        nl=False,
    )


@click.command()
@click.argument(
    "output_type",
    type=click.Choice(OUTPUT_TYPES),
)
@click.argument(
    "package_json_file",
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.argument(
    "ci_ref",
    type=str,
)
@click.argument(
    "commit_sha",
    type=str,
)
def npm_subcommand(
    output_type: str, package_json_file: str, ci_ref: str, commit_sha: str
) -> None:
    """From git reference extract release id for "simple" CI release flow."""
    release_id = acquire_release_id(ci_ref, commit_sha)
    if output_type == "id":
        click.echo(release_id, nl=False)
    elif output_type == "package":
        package_name_json = apply_package_release_id(
            pathlib.Path(package_json_file), release_id
        )

        output_package_name(package_name_json, release_id)
    else:
        raise RuntimeError("Unknown output type, {0}".format(output_type))
