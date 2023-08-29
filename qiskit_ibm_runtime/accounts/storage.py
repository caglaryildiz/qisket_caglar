# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Utility functions related to storing account configuration on disk."""

import json
import logging
import os
from typing import Optional, Dict
from configparser import ConfigParser
from .exceptions import AccountAlreadyExistsError

logger = logging.getLogger(__name__)


def save_config(
    filename: str, name: str, config: dict, overwrite: bool, default_channel: Optional[str] = None
) -> None:
    """Save configuration data in a JSON file under the given name."""
    logger.debug("Save configuration data for '%s' in '%s'", name, filename)
    _ensure_file_exists(filename)

    with open(filename, mode="r", encoding="utf-8") as json_in:
        data = json.load(json_in)

    if data.get(name) and not overwrite:
        raise AccountAlreadyExistsError(
            f"Named account ({name}) already exists. " f"Set overwrite=True to overwrite."
        )
    if data.get("default_channel") != default_channel and not overwrite:
        raise AccountAlreadyExistsError(
            f"default_channel ({name}) already exists. " f"Set overwrite=True to overwrite."
        )

    with open(filename, mode="w", encoding="utf-8") as json_out:
        data[name] = config
        if default_channel:
            data["default_channel"] = default_channel
        json.dump(data, json_out, sort_keys=True, indent=4)


def read_qiskitrc(qiskitrc_config_file: str) -> Dict[str, str]:
    """Read credentials from a qiskitrc config and return as a dictionary."""
    config_parser = ConfigParser()
    config_parser.read(qiskitrc_config_file)
    account_data = {}
    for name in config_parser.sections():
        account_data = dict(config_parser.items(name))
    return account_data


def read_config(
    filename: str,
    name: Optional[str] = None,
) -> Optional[Dict]:
    """Read configuration data from a JSON file."""
    logger.debug("Read configuration data for '%s' from '%s'", name, filename)
    _ensure_file_exists(filename)

    with open(filename, encoding="utf-8") as json_file:
        data = json.load(json_file)
        if name is None:
            return data
        if name in data:
            return data[name]
        return None


def delete_config(
    filename: str,
    name: str,
) -> bool:
    """Delete configuration data from a JSON file."""

    logger.debug("Delete configuration data for '%s' from '%s'", name, filename)

    _ensure_file_exists(filename)
    with open(filename, mode="r", encoding="utf-8") as json_in:
        data = json.load(json_in)

    if name in data:
        with open(filename, mode="w", encoding="utf-8") as json_out:
            del data[name]
            json.dump(data, json_out, sort_keys=True, indent=4)
            return True

    return False


def _ensure_file_exists(filename: str, initial_content: str = "{}") -> None:
    if not os.path.isfile(filename):
        logger.debug("Create empty configuration file at %s", filename)

        # create parent directories
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # initialize file
        with open(filename, mode="w", encoding="utf-8") as json_file:
            json_file.write(initial_content)
