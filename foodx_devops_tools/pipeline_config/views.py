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

from ..deployment import DeploymentState
from .pipeline import PipelineConfiguration

log = logging.getLogger(__name__)


class PipelineViewError(Exception):
    """Problem with view data."""


@dataclasses.dataclass
class DeploymentContext:
    """Deployment context data expected to be applied to resource tags."""

    commit_sha: str
    pipeline_id: str
    release_id: str
    release_state: str

    # these data must be provided at deployment time because they are more
    # deeply context sensitive.
    application_name: typing.Optional[str] = None
    azure_subscription_name: typing.Optional[str] = None
    azure_tenant_name: typing.Optional[str] = None
    client: typing.Optional[str] = None
    frame_name: typing.Optional[str] = None
    system: typing.Optional[str] = None


@dataclasses.dataclass
class DeployDataView:
    """Data critical to a resource deployment."""

    ado_service_connection: str
    azure_subscription_name: str
    azure_tenant_name: str
    deployment_state: str
    location_primary: str
    location_secondary: typing.Optional[str]
    release_state: str


@dataclasses.dataclass
class FlattenedDeployment:
    """Flattened deployment data for deployment concurrency."""

    context: DeploymentContext
    data: DeployDataView


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
                str(self.deployment_view.deployment_state)
            ]
        )
        for this_locations in this_deployment.subscriptions[
            self.subscription_name
        ].locations:
            this_data: typing.Dict[str, typing.Any] = {
                "ado_service_connection": base_data.ado_service_connection,
                "azure_subscription_name": self.subscription_name,
                "azure_tenant_name": base_data.tenant,
                "deployment_state": str(self.deployment_view.deployment_state),
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
    deployment_state: DeploymentState

    def __init__(
        self: U, release_view: T, deployment_state: DeploymentState
    ) -> None:
        """Construct ``DeploymentView`` object."""
        self.release_view = release_view
        self.deployment_state = deployment_state

        self._validate_deployment_state()

    @property
    def subscriptions(self: U) -> typing.List[SubscriptionView]:
        """Provide the subscriptions in this deployment."""
        result: typing.List[SubscriptionView] = list()
        if (
            str(self.deployment_state)
            in self.release_view.configuration.deployments
        ):
            for (
                this_subscription
            ) in self.release_view.configuration.deployments[
                str(self.deployment_state)
            ].subscriptions.keys():
                result.append(SubscriptionView(self, this_subscription))

        return result

    def _validate_deployment_state(self: U) -> None:
        if (
            self.deployment_state.release_state
            not in self.release_view.configuration.release_states
        ):
            raise PipelineViewError(
                "Bad release state, {0}".format(str(self.deployment_state))
            )

        if (
            self.deployment_state.client
            not in self.release_view.configuration.clients.keys()
        ):
            raise PipelineViewError(
                "Bad client, {0}".format(str(self.deployment_state))
            )

        if (
            self.deployment_state.system
            not in self.release_view.configuration.systems
        ):
            raise PipelineViewError(
                "Bad system, {0}".format(str(self.deployment_state))
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
                this_state = DeploymentState(
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
                        this_deployment.deployment_state.client
                    )
                    updated_context.system = (
                        this_deployment.deployment_state.system
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
