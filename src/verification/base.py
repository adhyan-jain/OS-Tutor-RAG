"""Abstract Base Verifier for MGEV executable semantics."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from src.mechanism.schema import MechanismContract, VerificationTrace, VerificationStatus


class BaseVerifier(ABC):
    """Abstract base class for all deterministic educational OS verifiers."""

    @property
    @abstractmethod
    def mechanism_name(self) -> str:
        """Returns the target OS mechanism name."""
        pass

    @abstractmethod
    def execute(self, verification_input: Dict[str, Any]) -> VerificationTrace:
        """Executes the deterministic simulation and returns the execution trace."""
        pass

    @abstractmethod
    def verify(self, contract: MechanismContract) -> Tuple[VerificationStatus, str, Dict[str, Any]]:
        """Verifies a claim prediction against actual observation.

        Returns (VerificationStatus, reason_str, observed_values_dict).
        """
        pass
