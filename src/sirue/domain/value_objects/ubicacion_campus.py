"""Value Object que representa una ubicación dentro del campus universitario."""

from __future__ import annotations

from dataclasses import dataclass

from sirue.domain.exceptions.domain_exceptions import ValidacionError


@dataclass(frozen=True)
class UbicacionCampus:
    """Ubicación o referencia dentro del campus universitario.

    Attributes:
        referencia_interna: Descripción legible del lugar (ej: 'Aula A-203', 'Biblioteca Central').
    """

    referencia_interna: str

    def __post_init__(self) -> None:
        """Valida que la referencia del lugar no esté vacía."""
        if not self.referencia_interna or not self.referencia_interna.strip():
            raise ValidacionError("La referencia o lugar del campus no puede estar vacía.")

    @property
    def referencia(self) -> str:
        """Alias legible de la referencia del lugar."""
        return self.referencia_interna

    def __str__(self) -> str:
        return self.referencia_interna

    def coincide_con(self, otra: UbicacionCampus) -> float:
        """Calcula la afinidad textual entre dos referencias de ubicación del campus.

        Utiliza el coeficiente de Jaccard sobre las palabras clave del lugar.

        Args:
            otra: Otra instancia de UbicacionCampus a comparar.

        Returns:
            Puntuación de afinidad entre 0.0 y 1.0.
        """
        palabras_self = set(self.referencia_interna.lower().split())
        palabras_otra = set(otra.referencia_interna.lower().split())

        if not palabras_self or not palabras_otra:
            return 0.0

        interseccion = len(palabras_self & palabras_otra)
        union = len(palabras_self | palabras_otra)

        return float(interseccion / union) if union > 0 else 0.0
