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

"""Tests for DebuggerResult class."""

import ddt

from qiskit.primitives.containers import PubResult, DataBin

from qiskit_ibm_runtime.debugger import DebuggerResult

from ...ibm_test_case import IBMTestCase
from ...utils import combine


@ddt.ddt
class TestDebuggerResult(IBMTestCase):
    """Class for testing the DebuggerResult class."""

    def setUp(self) -> None:
        super().setUp()

        result1 = DebuggerResult([1, 2, 3])
        result2 = DebuggerResult([[1, 2], [3, 4]])
        self.results = [result1, result2]

        databin1 = DataBin(evs=[4, 5, 6])
        databin2 = DataBin(evs=[[5, 6], [7, 8]])
        self.databins = [databin1, databin2]

        self.pub_results = [PubResult(databin1), PubResult(databin2)]

    @combine(
        scalar=[2, 4.5],
        idx=[0, 1],
        op_name=["add", "mul", "sub", "truediv", "radd", "rmul", "rsub", "rtruediv"],
    )
    def test_operations_with_scalarlike(self, scalar, idx, op_name):
        r"""Test operations between ``DebuggerResult`` and ``ScalarLike`` objects."""
        result = self.results[idx]

        new_result = getattr(result, f"__{op_name}__")(scalar)
        new_vals = getattr(result.vals, f"__{op_name}__")(scalar)

        self.assertListEqual(new_result.vals.tolist(), new_vals.tolist())

    @combine(
        idx=[0, 1],
        op_name=["add", "mul", "sub", "truediv", "radd", "rmul", "rsub", "rtruediv"],
    )
    def test_operations_with_debugger_result(self, idx, op_name):
        r"""Test operations between two ``DebuggerResult`` objects."""
        result1 = self.results[idx]
        result2 = 2 * result1

        new_result = getattr(result1, f"__{op_name}__")(result2)
        new_vals = getattr(result1.vals, f"__{op_name}__")(result2.vals)

        self.assertListEqual(new_result.vals.tolist(), new_vals.tolist())

    @combine(
        idx=[0, 1],
        op_name=["add", "mul", "sub", "truediv", "radd", "rmul", "rsub", "rtruediv"],
    )
    def test_operations_with_databins(self, idx, op_name):
        r"""Test operations between ``DebuggerResult`` and ``DataBin`` objects."""
        result = self.results[idx]
        databin = self.databins[idx]

        new_result = getattr(result, f"__{op_name}__")(databin)
        new_vals = getattr(result.vals, f"__{op_name}__")(databin.evs)

        self.assertListEqual(new_result.vals.tolist(), new_vals.tolist())

    @combine(op_name=["add", "mul", "sub", "truediv", "radd", "rmul", "rsub", "rtruediv"])
    def test_error_for_operations_with_databins(self, op_name):
        r"""Test the errors for operations between ``DebuggerResult`` and ``DataBin``."""
        result = self.results[0]
        databin = DataBin(wrong_kwarg=result.vals)

        with self.assertRaisesRegex(ValueError, f"Cannot apply operator '__{op_name}__'"):
            getattr(result, f"__{op_name}__")(databin)

    @combine(
        idx=[0, 1],
        op_name=["add", "mul", "sub", "truediv", "radd", "rmul", "rsub", "rtruediv"],
    )
    def test_operations_with_pub_results(self, idx, op_name):
        r"""Test operations between ``DebuggerResult`` and ``PubResult`` objects."""
        result = self.results[idx]
        pub_result = self.pub_results[idx]

        new_result = getattr(result, f"__{op_name}__")(pub_result)
        new_vals = getattr(result.vals, f"__{op_name}__")(pub_result.data.evs)

        self.assertListEqual(new_result.vals.tolist(), new_vals.tolist())

    @ddt.data(2, 4.5)
    def test_pow(self, p):
        r"""Test the ``pow`` operator."""
        result = self.results[0]
        new_result = result**p
        new_vals = result.vals**p

        self.assertListEqual(new_result.vals.tolist(), new_vals.tolist())
