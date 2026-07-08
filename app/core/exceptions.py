"""Application-specific exceptions.

Kept separate from generic Python errors so the CLI and service layers can
translate them into friendly Rich messages without leaking implementation detail.
"""

from __future__ import annotations


class OpsCollectorError(Exception):
    """Base class for all application errors."""


class ConfigurationError(OpsCollectorError):
    """Raised when configuration is missing or invalid."""


class RepositoryError(OpsCollectorError):
    """Raised when a data-access operation fails."""


class ValidationError(OpsCollectorError):
    """Raised when input data fails validation (import, forms, etc.)."""

    def __init__(self, message: str, *, field: str | None = None, row: int | None = None):
        super().__init__(message)
        self.field = field
        self.row = row

    def __str__(self) -> str:
        loc = ""
        if self.row is not None:
            loc += f" [row {self.row}]"
        if self.field:
            loc += f" (field: {self.field})"
        return f"{super().__str__()}{loc}"


class DuplicateError(OpsCollectorError):
    """Raised when a duplicate entity is detected during import/create."""


class NotFoundError(OpsCollectorError):
    """Raised when a requested entity does not exist."""


class EvidenceError(OpsCollectorError):
    """Raised when evidence file handling fails."""


class ExportError(OpsCollectorError):
    """Raised when an export operation fails."""


class ImportError_(OpsCollectorError):
    """Raised when an import operation fails."""
