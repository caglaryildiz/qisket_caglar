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

"""Tests for the classes used to instantiate noise learner results."""

from ddt import ddt

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import PauliList

from qiskit_ibm_runtime.utils.noise_learner_result import PauliLindbladError, LayerError

from ..ibm_test_case import IBMTestCase


@ddt
class TestPauliLindbladError(IBMTestCase):
    """Class for testing the PauliLindbladError class."""

    def setUp(self):
        super().setUp()

        # A set of paulis
        paulis1 = PauliList(["X", "Z"])
        paulis2 = PauliList(["XX", "ZZ", "IY"])
        self.paulis = [paulis1, paulis2]

        # A set of rates
        rates1 = [0.1, 0.2]
        rates2 = [0.3, 0.4, 0.5]
        self.rates = [rates1, rates2]

    def test_valid_inputs(self):
        """Test PauliLindbladError with valid inputs."""
        for paulis, rates in zip(self.paulis, self.rates):
            error = PauliLindbladError(paulis, rates)
            self.assertEqual(error.paulis, paulis)
            self.assertEqual(error.rates, rates)
            self.assertEqual(error.num_qubits, paulis.num_qubits)

    def test_invalid_inputs(self):
        """Test PauliLindbladError with invalid inputs."""
        with self.assertRaises(ValueError):
            PauliLindbladError(self.paulis[0], self.rates[1])


class TestLayerError(IBMTestCase):
    """Class for testing the LayerError class."""

    def setUp(self):
        super().setUp()

        # A set of circuits
        c1 = QuantumCircuit(2)
        c1.cx(0, 1)

        c2 = QuantumCircuit(3)
        c2.cx(0, 1)
        c2.cx(1, 2)

        self.circuits = [c1, c2]

        # A set of qubits
        qubits1 = [8, 9]
        qubits2 = [7, 11, 27]
        self.qubits = [qubits1, qubits2]

        # A set of errors
        error1 = PauliLindbladError(PauliList(["XX", "ZZ"]), [0.1, 0.2])
        error2 = PauliLindbladError(PauliList(["XXX", "ZZZ", "YIY"]), [0.3, 0.4, 0.5])
        self.errors = [error1, error2]

    def test_valid_inputs(self):
        """Test LayerError with valid inputs."""
        for circuit, qubits, error in zip(self.circuits, self.qubits, self.errors):
            layer_error = LayerError(circuit, qubits, error)
            self.assertEqual(layer_error.circuit, circuit)
            self.assertEqual(layer_error.qubits, qubits)
            self.assertEqual(layer_error.error, error)

            self.assertEqual(layer_error.num_qubits, circuit.num_qubits)
            self.assertEqual(layer_error.num_qubits, len(qubits))

    def test_invalid_inputs(self):
        """Test LayerError with invalid inputs."""
        with self.assertRaises(ValueError):
            LayerError(self.circuits[1], self.qubits[0], self.errors[0])

        with self.assertRaises(ValueError):
            LayerError(self.circuits[0], self.qubits[1], self.errors[0])

        with self.assertRaises(ValueError):
            LayerError(self.circuits[0], self.qubits[0], self.errors[1])
