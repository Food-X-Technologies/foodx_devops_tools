#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Utility related exceptions."""


class AnsibleVaultError(Exception):
    """Problem completing Ansible Vault operation."""


class CommandError(Exception):
    """Problem completing an external command run."""
