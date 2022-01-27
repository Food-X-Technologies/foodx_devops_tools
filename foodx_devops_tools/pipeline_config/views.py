#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Context sensitive views of pipeline configuration data."""

import copy
import dataclasses
import logging
import pathlib
import re
import typing

import deepmerge  # type: ignore

from foodx_devops_tools._to import StructuredTo
from foodx_devops_tools.azure.cloud import AzureCredentials
from foodx_devops_tools.patterns import SubscriptionData
from foodx_devops_tools.utilities.jinja2 import TemplateParameters
from foodx_devops_tools.utilities.templates import TemplateFiles, TemplatePaths

from ..deployment import DeploymentTuple
from ._exceptions import PipelineViewError
from .pipeline import PipelineConfiguration, PuffMap

log = logging.getLogger(__name__)

Z = typing.TypeVar("Z", bound="IterationContext")


class IterationContext(typing.List[str]):
    """Record the iteration path."""

    def __str__(self: Z) -> str:
        """Convert the iteration path to a structured string."""
        return ".".join(self)


Y = typing.TypeVar("Y", bound="DeploymentContext")


class DeploymentContext:
    """Deployment context data expected to be applied to resource tags."""

    commit_sha: str
    git_ref: typing.Optional[str]
    pipeline_id: str
    release_id: str
    release_state: str

    # these data must be provided at deployment time because they are more
    # deeply context sensitive.
    __application_name: typing.Optional[str] = None
    __azure_subscription_name: typing.Optional[str] = None
    __azure_tenant_name: typing.Optional[str] = None
    __client: typing.Optional[str] = None
    __frame_name: typing.Optional[str] = None
    __system: typing.Optional[str] = None

    def __init__(
        self: Y,
        commit_sha: str,
        git_ref: typing.Optional[str],
        pipeline_id: str,
        release_id: str,
        release_state: str,
    ) -> None:
        """Construct ``DeploymentContext`` object."""
        self.commit_sha = commit_sha
        self.git_ref = git_ref
        self.pipeline_id = pipeline_id
        self.release_id = release_id
        self.release_state = release_state

    @property
    def application_name(self: Y) -> str:
        """Get application name property."""
        if self.__application_name:
            return self.__application_name
        else:
            raise PipelineViewError(
                "application name not specified in deployment data"
            )

    @application_name.setter
    def application_name(self: Y, v: str) -> None:
        """Set application name property."""
        self.__application_name = v

    @property
    def azure_subscription_name(self: Y) -> str:
        """Get azure subscription name property."""
        if self.__azure_subscription_name:
            return self.__azure_subscription_name
        else:
            raise PipelineViewError(
                "azure subscription name not specified in deployment data"
            )

    @azure_subscription_name.setter
    def azure_subscription_name(self: Y, v: str) -> None:
        """Set azure subscription name property."""
        self.__azure_subscription_name = v

    @property
    def azure_tenant_name(self: Y) -> str:
        """Get azure tenant name property."""
        if self.__azure_tenant_name:
            return self.__azure_tenant_name
        else:
            raise PipelineViewError(
                "azure tenant name not specified in deployment data"
            )

    @azure_tenant_name.setter
    def azure_tenant_name(self: Y, v: str) -> None:
        """Set azure tenant name property."""
        self.__azure_tenant_name = v

    @property
    def client(self: Y) -> str:
        """Get client name property."""
        if self.__client:
            return self.__client
        else:
            raise PipelineViewError("client not specified in deployment data")

    @client.setter
    def client(self: Y, v: str) -> None:
        """Set client name property."""
        self.__client = v

    @property
    def frame_name(self: Y) -> str:
        """Get frame name property."""
        if self.__frame_name:
            return self.__frame_name
        else:
            raise PipelineViewError(
                "frame name not specified in deployment data"
            )

    @frame_name.setter
    def frame_name(self: Y, v: str) -> None:
        """Set frame name property."""
        self.__frame_name = v

    @property
    def resource_suffix(self: Y) -> str:
        """Get resource suffix property."""
        try:
            subscription_data = SubscriptionData.from_subscription_name(
                self.azure_subscription_name
            )

            return subscription_data.resource_suffix
        except PipelineViewError:
            # azure_subscription_name is undefined so just return an
            # identifiable response here.
            return "UNSPECIFIED"

    @property
    def system(self: Y) -> str:
        """Get system name property."""
        if self.__system:
            return self.__system
        else:
            raise PipelineViewError("system not specified in deployment data")

    @system.setter
    def system(self: Y, v: str) -> None:
        """Set system name property."""
        self.__system = v

    def as_dict(self: Y) -> dict:
        """
        Generate ``dict`` object representation of context data.

        The representation is intended to be used for tags data in ARM
        template parameter files. Note that "microsoft", "azure" and
        "windows" are reserved prefixes in Azure tags so any fields using
        these prefixes must be renamed for the dictionary conversion.
        """
        return {
            "application_name": self.__application_name,
            "client": self.__client,
            "commit_sha": self.commit_sha,
            "frame_name": self.__frame_name,
            "pipeline_id": self.pipeline_id,
            "release_id": self.release_id,
            "release_state": self.release_state,
            "resource_suffix": self.resource_suffix,
            "subscription_name": self.__azure_subscription_name,
            "system": self.__system,
            "tenant_name": self.__azure_tenant_name,
        }

    def __str__(self: Y) -> str:
        """Convert object to str for logging purposes."""
        return str(self.as_dict())


X = typing.TypeVar("X", bound="DeployDataView")


class DeployDataView:
    """Data critical to a resource deployment."""

    azure_credentials: AzureCredentials
    deployment_tuple: str
    location_primary: str
    release_state: str
    root_fqdn: str
    static_secrets: dict
    subscription_id: str
    template_context: dict
    tenant_id: str
    url_endpoints: typing.List[str]

    frame_folder: typing.Optional[pathlib.Path] = None

    __location_secondary: typing.Optional[str] = None

    iteration_context: IterationContext
    to: StructuredTo
    __puff_map: typing.Optional[PuffMap] = None

    def __init__(
        self: X,
        azure_credentials: AzureCredentials,
        deployment_tuple: str,
        location_primary: str,
        release_state: str,
        root_fqdn: str,
        static_secrets: dict,
        subscription_id: str,
        tenant_id: str,
        url_endpoints: typing.List[str],
        user_defined_template_context: dict,
        location_secondary: typing.Optional[str] = None,
    ) -> None:
        """Construct ``DeployDataView`` object."""
        self.azure_credentials = azure_credentials
        self.deployment_tuple = deployment_tuple
        self.location_primary = location_primary
        self.release_state = release_state
        self.root_fqdn = root_fqdn
        self.static_secrets = static_secrets
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.template_context = user_defined_template_context
        self.url_endpoints = url_endpoints
        self.__location_secondary = location_secondary

        self.iteration_context = IterationContext()
        self.to = StructuredTo()

    @property
    def location_secondary(self: X) -> typing.Optional[str]:
        """Get location secondary property."""
        return self.__location_secondary

    @location_secondary.setter
    def location_secondary(self: X, v: str) -> None:
        """Set location secondary property."""
        self.__location_secondary = v

    @property
    def puff_map(self: X) -> PuffMap:
        """Get puff map property."""
        if self.__puff_map:
            return self.__puff_map
        else:
            raise PipelineViewError("puff map not specified in deployment data")

    @puff_map.setter
    def puff_map(self: X, value: PuffMap) -> None:
        """Set puff map property."""
        self.__puff_map = value

    def __str__(self: X) -> str:
        """Convert object to str for logging purposes."""
        return str(
            {
                "azure_credentials": self.azure_credentials,
                "deployment_tuple": self.deployment_tuple,
                "location_primary": self.location_primary,
                "release_state": self.release_state,
                "location_secondary": self.__location_secondary,
                "iteration_context": self.iteration_context,
            }
        )


W = typing.TypeVar("W", bound="FlattenedDeployment")


@dataclasses.dataclass
class FlattenedDeployment:
    """Flattened deployment data for deployment concurrency."""

    context: DeploymentContext
    data: DeployDataView

    def copy_add_frame(self: W, frame_name: str) -> W:
        """
        Deep copy this object and add frame name data.

        Args:
            frame_name: Frame name data to add.

        Returns:
            Copied and updated object.
        """
        x = copy.deepcopy(self)
        x.context.frame_name = frame_name
        x.data.iteration_context.append(frame_name)
        return x

    def copy_add_application(self: W, application_name: str) -> W:
        """
        Deep copy this object and add application name data.

        Args:
            application_name: Application name data to add.

        Returns:
            Copied and updated object.
        """
        x = copy.deepcopy(self)
        x.context.application_name = application_name
        x.data.iteration_context.append(application_name)
        return x

    def construct_fqdn(self: W, leaf_name: str) -> str:
        """
        Construct an FQDN from deployment context.

        Raises:
            SubscriptionNameError: If the subscription name cannot be parsed to
                extract the resource suffix.
        """
        subscription_data = SubscriptionData.from_subscription_name(
            self.context.azure_subscription_name
        )

        return ".".join(
            [
                leaf_name,
                subscription_data.resource_suffix,
                self.context.client,
                self.data.root_fqdn,
            ]
        )

    def construct_app_fqdns(self: W) -> TemplateParameters:
        """Construct endpoint FQDNs for deployyment."""
        result: TemplateParameters = {
            x: self.construct_fqdn(x) for x in self.data.url_endpoints
        }
        result["root"] = self.data.root_fqdn
        result["support"] = "support.{0}.{1}".format(
            self.context.client, self.data.root_fqdn
        )
        return result

    def construct_app_urls(self: W) -> TemplateParameters:
        """Construct endpoint URLs for deployment."""
        fqdns = self.construct_app_fqdns()
        result: TemplateParameters = {
            x: "https://{0}".format(y) for x, y in fqdns.items() if x != "root"
        }

        return result

    def construct_template_parameters(
        self: W, resource_group_name: typing.Optional[str] = None
    ) -> TemplateParameters:
        """
        Construct set of parameters for jinja2 templates.

        Args:
            resource_group_name:    Name of current resource group being
                                    deployed to.

        Returns:
            Dict of parameters to be applied to jinja2 templating.
        """
        engine_data = {
            "environment": {
                "azure": {
                    "subscription_id": self.data.subscription_id,
                    "tenant_id": self.data.tenant_id,
                },
                "resource_group": resource_group_name,
            },
            "locations": {
                "primary": self.data.location_primary,
                "secondary": self.data.location_secondary,
            },
            "network": {
                "fqdns": self.construct_app_fqdns(),
                "urls": self.construct_app_urls(),
            },
            "tags": self.context.as_dict(),
        }
        result: TemplateParameters = {
            "context": {
                **deepmerge.always_merger.merge(
                    copy.deepcopy(self.data.template_context), engine_data
                ),
            },
        }

        return result

    def construct_deployment_name(self: W, step_name: str) -> str:
        """
        Construct the deployment name for use in az CLI.

        Note Azure deployment name have specific limitations:

        * limited to 64 characters
        * must only contain alphanumerics and the characters ".-_"
        """
        assert self.context.application_name is not None
        assert self.context.pipeline_id is not None
        assert self.context.release_id is not None

        substitution_value = "-"
        # reserving underscore here for segmentation of deployment name.
        regex = re.compile(r"[^A-Za-z0-9.\-]")

        filtered_app_name = regex.sub(
            substitution_value, self.context.application_name
        )[0:20]
        filtered_pipeline_id = regex.sub(
            substitution_value, self.context.pipeline_id
        )
        filtered_step_name = regex.sub(substitution_value, step_name)[0:20]

        result = "{0}_{1}".format(
            filtered_app_name
            if filtered_app_name == filtered_step_name
            else "{0}_{1}".format(filtered_app_name, filtered_step_name),
            filtered_pipeline_id,
        )

        return result[0:64]

    @staticmethod
    def __construct_working_directory(
        parent_dir: pathlib.Path, working_name: str
    ) -> pathlib.Path:
        working_dir = parent_dir / "working" / working_name

        return working_dir

    @staticmethod
    def __encode_working_name(parameters: TemplateParameters) -> str:
        """Construct a working directory name from template parameters."""
        # for now, use a simple predictable, non-empty value
        value = "w"
        return value

    def construct_deployment_paths(
        self: W,
        specified_arm_file: typing.Optional[pathlib.Path],
        specified_puff_file: typing.Optional[pathlib.Path],
        target_arm_parameter_path: typing.Optional[pathlib.Path],
    ) -> TemplateFiles:
        """
        Construct paths for ARM template files.

        Args:
            specified_arm_file:
            specified_puff_file:
            target_arm_parameter_path:
            working_name:

        Returns:
            Tuple of necessary paths.
        Raises:
            PipelineViewError:  If any errors occur due to undefined deployment
                                data.
        """
        template_parameters = self.construct_template_parameters()
        working_name = self.__encode_working_name(template_parameters)
        application_name = self.context.application_name
        frame_folder = self.data.frame_folder
        if not frame_folder:
            raise PipelineViewError(
                "frame_folder not defined for application step"
            )
        if not target_arm_parameter_path:
            raise PipelineViewError(
                "target_arm_parameter_path not defined for application step"
            )

        source_arm_template_path = (
            (frame_folder / specified_arm_file)
            if specified_arm_file
            else (frame_folder / "{0}.json".format(application_name))
        )
        log.debug(f"source arm template path, {source_arm_template_path}")

        # Assume that the source arm template path can be used for the other
        # files. In the case that the ARM template path is "out of frame"
        # then the user must explicitly define the puff file path
        if specified_puff_file:
            puff_prompt = "user specified puff file"
            source_puff_path = frame_folder / specified_puff_file
        elif specified_arm_file:
            puff_prompt = "puff file inferred from arm file"
            source_puff_path = source_arm_template_path.parent / str(
                specified_arm_file.name
            ).replace("json", "yml")
        else:
            puff_prompt = "puff file inferred from application name"
            source_puff_path = (
                source_arm_template_path.parent
                / "{0}.yml".format(application_name)
            )
        log.debug(f"{puff_prompt}, {source_puff_path}")

        working_dir = self.__construct_working_directory(
            frame_folder, working_name
        )
        # Assume arm template parameters file has been specified with any sub
        # directories in it's path in puff_map.yml, so only frame_folder is
        # used here.
        parameters_path = working_dir / target_arm_parameter_path
        log.debug(f"arm parameters path, {parameters_path}")

        log.debug(f"working directory, {working_dir}")
        target_arm_template_path = self.__screen_jinja_template(
            source_arm_template_path, working_dir
        )

        template_files = TemplateFiles(
            arm_template=TemplatePaths(
                source=source_arm_template_path,
                target=target_arm_template_path,
            ),
            arm_template_parameters=TemplatePaths(
                source=source_puff_path,
                target=parameters_path,
            ),
        )

        return template_files

    @staticmethod
    def __screen_jinja_template(
        source_path: pathlib.Path, working_dir: pathlib.Path
    ) -> pathlib.Path:
        # A jinja template file needs to have a target in the working dir.
        target_path = working_dir / "{0}".format(source_path.name)

        return target_path


V = typing.TypeVar("V", bound="SubscriptionView")
U = typing.TypeVar("U", bound="DeploymentView")
T = typing.TypeVar("T", bound="ReleaseView")


class SubscriptionView:
    """View of pipeline configuration conditioned by a subscription name."""

    deployment_view: "DeploymentView"
    subscription_name: str

    def __init__(self: V, deployment_view: U, subscription_name: str) -> None:
        """Construct ``SubscriptionView`` object."""
        self.deployment_view = deployment_view
        self.subscription_name = subscription_name

        self._validate_subscription()

    @property
    def deploy_data(self: V) -> typing.List[DeployDataView]:
        """Provide deployment data for each location in this subscription."""
        base_data = (
            self.deployment_view.release_view.configuration.subscriptions[
                self.subscription_name
            ]
        )
        result: typing.List[DeployDataView] = list()
        this_deployment = self.deployment_view.release_view.configuration.deployments.deployment_tuples[  # noqa: E501
            str(self.deployment_view.deployment_tuple)
        ]
        this_service_principals = (
            self.deployment_view.release_view.configuration.service_principals  # noqa: E501
        )
        if not this_service_principals:
            raise PipelineViewError("Missing service principal credentials")

        this_tenants = self.deployment_view.release_view.configuration.tenants
        for this_locations in this_deployment.subscriptions[
            self.subscription_name
        ].locations:
            this_credentials = AzureCredentials(
                userid=this_service_principals[self.subscription_name].id,
                secret=this_service_principals[self.subscription_name].secret,
                name=this_service_principals[self.subscription_name].name,
                subscription=base_data.azure_id,
                tenant=this_tenants[base_data.tenant].azure_id,
            )
            static_secrets = dict()
            secrets_collection = (
                self.deployment_view.release_view.configuration.static_secrets
            )
            if secrets_collection and (
                self.subscription_name in secrets_collection
            ):
                log.debug(
                    "static secret keys, {0}".format(secrets_collection.keys())
                )
                static_secrets = secrets_collection[self.subscription_name]
            elif secrets_collection and (
                self.subscription_name not in secrets_collection
            ):
                raise PipelineViewError(
                    "subscription not defined in static "
                    "secrets, {0}".format(self.subscription_name)
                )

            subscription_id = (
                self.deployment_view.release_view.configuration.subscriptions[
                    self.subscription_name
                ].azure_id
            )
            tenant_name = (
                self.deployment_view.release_view.configuration.subscriptions[
                    self.subscription_name
                ].tenant
            )
            tenant_id = self.deployment_view.release_view.configuration.tenants[
                tenant_name
            ].azure_id
            this_data: typing.Dict[str, typing.Any] = {
                "azure_credentials": this_credentials,
                "deployment_tuple": str(self.deployment_view.deployment_tuple),
                "location_primary": this_locations.primary,
                "location_secondary": this_locations.secondary,
                "root_fqdn": this_deployment.subscriptions[
                    self.subscription_name
                ].root_fqdn,
                "release_state": self.deployment_view.release_view.deployment_context.release_state,  # noqa: E501
                "static_secrets": static_secrets,
                "subscription_id": subscription_id,
                "tenant_id": tenant_id,
                "url_endpoints": self.deployment_view.release_view.configuration.deployments.url_endpoints,  # noqa: E501
                "user_defined_template_context": self.deployment_view.release_view.configuration.context,  # noqa: E501
            }
            if this_locations.secondary:
                this_data["location_secondary"] = this_locations.secondary

            result.append(DeployDataView(**this_data))

        return result

    def _validate_subscription(self: V) -> None:
        if (
            self.subscription_name
            not in self.deployment_view.release_view.configuration.subscriptions
        ):
            raise PipelineViewError(
                "Bad subscription, {0}".format(str(self.subscription_name))
            )


class DeploymentView:
    """View of pipeline configuration conditioned by deployment state."""

    release_view: "ReleaseView"
    deployment_tuple: DeploymentTuple

    def __init__(
        self: U, release_view: T, deployment_state: DeploymentTuple
    ) -> None:
        """Construct ``DeploymentView`` object."""
        self.release_view = release_view
        self.deployment_tuple = deployment_state

        self._validate_deployment_tuple()

    def __matched_subscription_patterns(
        self: U,
        subscription_name: str,
        gitref_patterns: typing.Optional[typing.List[str]],
    ) -> bool:
        """
        Check that the subscription matches any specified patterns.

        If a git reference has not been specified then no conditioning is
        applied and any specified subscriptions will be considered a "match".
        """
        result = True
        this_ref = self.release_view.deployment_context.git_ref
        if this_ref and gitref_patterns:
            not_match = [
                (re.match(x, this_ref) is None) for x in gitref_patterns
            ]
            if all(not_match):
                result = False

        return result

    @property
    def subscriptions(self: U) -> typing.List[SubscriptionView]:
        """
        Provide the subscriptions in this deployment.

        Qualifies subscriptions both by their presence in the deployment
        definitions for the project, and the optional branch patterns
        specified for the subscription.

        Returns:
            List of subscription views in this deployment.
        """
        result: typing.List[SubscriptionView] = list()
        this_id = str(self.deployment_tuple)
        deployment_ids = (
            self.release_view.configuration.deployments.deployment_tuples
        )
        if this_id in deployment_ids:
            for subscription_name in deployment_ids[
                this_id
            ].subscriptions.keys():
                this_subscription = deployment_ids[this_id].subscriptions[
                    subscription_name
                ]
                gitref_patterns = this_subscription.gitref_patterns
                if self.__matched_subscription_patterns(
                    subscription_name, gitref_patterns
                ):
                    result.append(SubscriptionView(self, subscription_name))

        return result

    def _validate_deployment_tuple(self: U) -> None:
        if (
            self.deployment_tuple.release_state
            not in self.release_view.configuration.release_states
        ):
            raise PipelineViewError(
                "Bad release state, {0}".format(str(self.deployment_tuple))
            )

        if (
            self.deployment_tuple.client
            not in self.release_view.configuration.clients.keys()
        ):
            raise PipelineViewError(
                "Bad client, {0}".format(str(self.deployment_tuple))
            )

        if (
            self.deployment_tuple.system
            not in self.release_view.configuration.systems
        ):
            raise PipelineViewError(
                "Bad system, {0}".format(str(self.deployment_tuple))
            )


class ReleaseView:
    """View of pipeline configuration conditioned by release state."""

    configuration: PipelineConfiguration
    deployment_context: DeploymentContext

    def __init__(
        self: T,
        configuration: PipelineConfiguration,
        deployment_context: DeploymentContext,
    ) -> None:
        """Construct ``ReleaseView`` object."""
        self.configuration = configuration
        self.deployment_context = deployment_context

        self._validate_release_state()

    @property
    def deployments(self: T) -> typing.List[DeploymentView]:
        """Provide the deployments in this release."""
        result: typing.List[DeploymentView] = list()
        for this_client in self.configuration.clients.keys():
            for this_system in self.configuration.systems:
                this_state = DeploymentTuple(
                    client=this_client,
                    release_state=self.deployment_context.release_state,
                    system=this_system,
                )
                if (
                    str(this_state)
                    in self.configuration.deployments.deployment_tuples.keys()
                ):
                    result.append(DeploymentView(self, this_state))

        return result

    def flatten(
        self: T,
        to: StructuredTo,
    ) -> typing.List[FlattenedDeployment]:
        """Flatten the nested hierarchy of views into a simple list."""
        result: typing.List[FlattenedDeployment] = list()
        for this_deployment in self.deployments:
            for this_subscription in this_deployment.subscriptions:
                for this_deploy_data in this_subscription.deploy_data:
                    updated_context = copy.deepcopy(self.deployment_context)
                    updated_context.azure_subscription_name = (
                        this_subscription.subscription_name
                    )
                    updated_context.azure_tenant_name = (
                        self.configuration.subscriptions[
                            this_subscription.subscription_name
                        ].tenant
                    )
                    updated_context.client = (
                        this_deployment.deployment_tuple.client
                    )
                    updated_context.system = (
                        this_deployment.deployment_tuple.system
                    )

                    updated_data = copy.deepcopy(this_deploy_data)
                    updated_data.to = to

                    this_value = FlattenedDeployment(
                        context=updated_context,
                        data=updated_data,
                    )
                    result.append(this_value)
        return result

    def _validate_release_state(self: T) -> None:
        if (
            self.deployment_context.release_state
            not in self.configuration.release_states
        ):
            message = "Bad release state, {0}, {1}".format(
                self.deployment_context.release_state,
                str(self.configuration.release_states),
            )
            raise PipelineViewError(message)
