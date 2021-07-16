#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import re
import subprocess
import typing

MAX_COMMIT_SHA_LENGTH = 7

PACKAGE_EXTENSION = "tgz"

GIT_DESCRIBE_PATTERN = r"^(?P<tag>[0-9a-z\-.]+)-(?P<offset>[0-9]+)-([0-9a-z]+)$"
SEMANTIC_RELEASE_PATTERN = r"(\d+)(\.\d+)*"
SEMANTIC_TAG_PATTERN = (
    r"^(refs/tags/(?P<release>{0}$))|"
    r"(refs/tags/(?P<dryrun>{0}-dryrun\d*)$)".format(SEMANTIC_RELEASE_PATTERN)
)


def acquire_post_data() -> typing.Tuple[str, str]:
    """
    Acquire the offset of HEAD from the last release tag in commit history.

    The offset is calculated as the number of commits between HEAD and the
    release tag.

    Returns:
        Tuple of last release tag and offset.
    """
    run_result = subprocess.run(
        # exclude prerelease tags from git describe
        ["git", "describe", "--first-parent", "--tags", "--exclude", "*.*.*-*"],
        capture_output=True,
        text=True,
    )

    if run_result.returncode != 0:
        raise RuntimeError(
            "git describe command failed, {0}".format(run_result.stderr)
        )

    match_result = re.match(GIT_DESCRIBE_PATTERN, run_result.stdout)
    if not match_result:
        raise RuntimeError(
            "git describe tag error, {0}".format(run_result.stdout)
        )

    return match_result.group("tag"), match_result.group("offset")


def acquire_release_id(ci_ref: str, commit_sha: str) -> str:
    """
    Formulate release id aligned with current CI branch.

    Args:
        ci_ref: CI branch reference.
        commit_sha: CI HEAD git commit SHA.

    Returns:
        Formulated release id.
    """
    if len(commit_sha) > MAX_COMMIT_SHA_LENGTH:
        this_sha = commit_sha[0:MAX_COMMIT_SHA_LENGTH]
    else:
        this_sha = commit_sha

    semantic_commit_ref = re.compile(SEMANTIC_TAG_PATTERN)
    regex_result = semantic_commit_ref.match(ci_ref)
    if regex_result and regex_result.group("release"):
        release_id = regex_result.group("release")
    elif regex_result and regex_result.group("dryrun"):
        release_id = regex_result.group("dryrun")
    else:
        # non-release use "-post" suffix
        this_tag, this_offset = acquire_post_data()
        release_id = "{0}-post.{1}.{2}".format(this_tag, this_offset, this_sha)

    return release_id
