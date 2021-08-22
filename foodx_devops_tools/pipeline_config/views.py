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
import typing

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
        pipeline_id: str,
        release_id: str,
        release_state: str,
    ) -> None:
        """Construct ``DeploymentContext`` object."""
        self.commit_sha = commit_sha
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

    def __str__(self: Y) -> str:
        """Convert object to str for logging purposes."""
        return str(
            {
                "commit_sha": self.commit_sha,
                "pipeline_id": self.pipeline_id,
                "release_id": self.release_id,
                "release_state": self.release_state,
                "application_name": self.__application_name,
                "azure_subscription_name": self.__azure_subscription_name,
                "azure_tenant_name": self.__azure_tenant_name,
                "client": self.__client,
                "frame_name": self.__frame_name,
                "system": self.__system,
            }
        )


X = typing.TypeVar("X", bound="DeployDataView")


class DeployDataView:
    """Data critical to a resource deployment."""

    ado_service_connection: str
    azure_subscription_name: str
    azure_tenant_name: str
    deployment_tuple: str
    location_primary: str
    release_state: str

    __location_secondary: typing.Optional[str] = None

    iteration_context: IterationContext
    __puff_map: typing.Optional[PuffMap] = None

    def __init__(
        self: X,
        ado_service_connection: str,
        azure_subscription_name: str,
        azure_tenant_name: str,
        deployment_tuple: str,
        location_primary: str,
        release_state: str,
        location_secondary: typing.Optional[str] = None,
    ) -> None:
        """Construct ``DeployDataView`` object."""
        self.ado_service_connection = ado_service_connection
        self.azure_subscription_name = azure_subscription_name
        self.azure_tenant_name = azure_tenant_name
        self.deployment_tuple = deployment_tuple
        self.location_primary = location_primary
        self.release_state = release_state
        self.__location_secondary = location_secondary

        self.iteration_context = IterationContext()

    @property
    def location_secondary(self: X) -> str:
        """Get location secondary property."""
        if self.__location_secondary:
            return self.__location_secondary
        else:
            raise PipelineViewError(
                "location secondary not specified in " "deployment data"
            )

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
                "ado_service_connection": self.ado_service_connection,
                "azure_subscription_name": self.azure_subscription_name,
                "azure_tenant_name": self.azure_tenant_name,
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
        this_deployment = (
            self.deployment_view.release_view.configuration.deployments[
                str(self.deployment_view.deployment_tuple)
            ]
        )
        for this_locations in this_deployment.subscriptions[
            self.subscription_name
        ].locations:
            this_data: typing.Dict[str, typing.Any] = {
                "ado_service_connection": base_data.ado_service_connection,
                "azure_subscription_name": self.subscription_name,
                "azure_tenant_name": base_data.tenant,
                "deployment_tuple": str(self.deployment_view.deployment_tuple),
                "location_primary": this_locations.primary,
                "location_secondary": None,
                "release_state": self.deployment_view.release_view.deployment_context.release_state,  # noqa E501
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

    @property
    def subscriptions(self: U) -> typing.List[SubscriptionView]:
        """Provide the subscriptions in this deployment."""
        result: typing.List[SubscriptionView] = list()
        if (
            str(self.deployment_tuple)
            in self.release_view.configuration.deployments
        ):
            for (
                this_subscription
            ) in self.release_view.configuration.deployments[
                str(self.deployment_tuple)
            ].subscriptions.keys():
                result.append(SubscriptionView(self, this_subscription))

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
                if str(this_state) in self.configuration.deployments.keys():
                    result.append(DeploymentView(self, this_state))

        return result

    def flatten(
        self: T,
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

                    this_value = FlattenedDeployment(
                        context=updated_context,
                        data=this_deploy_data,
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
