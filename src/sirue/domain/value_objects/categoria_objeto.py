"""Value Object que representa la categoría de un objeto perdido o encontrado."""

from __future__ import annotations

from enum import Enum


class CategoriaObjeto(Enum):
    """Categorías posibles para clasificar un objeto.

    Cada valor representa un tipo de objeto comúnmente reportado
    en un campus universitario.
    """

    MOCHILA = "MOCHILA"
    LAPTOP = "LAPTOP"
    CELULAR = "CELULAR"
    LLAVES = "LLAVES"
    CARTERA = "CARTERA"
    DOCUMENTO = "DOCUMENTO"
    ROPA = "ROPA"
    LIBRO = "LIBRO"
    OTRO = "OTRO"

    def es_compatible(self, otra: CategoriaObjeto) -> bool:
        """Determina si esta categoría es compatible con otra.

        Dos categorías son compatibles si son iguales o si alguna de ellas
        es OTRO (categoría comodín).

        Args:
            otra: Otra categoría de objeto.

        Returns:
            True si las categorías son compatibles.
        """
        if self == otra:
            return True
        if self == CategoriaObjeto.OTRO or otra == CategoriaObjeto.OTRO:
            return True
        return False
