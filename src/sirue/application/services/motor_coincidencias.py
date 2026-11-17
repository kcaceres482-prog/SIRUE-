"""Motor de coincidencias inteligente con similitud difusa, normalización y análisis semántico."""

from __future__ import annotations

import difflib
import re
import unicodedata

from sirue.domain.entities.reporte_objeto import ReporteObjeto, TipoReporte


def normalizar_texto(texto: str) -> str:
    """Normaliza un texto eliminando tildes, caracteres especiales y convirtiendo a minúsculas."""
    if not texto:
        return ""
    # Descomponer caracteres con acento
    nfkd = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Quitar puntuación y pasar a minúsculas
    limpio = re.sub(r"[^\w\s]", " ", sin_tildes.lower())
    return re.sub(r"\s+", " ", limpio).strip()


def extraer_tokens(texto: str) -> set[str]:
    """Extrae palabras clave significativas de un texto normalizado."""
    norm = normalizar_texto(texto)
    stopwords = {
        "a", "al", "algo", "con", "como", "cual", "de", "del", "el", "ella",
        "en", "era", "es", "esa", "ese", "eso", "esta", "este", "esto",
        "fue", "ha", "hay", "la", "las", "le", "les", "lo", "los", "mas",
        "me", "mi", "muy", "no", "nos", "otra", "otro", "para",
        "pero", "por", "que", "se", "ser", "si", "sin", "sobre", "son",
        "su", "sus", "te", "tu", "tus", "un", "una", "uno", "unas", "unos",
        "ya", "yo", "y", "o", "ni",
    }
    tokens = {p for p in norm.split() if len(p) > 2 and p not in stopwords}
    return tokens


class MotorCoincidencias:
    """Motor que calcula la afinidad y detecta coincidencias entre reportes de forma flexible.

    Utiliza cuatro criterios ponderados para determinar qué tan probable
    es que un reporte de objeto perdido y uno encontrado se refieran
    al mismo objeto. Incluye similitud difusa para tolerar errores tipográficos.

    Ponderaciones:
        - Categoría:             30 %
        - Palabras clave/texto:  30 %
        - Coincidencia de lugar: 20 %
        - Proximidad temporal:   20 %
    """

    PESO_CATEGORIA: float = 0.30
    PESO_PALABRAS: float = 0.30
    PESO_UBICACION: float = 0.20
    PESO_DISTANCIA: float = 0.20  # Alias de compatibilidad hacia PESO_UBICACION
    PESO_TIEMPO: float = 0.20

    TIEMPO_PERFECTO: float = 1.0
    TIEMPO_MAXIMO: float = 24.0

    def _calcular_similitud_difusa_textos(self, t1: str, t2: str) -> float:
        """Calcula la similitud difusa entre dos textos completos normalizados."""
        n1 = normalizar_texto(t1)
        n2 = normalizar_texto(t2)
        if not n1 or not n2:
            return 0.0
        if n1 == n2:
            return 1.0
        # Si un texto contiene al otro
        if n1 in n2 or n2 in n1:
            ratio_cont = min(len(n1), len(n2)) / max(len(n1), len(n2))
            return max(0.85, ratio_cont)
        ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
        return ratio if ratio >= 0.60 else 0.0

    def _calcular_similitud_tokens_difusa(
        self, tokens_p: set[str], tokens_e: set[str]
    ) -> float:
        """Calcula la afinidad entre dos conjuntos de palabras con tolerancia tipográfica."""
        if not tokens_p or not tokens_e:
            return 0.0

        # Jaccard exacto inicial
        interseccion_exacta = len(tokens_p & tokens_e)
        union = len(tokens_p | tokens_e)
        jaccard = interseccion_exacta / union if union > 0 else 0.0

        # Evaluación difusa palabra a palabra (ej: lapto vs laptop, mochilla vs mochila)
        coincidencias_difusas = 0.0
        coincidencias_encontradas = 0
        for p in tokens_p:
            mejor_match = 0.0
            for e in tokens_e:
                if p == e:
                    mejor_match = 1.0
                    break
                # Prefijo común largo (ej. lapto / laptop)
                if (p.startswith(e) or e.startswith(p)) and min(len(p), len(e)) >= 4:
                    mejor_match = max(mejor_match, 0.90)
                else:
                    ratio = difflib.SequenceMatcher(None, p, e).ratio()
                    if ratio >= 0.80:
                        mejor_match = max(mejor_match, ratio)
            if mejor_match > 0.0:
                coincidencias_difusas += mejor_match
                coincidencias_encontradas += 1

        if coincidencias_encontradas == 0:
            return 0.0

        score_promedio = coincidencias_difusas / max(len(tokens_p), len(tokens_e))
        return max(jaccard, score_promedio)

    def _calcular_similitud_ubicacion(self, ref_p: str, ref_e: str) -> float:
        """Calcula la similitud de ubicación en campus considerando subcadenas y typos."""
        n_p = normalizar_texto(ref_p)
        n_e = normalizar_texto(ref_e)
        if not n_p or not n_e:
            return 0.0
        if n_p == n_e:
            return 1.0
        if n_p in n_e or n_e in n_p:
            return 0.90

        tok_p = extraer_tokens(ref_p)
        tok_e = extraer_tokens(ref_e)
        if not tok_p or not tok_e:
            ratio_directo = difflib.SequenceMatcher(None, n_p, n_e).ratio()
            return ratio_directo if ratio_directo >= 0.70 else 0.0

        score_tok = self._calcular_similitud_tokens_difusa(tok_p, tok_e)
        ratio_cadena = difflib.SequenceMatcher(None, n_p, n_e).ratio()
        if ratio_cadena < 0.70:
            ratio_cadena = 0.0
        return max(score_tok, ratio_cadena)

    def calcular_puntuacion(
        self, perdido: ReporteObjeto, encontrado: ReporteObjeto
    ) -> tuple[float, dict]:
        """Calcula la puntuación de coincidencia entre un reporte perdido y uno encontrado.

        Returns:
            Tupla con (puntuación_total, desglose) donde desglose incluye etiquetas y métricas.
        """
        # 1. Similitud textual y palabras clave
        tok_perdido = extraer_tokens(f"{perdido.titulo} {perdido.descripcion}")
        tok_encontrado = extraer_tokens(f"{encontrado.titulo} {encontrado.descripcion}")
        score_palabras = self._calcular_similitud_tokens_difusa(tok_perdido, tok_encontrado)

        sim_titulos = self._calcular_similitud_difusa_textos(perdido.titulo, encontrado.titulo)
        score_texto_final = max(score_palabras, sim_titulos)

        # 2. Categoría (con flexibilidad si el texto es muy similar)
        if perdido.categoria == encontrado.categoria:
            score_categoria = 1.0
        elif perdido.categoria.es_compatible(encontrado.categoria):
            score_categoria = 0.3
        else:
            # Si el texto es idéntico o muy similar, otorgar flexibilidad
            score_categoria = 0.2 if score_texto_final >= 0.70 else 0.0

        # 3. Coincidencia de ubicación interna
        score_ubicacion = self._calcular_similitud_ubicacion(
            perdido.ubicacion.referencia_interna,
            encontrado.ubicacion.referencia_interna,
        )

        # 4. Proximidad temporal
        diferencia_horas = perdido.fecha_hora_incidente.diferencia_horas(
            encontrado.fecha_hora_incidente
        )

        if diferencia_horas <= self.TIEMPO_PERFECTO:
            score_tiempo = 1.0
        elif diferencia_horas >= self.TIEMPO_MAXIMO:
            score_tiempo = 0.0
        else:
            score_tiempo = 1.0 - (
                (diferencia_horas - self.TIEMPO_PERFECTO)
                / (self.TIEMPO_MAXIMO - self.TIEMPO_PERFECTO)
            )

        # Puntuación final ponderada
        puntuacion_total = (
            self.PESO_CATEGORIA * score_categoria
            + self.PESO_PALABRAS * score_texto_final
            + self.PESO_UBICACION * score_ubicacion
            + self.PESO_TIEMPO * score_tiempo
        )

        # Generación de etiquetas explicativas
        etiquetas: list[str] = []
        if score_categoria == 1.0:
            etiquetas.append("Misma categoría")
        if score_texto_final >= 0.50:
            etiquetas.append("Texto similar")
        if score_ubicacion >= 0.50:
            etiquetas.append("Misma zona del campus")
        if score_tiempo >= 0.75:
            etiquetas.append("Horario cercano")

        detalles = {
            "categoria": round(score_categoria, 4),
            "palabras_clave": round(score_texto_final, 4),
            "ubicacion": round(score_ubicacion, 4),
            "distancia": round(score_ubicacion, 4),
            "tiempo": round(score_tiempo, 4),
            "etiquetas": etiquetas,
        }

        return round(puntuacion_total, 4), detalles

    def buscar_coincidencias(
        self,
        nuevo_reporte: ReporteObjeto,
        reportes_opuestos: list[ReporteObjeto],
        umbral: float = 0.4,
    ) -> list[tuple[ReporteObjeto, float, dict]]:
        """Busca coincidencias ordenadas de mayor a menor porcentaje de afinidad."""
        coincidencias: list[tuple[ReporteObjeto, float, dict]] = []

        for opuesto in reportes_opuestos:
            if nuevo_reporte.tipo == TipoReporte.PERDIDO:
                perdido = nuevo_reporte
                encontrado = opuesto
            else:
                perdido = opuesto
                encontrado = nuevo_reporte

            puntuacion, detalles = self.calcular_puntuacion(perdido, encontrado)

            if puntuacion >= umbral:
                coincidencias.append((opuesto, puntuacion, detalles))

        # Ordenar de mayor a menor puntuación
        coincidencias.sort(key=lambda x: x[1], reverse=True)
        return coincidencias
