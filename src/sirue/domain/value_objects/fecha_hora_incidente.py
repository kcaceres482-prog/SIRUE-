"""Value Object que representa la fecha y hora de un incidente."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sirue.domain.exceptions.domain_exceptions import ValidacionError


@dataclass(frozen=True)
class FechaHoraIncidente:
    """Fecha y hora en que ocurrió el incidente (pérdida o hallazgo).

    Attributes:
        valor: Fecha y hora del incidente, timezone-aware en UTC.
    """

    valor: datetime

    def __post_init__(self) -> None:
        """Valida que la fecha sea timezone-aware y no esté en el futuro."""
        if self.valor.tzinfo is None:
            raise ValidacionError(
                "La fecha del incidente debe ser timezone-aware (UTC)."
            )

        ahora = datetime.now(timezone.utc)
        margen = timedelta(minutes=5)
        if self.valor > ahora + margen:
            raise ValidacionError(
                "La fecha del incidente no puede estar en el futuro "
                f"(máximo margen: 5 minutos). Valor: {self.valor.isoformat()}"
            )

    def diferencia_horas(self, otra: FechaHoraIncidente) -> float:
        """Calcula la diferencia absoluta en horas con otra fecha de incidente.

        Args:
            otra: Otra fecha de incidente.

        Returns:
            Diferencia absoluta en horas.
        """
        delta = abs((self.valor - otra.valor).total_seconds())
        return delta / 3600.0
