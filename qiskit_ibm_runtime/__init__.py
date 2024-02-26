# This code is part of Qiskit.
#
# (C) Copyright IBM 2022.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
==========================================
Qiskit Runtime (:mod:`qiskit_ibm_runtime`)
==========================================

.. currentmodule:: qiskit_ibm_runtime

Modules related to Qiskit Runtime IBM Client.

Qiskit Runtime is a new architecture that
streamlines computations requiring many iterations. These experiments will
execute significantly faster within its improved hybrid quantum/classical process.

Primitives and sessions
=======================

Qiskit Runtime has two predefined primitives: ``Sampler`` and ``Estimator``.
These primitives provide a simplified interface for performing foundational quantum
computing tasks while also accounting for the latest developments in
quantum hardware and software.

Qiskit Runtime also has the concept of a session. Jobs submitted within a session are
prioritized by the scheduler. A session
allows you to make iterative calls to the quantum computer more efficiently.

Below is an example of using primitives within a session::

    from qiskit_ibm_runtime import QiskitRuntimeService, Session, Sampler, Estimator, Options
    from qiskit.circuit.library import RealAmplitudes
    from qiskit.circuit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit.quantum_info import SparsePauliOp

    # Initialize account.
    service = QiskitRuntimeService()

    # Set options, which can be overwritten at job level.
    options = Options(optimization_level=3)

    # Prepare inputs.
    psi = RealAmplitudes(num_qubits=2, reps=2)
    H1 = SparsePauliOp.from_list([("II", 1), ("IZ", 2), ("XI", 3)])
    theta = [0, 1, 1, 2, 3, 5]
    # Bell Circuit
    qr = QuantumRegister(2, name="qr")
    cr = ClassicalRegister(2, name="qc")
    qc = QuantumCircuit(qr, cr, name="bell")
    qc.h(qr[0])
    qc.cx(qr[0], qr[1])
    qc.measure(qr, cr)

    with Session(service=service, backend="ibmq_qasm_simulator") as session:
        # Submit a request to the Sampler primitive within the session.
        sampler = Sampler(session=session, options=options)
        job = sampler.run(circuits=qc)
        print(f"Sampler results: {job.result()}")

        # Submit a request to the Estimator primitive within the session.
        estimator = Estimator(session=session, options=options)
        job = estimator.run(
            circuits=[psi], observables=[H1], parameter_values=[theta]
        )
        print(f"Estimator results: {job.result()}")

Backend data
============

:class:`QiskitRuntimeService` also has methods, such as :meth:`backend`,
:meth:`backends`, and :meth:`least_busy`, that allow you to query for a target
backend to use. These methods return one or more :class:`IBMBackend` instances
that contains methods and attributes describing the backend.

Supplementary Information
=========================

Account initialization
-------------------------

You need to initialize your account before you can start using the Qiskit Runtime service.
This is done by initializing a :class:`QiskitRuntimeService` instance with your
account credentials. If you don't want to pass in the credentials each time, you
can use the :meth:`QiskitRuntimeService.save_account` method to save the credentials
on disk.

Qiskit Runtime is available on both IBM Cloud and IBM Quantum, and you can specify
``channel="ibm_cloud"`` for IBM Cloud and ``channel="ibm_quantum"`` for IBM Quantum. The default
is IBM Cloud.

Runtime Jobs
------------

When you use the ``run()`` method of the :class:`Sampler` or :class:`Estimator`
to invoke the primitive, a
:class:`RuntimeJob` instance is returned. This class has all the basic job
methods, such as :meth:`RuntimeJob.status`, :meth:`RuntimeJob.result`, and
:meth:`RuntimeJob.cancel`.

Logging
-------

``qiskit-ibm-runtime`` uses the ``qiskit_ibm_runtime`` logger.

Two environment variables can be used to control the logging:

    * ``QISKIT_IBM_RUNTIME_LOG_LEVEL``: Specifies the log level to use.
        If an invalid level is set, the log level defaults to ``WARNING``.
        The valid log levels are ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, and ``CRITICAL``
        (case-insensitive). If the environment variable is not set, then the parent logger's level
        is used, which also defaults to ``WARNING``.
    * ``QISKIT_IBM_RUNTIME_LOG_FILE``: Specifies the name of the log file to use. If specified,
        messages will be logged to the file only. Otherwise messages will be logged to the standard
        error (usually the screen).

For more advanced use, you can modify the logger itself. For example, to manually set the level
to ``WARNING``::

    import logging
    logging.getLogger('qiskit_ibm_runtime').setLevel(logging.WARNING)

Interim and final results
-------------------------

Some runtime primitives provide interim results that inform you about the 
progress of your job. You can choose to stream the interim results and final result when you run the
primitive by passing in the ``callback`` parameter, or at a later time using
the :meth:`RuntimeJob.stream_results` method. For example::

    from qiskit_ibm_runtime import QiskitRuntimeService, Sampler
    from qiskit.circuit import QuantumCircuit, QuantumRegister, ClassicalRegister

    service = QiskitRuntimeService()
    backend = service.backend("ibmq_qasm_simulator")

    # Bell Circuit
    qr = QuantumRegister(2, name="qr")
    cr = ClassicalRegister(2, name="qc")
    qc = QuantumCircuit(qr, cr, name="bell")
    qc.h(qr[0])
    qc.cx(qr[0], qr[1])
    qc.measure(qr, cr)

    def result_callback(job_id, result):
        print(result)

    # Stream results as soon as the job starts running.
    job = Sampler(backend).run(qc, callback=result_callback)
    print(job.result())


Classes
=======
.. autosummary::
   :toctree: ../stubs/

   QiskitRuntimeService
   Estimator
   Sampler
   Session
   IBMBackend
   RuntimeJob
   RuntimeOptions
   RuntimeEncoder
   RuntimeDecoder
"""

import logging

from .qiskit_runtime_service import QiskitRuntimeService
from .ibm_backend import IBMBackend
from .runtime_job import RuntimeJob
from .runtime_options import RuntimeOptions
from .utils.json import RuntimeEncoder, RuntimeDecoder
from .session import Session  # pylint: disable=cyclic-import
from .batch import Batch  # pylint: disable=cyclic-import

from .exceptions import *
from .utils.utils import setup_logger
from .version import __version__

from .estimator import Estimator
from .sampler import Sampler
from .options import Options

# Setup the logger for the IBM Quantum Provider package.
logger = logging.getLogger(__name__)
setup_logger(logger)

# Constants used by the IBM Quantum logger.
QISKIT_IBM_RUNTIME_LOGGER_NAME = "qiskit_ibm_runtime"
"""The name of the IBM Quantum logger."""
QISKIT_IBM_RUNTIME_LOG_LEVEL = "QISKIT_IBM_RUNTIME_LOG_LEVEL"
"""The environment variable name that is used to set the level for the IBM Quantum logger."""
QISKIT_IBM_RUNTIME_LOG_FILE = "QISKIT_IBM_RUNTIME_LOG_FILE"
"""The environment variable name that is used to set the file for the IBM Quantum logger."""
