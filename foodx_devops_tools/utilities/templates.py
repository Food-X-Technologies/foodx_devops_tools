#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""General support for templating."""


def json_inlining(content: str) -> str:
    """
    Inline text content for inclusion in a JSON file (ARM template).

    Escape double quotes and retain newlines as escapes to embody the content
    in a single line.

    Args:
        content: Content to be "inlined".

    Returns:
        Modified content.
    """
    escaped_newlines = repr(content).strip("'").replace(r"\n", r"\n")
    escaped_quotes = escaped_newlines.replace('"', r"\"")

    return escaped_quotes
