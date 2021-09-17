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
from .deployments import ValueType as DeploymentsData
from .deployments import load_deployments
from .frames import ValueType as FramesData
from .frames import load_frames
from .puff_map import PuffMap, load_puff_map
from .release_states import ValueType as ReleaseStatesData
from .release_states import load_release_states
from .service_principals import ValueType as ServicePrincipalsData
from .service_principals import load_service_principals
from .static_secrets import ValueType as StaticSecrets
from .static_secrets import load_static_secrets
from .subscriptions import ValueType as SubscriptionsData
from .subscriptions import load_subscriptions
from .systems import ValueType as SystemsData
from .systems import load_systems
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
    release_states: ReleaseStatesData
    deployments: DeploymentsData
    frames: FramesData
    puff_map: PuffMap
    service_principals: typing.Optional[ServicePrincipalsData]
    static_secrets: typing.Optional[StaticSecrets]
    subscriptions: SubscriptionsData
    systems: SystemsData
    tenants: TenantsData

    decrypt_token: typing.Optional[str] = None

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
        release_state_config = load_release_states(paths.release_states)
        deployment_config = load_deployments(paths.deployments)
        frames_config = load_frames(paths.frames)
        puff_map_config = load_puff_map(paths.puff_map)
        subscription_config = load_subscriptions(paths.subscriptions)
        system_config = load_systems(paths.systems)
        tenant_config = load_tenants(paths.tenants)

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

        kwargs = {
            "clients": client_config.clients,
            "release_states": release_state_config.release_states,
            "deployments": deployment_config.deployments,
            "frames": frames_config.frames,
            "puff_map": puff_map_config.puff_map,
            "subscriptions": subscription_config.subscriptions,
            "systems": system_config.systems,
            "tenants": tenant_config.tenants,
            "decrypt_token": decrypt_token,
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

    @pydantic.root_validator()
    def check_deployments(cls: pydantic.BaseModel, loaded_data: dict) -> dict:
        """Cross-check loaded deployment data."""
        deployment_names = set(loaded_data["deployments"].keys())
        this_re = re.compile(DEPLOYMENT_NAME_REGEX)
        for this_name in deployment_names:
            result = this_re.match(this_name)

            if not result:
                message = "Bad deployment tuple, {0}".format(this_name)
                log.error("{0}, {1}".format(message, DEPLOYMENT_NAME_REGEX))
                raise PipelineConfigurationError(message)

            this_client = result.group("client")
            if this_client not in loaded_data["clients"]:
                message = "Bad client in deployment tuple, {0}".format(
                    this_client
                )
                log.error(
                    "{0}, {1}, {2}".format(
                        message, this_name, str(loaded_data["clients"])
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
                        message, this_name, str(loaded_data["release_states"])
                    )
                )
                raise PipelineConfigurationError(message)

            this_system = result.group("system")
            if this_system not in loaded_data["systems"]:
                message = "Bad system in deployment tuple, {0}".format(
                    this_system
                )
                log.error(
                    "{0}, {1}, {2}".format(
                        message, this_name, str(loaded_data["systems"])
                    )
                )
                raise PipelineConfigurationError(message)

            this_subscriptions = loaded_data["deployments"][
                this_name
            ].subscriptions
            for subscription_name in this_subscriptions.keys():
                if subscription_name not in loaded_data["subscriptions"]:
                    message = "Bad subscription in deployment, {0}".format(
                        this_name
                    )
                    log.error(
                        "{0}, {1}, {2}, {3}".format(
                            message,
                            this_name,
                            str(this_subscriptions.keys()),
                            str(loaded_data["subscriptions"]),
                        )
                    )
                    raise PipelineConfigurationError(message)
        return loaded_data

    @pydantic.root_validator()
    def check_service_principals(
        cls: pydantic.BaseModel, loaded_data: dict
    ) -> dict:
        """Validate service principal data."""
        if loaded_data["service_principals"]:
            bad_subscriptions = [
                "{0}".format(name)
                for name in loaded_data["service_principals"].keys()
                if name not in loaded_data["subscriptions"].keys()
            ]
            if any(bad_subscriptions):
                message = "Bad subscription(s) in service_principals"
                log.error("{0}, {1}".format(message, str(bad_subscriptions)))
                raise PipelineConfigurationError(message)
        return loaded_data

    @pydantic.root_validator()
    def check_static_secrets(
        cls: pydantic.BaseModel, loaded_data: dict
    ) -> dict:
        """Validate static secret data."""
        if loaded_data["static_secrets"]:
            bad_subscriptions = [
                "{0}".format(name)
                for name in loaded_data["static_secrets"].keys()
                if name not in loaded_data["subscriptions"].keys()
            ]
            if any(bad_subscriptions):
                message = "Bad subscription(s) in static_secrets"
                log.error("{0}, {1}".format(message, str(bad_subscriptions)))
                raise PipelineConfigurationError(message)
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

    @pydantic.root_validator()
    def check_frames_puff_map(
        cls: pydantic.BaseModel, loaded_data: dict
    ) -> dict:
        """
        Cross-check frames, puff map data.

        * The identified frames must be the same.
        * The identified applications must be the same.
        * Any application deployment steps defined in a frame must be defined
          in the puff map.
        * Release states and subscriptions must be valid.
        """
        if set(loaded_data["frames"].frames.keys()) != set(
            loaded_data["puff_map"].frames.keys()
        ):
            message = "Frame definitions mismatch between frames and puff map"
            log.error(
                "{0}, {1}, {2}".format(
                    message,
                    str(set(loaded_data["frames"].frames.keys())),
                    str(set(loaded_data["puff_map"].frames.keys())),
                )
            )
            raise PipelineConfigurationError(message)
        for this_frame, frame_data in loaded_data["frames"].frames.items():
            if set(frame_data.applications.keys()) != set(
                loaded_data["puff_map"].frames[this_frame].applications.keys()
            ):
                message = (
                    "Application definitions mismatch between frames "
                    "and puff map"
                )
                log.error(
                    "{0}, {1}, {2}".format(
                        message,
                        str(set(frame_data.applications.keys())),
                        str(
                            set(
                                loaded_data["puff_map"]
                                .frames[this_frame]
                                .applications.keys()
                            )
                        ),
                    )
                )
                raise PipelineConfigurationError(message)
            for (
                this_application,
                application_data,
            ) in frame_data.applications.items():
                pm_app_data = (
                    loaded_data["puff_map"]
                    .frames[this_frame]
                    .applications[this_application]
                )
                if any(
                    [
                        x not in loaded_data["release_states"]
                        for x in pm_app_data.arm_parameters_files.keys()
                    ]
                ):
                    message = "Bad release state in puff map"
                    log.error(
                        "{0}, {1}, {2}".format(
                            message,
                            str(loaded_data["release_states"]),
                            str(pm_app_data.arm_parameters_files.keys()),
                        )
                    )
                    raise PipelineConfigurationError(message)
                for (
                    this_state,
                    state_data,
                ) in pm_app_data.arm_parameters_files.items():
                    if any(
                        [
                            x not in loaded_data["subscriptions"].keys()
                            for x in state_data.keys()
                        ]
                    ):
                        message = "Bad subscription in puff map"
                        log.error(
                            "{0}, {1}, {2}".format(
                                message,
                                str(loaded_data["subscriptions"].keys()),
                                str(state_data.keys()),
                            )
                        )
                        raise PipelineConfigurationError(message)
                    for subscription_data in state_data.values():
                        frame_step_names = {
                            x.name
                            for x in application_data
                            if hasattr(x, "name")
                        }
                        if frame_step_names != set(subscription_data.keys()):
                            message = (
                                "Application step name mismatch between "
                                "frames and puff map"
                            )
                            log.error(
                                "{0}, {1}, {2}".format(
                                    message,
                                    str(frame_step_names),
                                    str(set(subscription_data.keys())),
                                )
                            )
                            raise PipelineConfigurationError(message)
        return loaded_data
