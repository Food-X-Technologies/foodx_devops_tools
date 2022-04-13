#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Manage pipeline configuration files collectively."""

import logging
import re
import typing

import pydantic

from ._exceptions import PipelineConfigurationError
from ._paths import PipelineConfigurationPaths
from .clients import ValueType as ClientsData
from .clients import load_clients
from .deployments import DeploymentsEndpointsDefinitions as DeploymentsData
from .deployments import load_deployments
from .frames import ValueType as FramesData
from .frames import load_frames
from .release_states import ValueType as ReleaseStatesData
from .release_states import load_release_states
from .service_principals import ServicePrincipals
from .service_principals import ValueType as ServicePrincipalsData
from .service_principals import load_service_principals
from .static_secrets import StaticSecrets
from .static_secrets import ValueType as StaticSecretsData
from .static_secrets import load_static_secrets
from .subscriptions import ValueType as SubscriptionsData
from .subscriptions import load_subscriptions
from .systems import ValueType as SystemsData
from .systems import load_systems
from .template_context import ValueType as TemplateContextData
from .template_context import load_template_context
from .tenants import ValueType as TenantsData
from .tenants import load_tenants

log = logging.getLogger(__name__)

DEPLOYMENT_NAME_REGEX = (
    r"^(?P<system>[a-z0-9]+)"
    r"[_-]"
    r"(?P<client>[a-z0-9]+)"
    r"[_-]"
    r"(?P<release_state>[a-z0-9]+)$"
)


T = typing.TypeVar("T", bound="PipelineConfiguration")


class PipelineConfiguration(pydantic.BaseModel):
    """Pipeline configuration data."""

    clients: ClientsData
    context: TemplateContextData
    release_states: ReleaseStatesData
    deployments: DeploymentsData
    frames: FramesData
    service_principals: typing.Optional[ServicePrincipalsData]
    static_secrets: typing.Optional[StaticSecretsData]
    subscriptions: SubscriptionsData
    systems: SystemsData
    tenants: TenantsData

    decrypt_token: typing.Optional[str] = None

    @staticmethod
    def __load_encrypted_data(
        paths: PipelineConfigurationPaths, decrypt_token: typing.Optional[str]
    ) -> typing.Tuple[
        typing.Optional[ServicePrincipals], typing.Optional[StaticSecrets]
    ]:
        service_principals_config = None
        static_secrets_config = None
        if decrypt_token:
            service_principals_config = load_service_principals(
                paths.service_principals, decrypt_token
            )
            static_secrets_config = load_static_secrets(
                paths.static_secrets, decrypt_token
            )
        else:
            if not paths.service_principals.is_file():
                raise FileNotFoundError(
                    "Missing service principals vault "
                    "file, {0}".format(paths.service_principals)
                )
            missing_files = {
                str(x) for x in paths.static_secrets if not x.is_file()
            }
            if any(missing_files):
                raise FileNotFoundError(
                    "Missing static secrets files, {0}".format(
                        str(missing_files)
                    )
                )

        return service_principals_config, static_secrets_config

    @classmethod
    def from_files(
        cls: typing.Type[T],
        paths: PipelineConfigurationPaths,
        decrypt_token: typing.Optional[str],
    ) -> T:
        """
        Load pipeline configuration from collection of files.

        Args:
            paths: Paths to pipeline configuration files.

        Returns:
            Instantiated ``PipelineConfiguration`` object.
        """
        client_config = load_clients(paths.clients)
        deployment_config = load_deployments(paths.deployments)
        frames_config = load_frames(paths.frames)
        release_state_config = load_release_states(paths.release_states)
        subscription_config = load_subscriptions(paths.subscriptions)
        system_config = load_systems(paths.systems)
        tenant_config = load_tenants(paths.tenants)
        template_context = load_template_context(paths.context)

        (
            service_principals_config,
            static_secrets_config,
        ) = cls.__load_encrypted_data(paths, decrypt_token)

        kwargs = {
            "clients": client_config.clients,
            "release_states": release_state_config.release_states,
            "decrypt_token": decrypt_token,
            "deployments": deployment_config.deployments,
            "frames": frames_config.frames,
            "subscriptions": subscription_config.subscriptions,
            "systems": system_config.systems,
            "tenants": tenant_config.tenants,
            "context": template_context.context,
        }
        if service_principals_config:
            kwargs[
                "service_principals"
            ] = service_principals_config.service_principals
        if static_secrets_config:
            kwargs["static_secrets"] = static_secrets_config.static_secrets

        new_object = cls(**kwargs)

        return new_object

    @pydantic.root_validator()
    def check_clients(cls: pydantic.BaseModel, loaded_data: dict) -> dict:
        """Cross-check clients data with other fields."""
        for name, data in loaded_data["clients"].items():
            if not all(
                [
                    x in loaded_data["release_states"]
                    for x in data.release_states
                ]
            ):
                message = "Bad release state in client, {0}".format(name)
                log.error(
                    "{0}, {1}, {2}".format(
                        message,
                        str(loaded_data["release_states"]),
                        str(data.release_states),
                    )
                )
                raise PipelineConfigurationError(message)

            if data.system not in loaded_data["systems"]:
                message = "Bad system in client, {0}".format(name)
                log.error(
                    "{0}, {1}, {2}".format(
                        message,
                        str(loaded_data["release_states"]),
                        str(data.release_states),
                    )
                )
                raise PipelineConfigurationError(message)
        return loaded_data

    @staticmethod
    def __check_deployment_tuple(
        deployment_tuple: str, loaded_data: dict
    ) -> None:
        """Check for a valid deployment tuple in deployments."""
        this_re = re.compile(DEPLOYMENT_NAME_REGEX)
        result = this_re.match(deployment_tuple)

        if not result:
            message = "Bad deployment tuple, {0}".format(deployment_tuple)
            log.error("{0}, {1}".format(message, DEPLOYMENT_NAME_REGEX))
            raise PipelineConfigurationError(message)

        this_client = result.group("client")
        if this_client not in loaded_data["clients"]:
            message = "Bad client in deployment tuple, {0}".format(this_client)
            log.error(
                "{0}, {1}, {2}".format(
                    message, deployment_tuple, str(loaded_data["clients"])
                )
            )
            raise PipelineConfigurationError(message)

        this_release_state = result.group("release_state")
        if this_release_state not in loaded_data["release_states"]:
            message = "Bad release state in deployment tuple, {0}".format(
                this_release_state
            )
            log.error(
                "{0}, {1}, {2}".format(
                    message,
                    deployment_tuple,
                    str(loaded_data["release_states"]),
                )
            )
            raise PipelineConfigurationError(message)

        this_system = result.group("system")
        if this_system not in loaded_data["systems"]:
            message = "Bad system in deployment tuple, {0}".format(this_system)
            log.error(
                "{0}, {1}, {2}".format(
                    message, deployment_tuple, str(loaded_data["systems"])
                )
            )
            raise PipelineConfigurationError(message)

    @staticmethod
    def __report_deployment_subscription_error(
        deployment_tuple: str,
        subscription_name: str,
        subscriptions: set,
        category: str,
    ) -> None:
        message = (
            "Deployment subscription not defined in "
            "{0}, {1}, {2}".format(
                category, deployment_tuple, subscription_name
            )
        )
        log.error(
            "{0}, {1}".format(
                message,
                str(subscriptions),
            )
        )
        raise PipelineConfigurationError(message)

    @staticmethod
    def __check_deployment_subscriptions(
        deployment_tuple: str, loaded_data: dict
    ) -> None:
        """Check for valid subscriptions in deployments."""
        deployment_subscriptions = set(
            loaded_data["deployments"]
            .deployment_tuples[deployment_tuple]
            .subscriptions.keys()
        )
        for this_deployment_subscription in deployment_subscriptions:
            if this_deployment_subscription not in loaded_data["subscriptions"]:
                # a deployment subscription must be defined in subscriptions.yml
                PipelineConfiguration.__report_deployment_subscription_error(
                    deployment_tuple,
                    this_deployment_subscription,
                    set(loaded_data["subscriptions"].keys()),
                    "subscriptions",
                )

            if (
                ("service_principals" in loaded_data)
                and (loaded_data["service_principals"])
                and (
                    this_deployment_subscription
                    not in loaded_data["service_principals"]
                )
            ):
                # a deployment subscription must be defined in
                # service_principals.vault
                PipelineConfiguration.__report_deployment_subscription_error(
                    deployment_tuple,
                    this_deployment_subscription,
                    set(loaded_data["service_principals"].keys()),
                    "service principals",
                )

            if (
                ("static_secrets" in loaded_data)
                and (loaded_data["static_secrets"])
                and (
                    this_deployment_subscription
                    not in loaded_data["static_secrets"]
                )
            ):
                # a deployment subscription must be defined in static_secrets
                PipelineConfiguration.__report_deployment_subscription_error(
                    deployment_tuple,
                    this_deployment_subscription,
                    set(loaded_data["static_secrets"].keys()),
                    "static secrets",
                )

    @pydantic.root_validator()
    def check_deployments(cls: pydantic.BaseModel, loaded_data: dict) -> dict:
        """Cross-check loaded deployment data."""
        deployment_names = set(
            loaded_data["deployments"].deployment_tuples.keys()
        )
        for this_name in deployment_names:
            typing.cast("PipelineConfiguration", cls).__check_deployment_tuple(
                this_name, loaded_data
            )
            typing.cast(
                "PipelineConfiguration", cls
            ).__check_deployment_subscriptions(this_name, loaded_data)

        return loaded_data

    @pydantic.root_validator()
    def check_service_principals(
        cls: pydantic.BaseModel, loaded_data: dict
    ) -> dict:
        """Validate service principal data."""
        if loaded_data["service_principals"]:
            PipelineConfiguration.__check_subscriptions_in_subscriptions(
                loaded_data, "service_principals"
            )
        return loaded_data

    @staticmethod
    def __check_subscriptions_in_subscriptions(
        loaded_data: dict, data_name: str
    ) -> None:
        """Check that subscriptions names are defined in subscriptions."""
        bad_subscriptions = [
            "{0}".format(name)
            for name in loaded_data[data_name].keys()
            if name not in loaded_data["subscriptions"].keys()
        ]
        if any(bad_subscriptions):
            message = f"{data_name} subscriptions not defined in subscriptions"
            log.error("{0}, {1}".format(message, str(bad_subscriptions)))
            raise PipelineConfigurationError(message)

    @pydantic.root_validator()
    def check_static_secrets(
        cls: pydantic.BaseModel, loaded_data: dict
    ) -> dict:
        """Validate static secret data."""
        if loaded_data["static_secrets"]:
            PipelineConfiguration.__check_subscriptions_in_subscriptions(
                loaded_data, "static_secrets"
            )
        return loaded_data

    @pydantic.root_validator()
    def check_subscriptions(cls: pydantic.BaseModel, loaded_data: dict) -> dict:
        """Validate subscriptions data."""
        bad_tenants = [
            "{0}.{1}".format(name, data.tenant)
            for name, data in loaded_data["subscriptions"].items()
            if data.tenant not in loaded_data["tenants"]
        ]
        if any(bad_tenants):
            message = "Bad tenant(s) in subscription"
            log.error(
                "{0}, {1}, {2}".format(
                    message, str(bad_tenants), str(loaded_data["tenants"])
                )
            )
            raise PipelineConfigurationError(message)
        return loaded_data
