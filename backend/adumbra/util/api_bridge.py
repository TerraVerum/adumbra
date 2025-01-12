"""
Functions assisting the handoff of data between server <-> client. Things like paginating
data queries, jsonifying data, etc.
"""

import json
import typing as t
from dataclasses import asdict, dataclass
from datetime import timedelta

if t.TYPE_CHECKING:
    from mongoengine import Document, QuerySet


class SupportsSlice(t.Protocol):
    def __getitem__(self, key: slice) -> t.Self: ...


Sliceable_T = t.TypeVar("Sliceable_T", bound=SupportsSlice)


def to_human_timedelta_str(td_object: timedelta) -> str:
    """
    Convert a timedelta object to a human-readable string. Converts a datetime.timedelta
    object into a string representation using the largest applicable time unit (years,
    months, days, hours, minutes, or seconds).

    Parameters
    ----------
    td_object
        The timedelta object to convert

    Returns
    -------
    str
        A human-readable string representing the time duration (e.g., "2 years" or "1
        hour")

    Examples
    --------
    >>> from datetime import timedelta
    >>> to_human_timedelta(timedelta(days=365))
    '1 year'
    >>> to_human_timedelta(timedelta(hours=25))
    '1 day, 1 hour'
    """

    seconds = int(td_object.total_seconds())
    periods = [
        ("year", 60 * 60 * 24 * 365),
        ("month", 60 * 60 * 24 * 30),
        ("day", 60 * 60 * 24),
        ("hour", 60 * 60),
        ("minute", 60),
        ("second", 1),
    ]

    strings = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            has_s = "s" if period_value > 1 else ""
            strings.append(f"{period_value} {period_name}{has_s}")
            break

    return ", ".join(strings)


# See https://github.com/pylint-dev/pylint/issues/2411. Pylint thinks mongo stuff
# isn't imported since it's guarded by TYPE_CHECKING (common practice). Workaround
# is to use stringified type references.
@t.overload
def queryset_to_json(objs: "Document") -> dict: ...
@t.overload
def queryset_to_json(objs: "QuerySet") -> list[dict]: ...
def queryset_to_json(objs: "QuerySet | Document") -> dict | list[dict]:
    """
    Convert a MongoEngine QuerySet to a list of dictionaries, removing the leading
    underscore from the ID field.

    Parameters
    ----------
    objs
        The QuerySet to convert

    Returns
    -------
    list[dict]
        A list of dictionaries representing the QuerySet
    """

    objects_list = json.loads(objs.to_json().replace('"_id"', '"id"'))
    return objects_list


@dataclass
class Pagination:
    """
    A class to represent pagination data. NOTE: `first_item` and `last_item` are
    1-indexed, so use the `slice_objects` method to get the correct subset of objects
    in code.
    """

    total_results: int = 0
    total_pages: int = 0
    page: int = 0
    first_item: int = 0
    last_item: int = 0

    @classmethod
    def from_count_and_page(cls, n_objects: int, page_size: int | None, page: int):
        if page_size is None:
            page_size = n_objects
        pages = int((n_objects - 1) / page_size) + 1
        page = min(max(1, page), pages)
        return cls(
            total_results=n_objects,
            total_pages=pages,
            page=page,
            first_item=(page - 1) * page_size + 1,
            last_item=min(page * page_size, n_objects),
        )

    def slice_objects(self, objects: Sliceable_T) -> Sliceable_T:
        """Returns the subset of objects on the current page."""
        return objects[(self.first_item - 1) : self.last_item]

    def to_dict(self):
        return asdict(self)
