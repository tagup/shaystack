# -*- coding: utf-8 -*-
# JSON Grid dumper
# See the accompanying LICENSE file.
# (C) 2018 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Save a `Grid` in JSON file, conform with the specification describe
here (https://www.project-haystack.org/doc/Json)
"""
from __future__ import unicode_literals

import datetime
import functools
import json
from typing import Dict, Optional, Tuple, List, Any, Union

from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
    MARKER, NA, REMOVE, XStr
from .grid import Grid
from .jsonparser import MARKER_STR, NA_STR, REMOVE2_STR, REMOVE3_STR
from .metadata import MetadataObject
from .sortabledict import SortableDict
from .version import LATEST_VER, VER_3_0, Version
from .zoneinfo import timezone_name


def dump_grid(grid: Grid) -> str:
    """
    Dump a grid to JSON
    Args:
        grid: The grid.
    Returns:
        A json string
    """
    return json.dumps(_dump_grid_to_json(grid))


def _dump_grid_to_json(grid: Grid) -> Dict[str, Union[List[str], Dict[str, str]]]:
    """
    Convert a grid to JSON object
    Args:
        grid: The grid to dump
    Returns:
        A json object.
    """
    return {
        'meta': _dump_meta(grid.metadata, version=grid.version, for_grid=True),
        'cols': _dump_columns(grid.column, version=grid.version),
        'rows': _dump_rows(grid),
    }


def _dump_meta(meta: MetadataObject,
               version: Version = LATEST_VER,
               for_grid: Optional[bool] = False) -> Dict[str, str]:
    _dump = functools.partial(_dump_meta_item, version=version)
    _meta = dict(map(_dump, list(meta.items())))
    if for_grid:
        _meta['ver'] = str(version)
    return _meta


def _dump_meta_item(item: str, version: Version = LATEST_VER) \
        -> Tuple[str, Union[None, bool, str, List[str], Dict[str, Any]]]:
    (item_id, item_value) = item
    return (_dump_id(item_id),
            _dump_scalar(item_value, version=version))


def _dump_columns(cols: SortableDict, version: Version = LATEST_VER) -> List[str]:
    _dump = functools.partial(_dump_column, version=version)
    _cols = list(zip(*list(cols.items())))
    return list(map(_dump, *_cols))


def _dump_column(col: str, col_meta: MetadataObject, version: Version = LATEST_VER) -> Dict[str, str]:
    if bool(col_meta):
        _meta = _dump_meta(col_meta, version=version)
    else:
        _meta = {}
    _meta['name'] = col
    return _meta


def _dump_rows(grid: Grid) -> List[str]:
    return list(map(functools.partial(_dump_row, grid), grid))


def _dump_row(grid: Grid, row: Dict[str, Any]) -> Dict[str, str]:
    return {
        c: _dump_scalar(row.get(c), version=grid.version)
        for c in list(grid.column.keys()) if c in row
    }


def _dump_scalar(scalar: Any, version: Version = LATEST_VER) \
        -> Union[None, str, bool, List[str], Dict[str, Any]]:
    if scalar is None:
        return None
    if scalar is MARKER:
        return MARKER_STR
    if scalar is NA:
        if version < VER_3_0:
            raise ValueError('Project Haystack %s '
                             'does not support NA' % version)
        return NA_STR
    if scalar is REMOVE:
        if version < VER_3_0:
            return REMOVE2_STR
        return REMOVE3_STR
    if isinstance(scalar, list):
        return _dump_list(scalar, version=version)
    if isinstance(scalar, dict):
        return _dump_dict(scalar, version=version)
    if isinstance(scalar, bool):
        return _dump_bool(scalar)
    if isinstance(scalar, Ref):
        return _dump_ref(scalar)
    if isinstance(scalar, Bin):
        return _dump_bin(scalar)
    if isinstance(scalar, XStr):
        return _dump_xstr(scalar)
    if isinstance(scalar, Uri):
        return _dump_uri(scalar)
    if isinstance(scalar, str):
        return _dump_str(scalar)
    if isinstance(scalar, datetime.datetime):
        return _dump_date_time(scalar)
    if isinstance(scalar, datetime.time):
        return _dump_time(scalar)
    if isinstance(scalar, datetime.date):
        return _dump_date(scalar)
    if isinstance(scalar, Coordinate):
        return _dump_coord(scalar)
    if isinstance(scalar, Quantity):
        return _dump_quantity(scalar)
    if isinstance(scalar, (float, int)):
        return _dump_decimal(scalar)
    if isinstance(scalar, Grid):
        return _dump_grid_to_json(scalar)
    raise NotImplementedError('Unhandled case: %r' % scalar)


def _dump_id(id_str: str) -> str:
    return id_str


def _dump_str(str_value: str) -> str:
    return 's:%s' % str_value


def _dump_uri(uri_value: Uri) -> str:
    return 'u:%s' % uri_value


def _dump_bin(bin_value: Bin) -> str:
    return 'b:%s' % bin_value


def _dump_xstr(xstr_value: XStr) -> str:
    return 'x:%s:%s' % (xstr_value.encoding, xstr_value.data_to_string())


def _dump_quantity(quantity: Quantity) -> str:
    if (quantity.units is None) or (quantity.units == ''):
        return _dump_decimal(quantity.m)
    return 'n:%f %s' % (quantity.m, quantity.symbol)


def _dump_decimal(decimal: float) -> str:
    return 'n:%f' % decimal


def _dump_bool(bool_value: bool) -> bool:
    return bool_value


def _dump_coord(coordinate: Coordinate) -> str:
    return 'c:%f,%f' % (coordinate.latitude, coordinate.longitude)


def _dump_ref(ref: Ref) -> str:
    if ref.has_value:
        return 'r:%s %s' % (ref.name, ref.value)
    return 'r:%s' % ref.name


def _dump_date(date: datetime.date) -> str:
    return 'd:%s' % date.isoformat()


def _dump_time(time: datetime.time) -> str:
    return 'h:%s' % time.isoformat()


def _dump_date_time(date_time: datetime.datetime) -> str:
    tz_name = timezone_name(date_time)
    return 't:%s %s' % (date_time.isoformat(), tz_name)


def _dump_list(lst: List[Any], version: Version = LATEST_VER) -> List[str]:
    if version < VER_3_0:
        raise ValueError('Project Haystack %s '
                         'does not support lists' % version)
    return list(map(functools.partial(_dump_scalar, version=version), lst))


def _dump_dict(dic: Dict[str, Any], version: Version = LATEST_VER) -> Dict[str, str]:
    if version < VER_3_0:
        raise ValueError('Project Haystack %s '
                         'does not support dict' % version)
    return {k: _dump_scalar(v, version=version) for (k, v) in dic.items()}


def dump_scalar(scalar: Any, version: Version = LATEST_VER) -> str:
    """
    Dump a scalar to JSON
    Args:
        scalar: The scalar value
        version: The Haystack version
    Returns:
        The JSON string
    """
    return json.dumps(_dump_scalar(scalar, version))
