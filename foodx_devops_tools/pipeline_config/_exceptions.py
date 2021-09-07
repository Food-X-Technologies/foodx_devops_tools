#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Exception declarations for package internal consumption."""


class ConfigurationPathsError(Exception):
    """Problem with configuration paths, or acquiring configuration."""


class DeploymentsDefinitionError(Exception):
    """Problem loading deployment definitions."""


class FrameDefinitionsError(Exception):
    """Problem loading frame definitions."""


class FolderPathError(Exception):
    """Problem acquiring frame folder path."""


class PipelineConfigurationError(Exception):
    """Problem occurred loading pipeline configuration."""


class PuffMapDefinitionsError(Exception):
    """Problem parsing puff map definitions."""


class ReleaseStatesDefinitionError(Exception):
    """Problem loading release state definitions."""


class ServicePrincipalsError(Exception):
    """Problem loading service principal secrets."""


class StaticSecretsError(Exception):
    """Problem loading static secrets."""


class SubscriptionsDefinitionError(Exception):
    """Problem loading subscription definitions."""


class SystemsDefinitionError(Exception):
    """Problem loading system definitions."""


class TenantsDefinitionError(Exception):
    """Problem loading tenant definitions."""


class PipelineViewError(Exception):
    """Problem with view data."""


class ClientsDefinitionError(Exception):
    """Problem loading client definitions."""
