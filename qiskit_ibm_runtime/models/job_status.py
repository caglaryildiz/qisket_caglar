# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2018.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Class for job status."""
from typing import Any, Dict, TypeVar, Type

JobStatusT = TypeVar("JobStatusT", bound="JobStatus")


class JobStatus:
    """Model for JobStatus.

    Attributes:
        job_id (str): backend job_id.
        status (str): status of the job.
        status_msg (str): status message.
    """

    _data: Dict[str, str] = {}

    def __init__(self, job_id: str, status: str, status_msg: str, **kwargs: Any):
        self._data = {}
        self.job_id = job_id
        self.status = status
        self.status_msg = status_msg
        self._data.update(kwargs)

    @classmethod
    def from_dict(cls: Type[JobStatusT], data: Dict[str, str]) -> JobStatusT:
        """Create a new JobStatus object from a dictionary.

        Args:
            data (dict): A dictionary representing the JobStatus to create.
                         It will be in the same format as output by
                         :meth:`to_dict`.

        Returns:
            JobStatus: The ``JobStatus`` from the input dictionary.
        """
        return cls(**data)

    def to_dict(self) -> Dict[str, str]:
        """Return a dictionary format representation of the JobStatus.

        Returns:
            dict: The dictionary form of the JobStatus.
        """
        out_dict = {
            "job_id": self.job_id,
            "status": self.status,
            "status_msg": self.status_msg,
        }
        out_dict.update(self._data)
        return out_dict

    def __getattr__(self, name: str) -> str:
        try:
            return self._data[name]
        except KeyError as ex:
            raise AttributeError(f"Attribute {name} is not defined") from ex
