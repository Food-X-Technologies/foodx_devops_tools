#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Pydantic model of puff parameter data."""

import typing

import pydantic

PuffRegionVariables = typing.Dict[str, typing.Any]

PuffRegionValues = typing.Dict[str, typing.Optional[PuffRegionVariables]]

T = typing.TypeVar("T", bound="PuffRegion")


class PuffRegion(pydantic.BaseModel):
    """
    Puff parameter region (singular) data model.

    Region data is a dictionary of variable names and values to be applied.
    """

    __root__: PuffRegionValues

    def __getitem__(self: T, item: str) -> typing.Optional[PuffRegionVariables]:
        """Get region parameters."""
        return self.__root__[item]

    def __contains__(self: T, item: str) -> bool:
        """Verify the region contains a parameter."""
        return item in self.__root__

    @pydantic.root_validator(pre=True)
    def check_single_entry(
        cls: pydantic.BaseModel,
        values: typing.Dict[str, typing.Dict[str, typing.Any]],
    ) -> dict:
        """Check that a single name entry exists."""
        assert values
        # ignore this mypy error:
        #   error: Argument 1 to "len" has incompatible type \
        #     "Optional[Dict[str, Any]]"; expected "Sized"  [arg-type]
        if len(values.get("__root__")) > 1:  # type: ignore
            raise ValueError(
                "must only specify a single name in a region entry"
            )
        return values


PuffRegionsValues = typing.List[PuffRegion]


U = typing.TypeVar("U", bound="PuffRegions")


class PuffRegions(pydantic.BaseModel):
    """Puff parameter regions data model."""

    __root__: PuffRegionsValues

    def __getitem__(self: U, item: int) -> PuffRegion:
        """Get a region item."""
        return self.__root__[item]

    @pydantic.root_validator(pre=True)
    def check_regions(cls: pydantic.BaseModel, values: dict) -> dict:
        """
        Check that regions are formulated correctly.

        Args:
            values:

        Returns:
            Reviewed region values.
        """
        this_values = values.get("__root__")
        if not isinstance(this_values, list):
            raise ValueError("")
        for k in range(0, len(this_values)):
            PuffRegion.parse_obj(this_values[k])
        return values


PuffEnvironmentValues = typing.Dict[str, typing.Any]


V = typing.TypeVar("V", bound="PuffEnvironment")


class PuffEnvironment(pydantic.BaseModel):
    """Puff parameter environment (singular) data model."""

    __root__: PuffEnvironmentValues

    @pydantic.root_validator(pre=True)
    def check_regions(cls: pydantic.BaseModel, values: dict) -> dict:
        """Verify validity of region entries."""
        # ignore this mypy error:
        #    error: Unsupported right operand type for in \
        #      ("Optional[Any]")  [operator]
        if "regions" in values.get("__root__"):  # type: ignore
            PuffRegions.parse_obj(values["__root__"]["regions"])
        return values

    def __getitem__(self: V, item: str) -> typing.Any:
        """Get environment item."""
        return self.__root__[item]

    def __contains__(self: V, item: str) -> bool:
        """Verify that an environment contains the specific item."""
        return item in self.__root__


W = typing.TypeVar("W", bound="PuffEnvironments")


class PuffEnvironments(pydantic.BaseModel):
    """Puff parameter environments data model."""

    __root__: typing.Dict[str, typing.Optional[PuffEnvironment]]

    def __getitem__(self: W, item: str) -> typing.Optional[PuffEnvironment]:
        """Get named environment entry."""
        return self.__root__[item]

    def __contains__(self: W, item: str) -> bool:
        """Verify that environments contains the named environment."""
        return item in self.__root__


PuffServiceValues = typing.Dict[str, typing.Any]


X = typing.TypeVar("X", bound="PuffService")


class PuffService(pydantic.BaseModel):
    """Puff parameter service (singular) data model."""

    __root__: PuffServiceValues

    @pydantic.root_validator(pre=True)
    def check_environments(cls: pydantic.BaseModel, values: dict) -> dict:
        """Check validity of environments structure."""
        if "environments" in values:
            PuffEnvironments.parse_obj(values["environments"])
        return values

    def __getitem__(self: X, item: str) -> typing.Any:
        """Get the specified item from a service."""
        return self.__root__[item]

    def __contains__(self: X, item: str) -> bool:
        """Verify that a service contains the named item."""
        return item in self.__root__


Y = typing.TypeVar("Y", bound="PuffServices")


class PuffServices(pydantic.BaseModel):
    """Puff parameter services data model."""

    __root__: typing.Dict[str, PuffService]

    def __getitem__(self: Y, item: str) -> PuffService:
        """Get the named service."""
        return self.__root__[item]

    def __contains__(self: Y, item: str) -> bool:
        """Verify that the named service is in the services list."""
        return item in self.__root__


PuffModelValues = typing.Dict[str, typing.Any]


Z = typing.TypeVar("Z", bound="PuffParameterModel")


class PuffParameterModel(pydantic.BaseModel):
    """Data model for puff parameters."""

    __root__: PuffModelValues

    def __getitem__(self: Z, item: str) -> typing.Any:
        """Get the name item from the puff parameters."""
        return self.__root__[item]

    def __contains__(self: Z, item: str) -> bool:
        """Verify that the puff parameters contains the specified item."""
        return item in self.__root__

    @pydantic.root_validator(pre=True)
    def check_structured_elements(
        cls: pydantic.BaseModel, values: dict
    ) -> dict:
        """Check validity of puff parameters structure."""
        if "environments" in values["__root__"]:
            PuffEnvironments.parse_obj(values["__root__"]["environments"])

        if "services" in values["__root__"]:
            PuffServices.parse_obj(values["__root__"]["services"])

        return values
