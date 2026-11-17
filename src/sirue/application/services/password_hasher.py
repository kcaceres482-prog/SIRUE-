"""Servicio criptográfico para hash y verificación segura de contraseñas."""

from __future__ import annotations

import hashlib
import hmac
import secrets


class PasswordHasher:
    """Utilidad de hashing basada en PBKDF2-HMAC-SHA256 con salt criptográfica."""

    ITERACIONES: int = 100_000

    @classmethod
    def hashear_password(cls, password: str) -> str:
        """Genera un hash seguro para la contraseña con salt aleatorio.

        Format: pbkdf2_sha256$<iteraciones>$<salt_hex>$<hash_hex>
        """
        salt = secrets.token_hex(16)
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            cls.ITERACIONES,
        )
        hash_hex = hash_bytes.hex()
        return f"pbkdf2_sha256${cls.ITERACIONES}${salt}${hash_hex}"

    @classmethod
    def verificar_password(cls, password: str, password_hash: str) -> bool:
        """Verifica una contraseña en texto claro contra su hash almacenado."""
        try:
            partes = password_hash.split("$")
            if len(partes) != 4 or partes[0] != "pbkdf2_sha256":
                return False

            iteraciones = int(partes[1])
            salt = partes[2]
            hash_esperado = partes[3]

            calculado = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                iteraciones,
            ).hex()

            return hmac.compare_digest(calculado, hash_esperado)
        except Exception:
            return False
