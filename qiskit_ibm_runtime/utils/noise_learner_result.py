# This code is part of Qiskit.
#
# (C) Copyright IBM 2024.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
==================================================================================
NoiseLearner result classes (:mod:`qiskit_ibm_runtime.utils.noise_learner_result`)
==================================================================================

.. autosummary::
   :toctree: ../stubs/

   PauliLindbladError
   LayerError
"""

from __future__ import annotations

from typing import Any, Iterator, Optional, Sequence
from numpy.typing import NDArray
import numpy as np

from qiskit.providers.backend import BackendV2
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import PauliList

import plotly.graph_objects as go

from ..utils.deprecation import issue_deprecation_msg


class PauliLindbladError:
    r"""A Pauli error channel generated by a Pauli Lindblad dissipators.

    This operator represents an N-qubit quantum error channel
    :math:`E(\rho) = e^{\sum_j r_j D_{P_j}}(\rho)` generated by Pauli Lindblad dissipators
    :math:`D_P(\rho) = P \rho P - \rho`, where :math:`P_j` are N-qubit :class:`~.Pauli`
    operators.

    The list of Pauli generator terms are stored as a :class:`~.PauliList` and can be
    accessed via the :attr:`~generators` attribute. The array of dissipator rates
    :math:`r_j` can be accessed via the :attr:`~rates` attribute.

    The equivalent Pauli error channel can be constructed as a composition
    of single-Pauli channel terms

    .. math::

        E = e^{\sum_j r_j D_{P_j}} = \prod_j e^{r_j D_{P_j}}
        = prod_j \left( (1 - p_j) S_I + p_j S_{P_j} \right)

    where :math:`p_j = \frac12 - \frac12 e^{-2 r_j}` [1].

    Args:
        generators: A list of the Pauli Lindblad generators for the error channel.
        rates: A list of the rates for the Pauli-Lindblad ``generators``.

    Raises:
        ValueError: If ``generators`` and ``rates`` have different lengths.

    References:
        1. E. van den Berg, Z. Minev, A. Kandala, K. Temme, *Probabilistic error
           cancellation with sparse Pauli–Lindblad models on noisy quantum processors*,
           Nature Physics volume 19, pages1116–1121 (2023).
           `arXiv:2201.09866 [quant-ph] <https://arxiv.org/abs/2201.09866>`_
    """

    def __init__(self, generators: PauliList, rates: Sequence[float]) -> None:
        self._generators = generators
        self._rates = np.asarray(rates, dtype=float)

        if (len(generators),) != self._rates.shape:
            raise ValueError(
                f"``generators`` has length {len(generators)} "
                f"but ``rates`` has shape {self._rates.shape}."
            )

    @property
    def generators(self) -> PauliList:
        r"""
        The Pauli Lindblad generators of this :class:`~.PauliLindbladError`.
        """
        return self._generators

    @property
    def rates(self) -> NDArray[np.float64]:
        r"""
        The Lindblad generator rates of this quantum error.
        """
        return self._rates

    @property
    def num_qubits(self) -> int:
        r"""
        The number of qubits in this :class:`~.PauliLindbladError`.
        """
        return self.generators.num_qubits

    def restrict_num_bodies(self, num_qubits: int) -> PauliLindbladError:
        r"""
        The :class:`~.PauliLindbladError` containing only those terms acting on exactly
        ``num_qubits`` qubits.

        Args:
            num_qubits: The number of qubits that the returned error acts on.
        
        Returns:
            The error containing only those terms acting on exactly ``num_qubits`` qubits.

        Raises:
            ValueError: If ``num_qubits`` is smaller than ``0``.
        """
        if num_qubits < 0:
            raise ValueError("``num_qubits`` must be ``0`` or larger.")
        mask = np.sum(self.generators.x | self.generators.z, axis=1) == num_qubits
        return PauliLindbladError(self.generators[mask], self.rates[mask])

    def _json(self) -> dict:
        """Return a dictionary containing all the information to re-initialize this object."""
        return {"generators": self.generators, "rates": self.rates}

    def __repr__(self) -> str:
        return f"PauliLindbladError(generators={self.generators}, rates={self.rates.tolist()})"


class LayerError:
    """The error channel (in Pauli-Lindblad format) of a single layer of instructions.

    Args:
        circuit: A circuit whose noise has been learnt.
        qubits: The labels of the qubits in the ``circuit``.
        error: The Pauli Lindblad error channel affecting the ``circuit``.

    Raises:
        ValueError: If ``circuit``, ``qubits``, and ``error`` have mismatching number of qubits.
    """

    def __init__(
        self, circuit: QuantumCircuit, qubits: Sequence[int], error: PauliLindbladError
    ) -> None:
        self._circuit = circuit
        self._qubits = list(qubits)
        self._error = error

        if len({self.circuit.num_qubits, len(self.qubits), self.error.num_qubits}) != 1:
            raise ValueError("Mistmatching numbers of qubits.")

    @property
    def circuit(self) -> QuantumCircuit:
        r"""
        The circuit in this :class:`.~LayerError`.
        """
        return self._circuit

    @property
    def qubits(self) -> list[int]:
        r"""
        The qubits in this :class:`.~LayerError`.
        """
        return self._qubits

    @property
    def error(self) -> PauliLindbladError:
        r"""
        The error channel in this :class:`.~LayerError`.
        """
        return self._error

    @property
    def generators(self) -> PauliList:
        r"""
        (DEPRECATED) The Pauli Lindblad generators of the error channel in this :class:`.~LayerError`.
        """
        issue_deprecation_msg(
            "The ``generators`` property is deprecated",
            "0.27.0",
            "Instead, you can access the generators through the ``error`` property.",
            1,
        )
        return self.error.generators

    @property
    def rates(self) -> NDArray[np.float64]:
        r"""
        (DEPRECATED) The Lindblad generator rates of the error channel in this :class:`.~LayerError`.
        """
        issue_deprecation_msg(
            "The ``rates`` property is deprecated",
            "0.27.0",
            "Instead, you can access the rates through the ``error`` property.",
            1,
        )
        return self.error.rates

    @property
    def num_qubits(self) -> int:
        r"""
        The number of qubits in this :class:`~.LayerError`.
        """
        return len(self.qubits)

    def draw_map(
        self,
        backend: BackendV2,
        coordinates: Optional[list[tuple[int, int]]] = None,
        *,
        colorscale: str = "Bluered",
        color_no_data: str = "lightgray",
        num_edge_segments: int = 16,
        edge_width: float = 4,
        height: int = 500,
        background_color: str = "white",
        radius: float = 0.25,
        width: int = 800,
    ) -> go.Figure:
        r"""
        Draws a map view of a this layer error.

        Args:
            backend: The backend on top of which the layer error is drawn.
            coordinates: A list of coordinates in the form ``(row, column)`` that allow drawing each
                qubit in the given backend on a 2D grid.
            colorscale: The colorscale used to show the rates of this layer error.
            color_no_data: The color used for qubits and edges for which no data is available.
            num_edge_segments: The number of equal-sized segments that edges are made of.
            edge_width: The line width of the edges in pixels.
            height: The height of the returned figure.
            background_color: The background color.
            radius: The radius of the pie charts representing the qubits.
            width: The width of the returned figure.
        """
        # pylint: disable=import-outside-toplevel, cyclic-import
        from ..visualization import draw_layer_error_map

        return draw_layer_error_map(
            self,
            backend,
            coordinates,
            colorscale=colorscale,
            color_no_data=color_no_data,
            num_edge_segments=num_edge_segments,
            edge_width=edge_width,
            height=height,
            background_color=background_color,
            radius=radius,
            width=width,
        )

    def _json(self) -> dict:
        """Return a dictionary containing all the information to re-initialize this object."""
        return {"circuit": self.circuit, "qubits": self.qubits, "error": self.error}

    def __repr__(self) -> str:
        ret = f"circuit={repr(self.circuit)}, qubits={self.qubits}, error={self.error})"
        return f"LayerError({ret})"


class NoiseLearnerResult:
    """A container for the results of a noise learner experiment."""

    def __init__(self, data: Sequence[LayerError], metadata: dict[str, Any] | None = None):
        """
        Args:
            data: The data of a noise learner experiment.
            metadata: Metadata that is common to all pub results; metadata specific to particular
                pubs should be placed in their metadata fields. Keys are expected to be strings.
        """
        self._data = list(data)
        self._metadata = {} if metadata is None else metadata.copy()

    @property
    def data(self) -> list[LayerError]:
        """The data of this noise learner result."""
        return self._data

    @property
    def metadata(self) -> dict[str, Any]:
        """The metadata of this noise learner result."""
        return self._metadata

    def __getitem__(self, index: int) -> LayerError:
        return self.data[index]

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return f"NoiseLearnerResult(data={self.data}, metadata={self.metadata})"

    def __iter__(self) -> Iterator[LayerError]:
        return iter(self.data)
