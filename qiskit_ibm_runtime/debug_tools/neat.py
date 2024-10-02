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

"""A class to help understand the expected performance of estimator jobs."""

from __future__ import annotations
from typing import Optional, Sequence, List
import numpy as np

from qiskit.transpiler.passmanager import PassManager
from qiskit.primitives.containers import EstimatorPubLike
from qiskit.primitives.containers.estimator_pub import EstimatorPub
from qiskit.providers import BackendV2 as Backend

from qiskit_ibm_runtime.debug_tools.neat_results import NeatPubResult, NeatResult
from qiskit_ibm_runtime.transpiler.passes.cliffordization import ConvertISAToClifford
from qiskit_ibm_runtime.utils import validate_estimator_pubs, validate_isa_circuits


try:
    from qiskit_aer.noise import NoiseModel
    from qiskit_aer.primitives.estimator_v2 import EstimatorV2 as AerEstimator

    HAS_QISKIT_AER = True
except ImportError:
    HAS_QISKIT_AER = False


def _validate_pubs(
    backend: Backend, pubs: List[EstimatorPub], validate_clifford: bool = True
) -> None:
    r"""Validate a list of PUBs for use inside the neat class.

    This funtion runs the :meth:`.~validate_estimator_pubs` and :meth:`.~validate_isa_circuits`
    checks. Optionally, it also validates that every PUB's circuit is a Clifford circuit.

    Args:
        backend: A backend.
        pubs: A set of PUBs.
        validate_clifford: Whether or not to validate that the PUB's circuit do not contain
            non-Clifford gates.

    Raises:
        ValueError: If the PUBs contain non-Clifford circuits.
    """
    validate_estimator_pubs(pubs)
    validate_isa_circuits([pub.circuit for pub in pubs], backend.target)

    if validate_clifford:
        for pub in pubs:
            for instr in pub.circuit:
                op = instr.operation
                # ISA circuits contain only one type of non-Clifford gate, namely RZ
                if op.name == "rz" and op.params[0] not in [0, np.pi / 2, np.pi, 3 * np.pi / 2]:
                    raise ValueError(
                        "Given ``pubs`` contain non-Clifford circuits. To fix, consider using the "
                        "``.to_clifford`` method of ``Neat`` to map the PUBs' circuits to Clifford"
                        " circuits, then try again."
                    )


class Neat:
    r"""A class to help understand the expected performance of estimator jobs.

    The "Noisy Estimator Analyzer Tool" (or "NEAT") is a convenience tool that users of the
    :class:`~.Estimator` primitive can employ to analyze and predict the performance of
    their queries. Its simulate method uses ``qiskit-aer`` to simulate the estimation task
    classically efficiently, either in ideal conditions or in the presence of noise. The
    simulations' results can be compared with other simulation results or with primitive results
    results to draw custom figures of merit.

    .. code::python

        # Initialize a Neat object
        analyzer = Neat(backend)

        # Map arbitrary PUBs to Clifford PUBs
        cliff_pubs = analyzer.to_clifford(pubs)

        # Calculate the expectation values in the absence of noise
        r_ideal = analyzer.simulate(cliff_pubs, with_noise=False)

        # Calculate the expectation values in the presence of noise
        r_noisy = analyzer.simulate(cliff_pubs, with_noise=True)

        # Calculate the expectation values for a different noise model
        analyzer.noise_model = another_noise_model
        another_r_noisy = analyzer.simulate(cliff_pubs, with_noise=True)

        # Run the Clifford PUBs on a QPU
        r_qpu = estimator.run(cliff_pubs)

        # Calculate useful figures of merit using mathematical operators, for example the relative
        # difference between experimental and noisy results, ...
        rel_diff = abs(r_noisy[0] - r_qpu[0]) / r_noisy[0]

        # ... the signal-to-noise ratio between experimental and ideal results, ...
        ratio = r_qpu[0] / r_ideal[0]

        # ... or the absolute difference between results obtained with different noise models
        abs_diff = abs(r_noisy[0] - another_r_noisy[0])

    Args:
        backend: A backend.
        noise_model: A noise model for the operations of the given backend. If ``None``, it
            defaults to the noise model generated by :meth:`NoiseModel.from_backend`.
    """

    def __init__(self, backend: Backend, noise_model: Optional[NoiseModel] = None) -> None:
        if not HAS_QISKIT_AER:
            raise ValueError(
                "Cannot initialize object of type 'Neat' since 'qiskit-aer' is not installed. "
                "Install 'qiskit-aer' and try again."
            )

        self._backend = backend
        self._noise_model = (
            noise_model
            if noise_model is not None
            else NoiseModel.from_backend(backend, thermal_relaxation=False)
        )

    @property
    def noise_model(self) -> NoiseModel:
        r"""
        The noise model used by this analyzer tool for the noisy simulations.
        """
        return self._noise_model

    @noise_model.setter
    def noise_model(self, value: NoiseModel) -> NoiseModel:
        """Sets a new noise model.

        Args:
            value: A new noise model.
        """
        self._noise_model = value

    def backend(self) -> Backend:
        r"""
        The backend used by this analyzer tool.
        """
        return self._backend

    def simulate(
        self,
        pubs: Sequence[EstimatorPubLike],
        with_noise: bool = True,
        cliffordize: bool = False,
        seed_simulator: Optional[int] = None,
        precision: float = 0,
    ) -> NeatResult:
        r"""
        Calculates the expectation values for the estimator task specified by the given ``pubs``.

        This function uses ``qiskit-aer``'s ``Estimator`` class to simulate the estimation task
        classically.

        .. note::
            To ensure scalability, every circuit in ``pubs`` is required to be a Clifford circuit,
            so that it can be simulated efficiently regardless of its size. For estimation tasks
            that involve non-Clifford circuits, the recommended workflow consists of mapping
            the non-Clifford circuits to the nearest Clifford circuits using the
            :class:`.~ConvertISAToClifford` transpiler pass, or equivalently, to use the Neat's
            :meth:`to_clifford` convenience method. Alternatively, setting ``cliffordize`` to
            ``True`` ensures that the :meth:`to_clifford` method is applied automatically to the
            given ``pubs`` prior to the simulation.

        Args:
            pubs: The PUBs specifying the estimation task of interest.
            with_noise: Whether to perform an ideal, noiseless simulation (``False``) or a noisy
                simulation (``True``).
            cliffordize: Whether or not to automatically apply the
                :class:`.~ConvertISAToClifford` transpiler pass to the given ``pubs`` before
                performing the simulations.
            seed_simulator: A seed for the simulator.
            precision: The default precision used to run the ideal and noisy simulations.

        Returns:
            The results of the simulation.
        """
        if cliffordize:
            coerced_pubs = self.to_clifford(pubs)
        else:
            _validate_pubs(self.backend(), coerced_pubs := [EstimatorPub.coerce(p) for p in pubs])

        backend_options = {
            "method": "stabilizer",
            "noise_model": self.noise_model if with_noise else None,
            "seed_simulator": seed_simulator,
        }
        estimator = AerEstimator(
            options={"backend_options": backend_options, "precision": precision}
        )

        pub_results = [NeatPubResult(r.data.evs) for r in estimator.run(coerced_pubs).result()]
        return NeatResult(pub_results)

    def to_clifford(self, pubs: Sequence[EstimatorPubLike]) -> list[EstimatorPub]:
        r"""
        Return the cliffordized version of the given ``pubs``.

        This convenience method runs the :class:`.~ConvertISAToClifford` transpiler pass on the
        PUBs' circuits.

        Args:
            pubs: The PUBs to turn into Clifford PUBs.

        Returns:
            The Clifford PUBs.
        """
        coerced_pubs = []
        for pub in pubs:
            _validate_pubs(self.backend(), [coerced_pub := EstimatorPub.coerce(pub)], False)
            coerced_pubs.append(
                EstimatorPub(
                    PassManager([ConvertISAToClifford()]).run(coerced_pub.circuit),
                    coerced_pub.observables,
                    coerced_pub.parameter_values,
                    coerced_pub.precision,
                    False,
                )
            )

        return coerced_pubs

    def __repr__(self) -> str:
        return f'Neat(backend="{self.backend().name}")'
