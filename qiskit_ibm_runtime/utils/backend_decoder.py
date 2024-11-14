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

"""Utilities for working with IBM Quantum backends."""

from typing import List, Dict, Union, Optional
import logging
import traceback

import dateutil.parser
from ..models import (
    BackendProperties,
    PulseDefaults,
    PulseBackendConfiguration,
    QasmBackendConfiguration,
)

from .converters import utc_to_local_all

logger = logging.getLogger(__name__)

FRACTIONAL_GATES = ("rzz", "rx")
DYNAMIC_INSTRUCTIONS = ("if_else", "while_loop", "for_loop", "switch_case")


def configuration_from_server_data(
    raw_config: Dict,
    instance: str = "",
    use_fractional_gates: Optional[bool] = False,
) -> Optional[Union[QasmBackendConfiguration, PulseBackendConfiguration]]:
    """Create an IBMBackend instance from raw server data.

    Args:
        raw_config: Raw configuration.
        instance: Service instance.
        use_fractional_gates: Set True to allow for the backends to include
            fractional gates. See :meth:`~.QiskitRuntimeService.backends`
                for further details.

    Returns:
        Backend configuration.
    """
    # Make sure the raw_config is of proper type
    if not isinstance(raw_config, dict):
        logger.warning(  # type: ignore[unreachable]
            "An error occurred when retrieving backend "
            "information. Some backends might not be available."
        )
        return None
    try:
        decode_backend_configuration(raw_config)
        filter_raw_configuration(raw_config, use_fractional_gates=use_fractional_gates)
        try:
            return PulseBackendConfiguration.from_dict(raw_config)
        except (KeyError, TypeError):
            return QasmBackendConfiguration.from_dict(raw_config)
    except Exception:  # pylint: disable=broad-except
        logger.warning(
            'Remote backend "%s" for service instance %s could not be instantiated due '
            "to an invalid server-side configuration",
            raw_config.get("backend_name", raw_config.get("name", "unknown")),
            repr(instance),
        )
        logger.debug("Invalid device configuration: %s", traceback.format_exc())
    return None


def filter_raw_configuration(
    raw_config: dict, use_fractional_gates: Optional[bool] = False
) -> None:
    """Filter unwanted entries from raw configuration data

    Args:
        use_fractional_gates: Set True to allow for the backends to include
            fractional gates. See :meth:`~.QiskitRuntimeService.backends`
                for further details.
    """
    if use_fractional_gates is None:
        return

    if use_fractional_gates:
        if "supported_instructions" in raw_config:
            raw_config["supported_instructions"] = [
                i for i in raw_config["supported_instructions"] if i not in DYNAMIC_INSTRUCTIONS
            ]
        if "supported_features" in raw_config:
            raw_config["supported_features"] = [
                g for g in raw_config["supported_features"] if g != "qasm3"
            ]
    else:
        if "basis_gates" in raw_config:
            raw_config["basis_gates"] = [
                g for g in raw_config["basis_gates"] if g not in FRACTIONAL_GATES
            ]
        if "gates" in raw_config:
            raw_config["gates"] = [
                g for g in raw_config["gates"] if g.get("name") not in FRACTIONAL_GATES
            ]
        if "supported_instructions" in raw_config:
            raw_config["supported_instructions"] = [
                i for i in raw_config["supported_instructions"] if i not in FRACTIONAL_GATES
            ]


def defaults_from_server_data(defaults: Dict) -> PulseDefaults:
    """Decode pulse defaults data.

    Args:
        defaults: Raw pulse defaults data.

    Returns:
        A ``PulseDefaults`` instance.
    """
    for item in defaults["pulse_library"]:
        _decode_pulse_library_item(item)

    for cmd in defaults["cmd_def"]:
        if "sequence" in cmd:
            for instr in cmd["sequence"]:
                _decode_pulse_qobj_instr(instr)

    return PulseDefaults.from_dict(defaults)


def properties_from_server_data(properties: Dict) -> BackendProperties:
    """Decode backend properties.

    Args:
        properties: Raw properties data.

    Returns:
        A ``BackendProperties`` instance.
    """
    if isinstance(properties["last_update_date"], str):
        properties["last_update_date"] = dateutil.parser.isoparse(properties["last_update_date"])
        for qubit in properties["qubits"]:
            for nduv in qubit:
                nduv["date"] = dateutil.parser.isoparse(nduv["date"])
        for gate in properties["gates"]:
            for param in gate["parameters"]:
                param["date"] = dateutil.parser.isoparse(param["date"])
        for gen in properties["general"]:
            gen["date"] = dateutil.parser.isoparse(gen["date"])

    properties = utc_to_local_all(properties)
    return BackendProperties.from_dict(properties)


def decode_backend_configuration(config: Dict) -> None:
    """Decode backend configuration.

    Args:
        config: A ``QasmBackendConfiguration`` or ``PulseBackendConfiguration``
            in dictionary format.
    """
    config["online_date"] = dateutil.parser.isoparse(config["online_date"])

    if "u_channel_lo" in config:
        for u_channel_list in config["u_channel_lo"]:
            for u_channel_lo in u_channel_list:
                u_channel_lo["scale"] = _to_complex(u_channel_lo["scale"])


# TODO: remove this when no longer needed server-side
_decode_backend_configuration = decode_backend_configuration


def _to_complex(value: Union[List[float], complex]) -> complex:
    """Convert the input value to type ``complex``.

    Args:
        value: Value to be converted.

    Returns:
        Input value in ``complex``.

    Raises:
        TypeError: If the input value is not in the expected format.
    """
    if isinstance(value, list) and len(value) == 2:
        return complex(value[0], value[1])
    elif isinstance(value, complex):
        return value

    raise TypeError("{} is not in a valid complex number format.".format(value))


def _decode_pulse_library_item(pulse_library_item: Dict) -> None:
    """Decode a pulse library item.

    Args:
        pulse_library_item: A ``PulseLibraryItem`` in dictionary format.
    """
    pulse_library_item["samples"] = [
        _to_complex(sample) for sample in pulse_library_item["samples"]
    ]


def _decode_pulse_qobj_instr(pulse_qobj_instr: Dict) -> None:
    """Decode a pulse Qobj instruction.

    Args:
        pulse_qobj_instr: A ``PulseQobjInstruction`` in dictionary format.
    """
    if "val" in pulse_qobj_instr:
        pulse_qobj_instr["val"] = _to_complex(pulse_qobj_instr["val"])
    if "parameters" in pulse_qobj_instr and "amp" in pulse_qobj_instr["parameters"]:
        pulse_qobj_instr["parameters"]["amp"] = _to_complex(pulse_qobj_instr["parameters"]["amp"])
