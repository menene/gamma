# Figuras del deck

Todo lo que `presentation.html` carga vive aquí. Las rutas en el deck son
relativas a esta carpeta: `src="figuras/…"`.

| Archivo | Lámina | Origen |
|---|---|---|
| `fig02-duplicados-por-tipo.png` | 7 · Descripciones sin separador estándar | Tesis, Figura 2, p. 27 |
| `fig03-mapa-calidad.png` | 8 · Mapa de calidad consolidado | Tesis, Figura 3, p. 27 |
| `medallon.svg` | 19 · Las tres capas del medallón | Propio |
| `pipeline.svg` | 27 · Cómo funciona el modelo | Propio |
| `ngramas.svg` | 28 · Vectorización por caracteres | Propio |
| `umbral.svg` | 31 · Exactitud y cobertura según el umbral | Propio |

El diagrama de arquitectura de la lámina 18 no está aquí: va incrustado como SVG
dentro del HTML, porque es el mismo que la plataforma publica en `/arquitectura`.

## Si reemplazás una figura

- **PNG a 2× o SVG.** El deck renderiza a 1600×900 y una figura ocupa hasta ~660 px de alto.
- Los PNG con fondo blanco llevan `class="diagram png"`, que aplica `mix-blend-mode:multiply`
  para fundir el blanco con el fondo del deck. Un SVG con fondo transparente no lo necesita.
- **Sin título embebido** si se puede: el título lo pone la lámina y el crédito el `.figure-caption`.
  Las figuras de la tesis lo traen y se dejaron así para que coincidan con el documento.
- Una figura muy apaisada (más de 2:1) no se lee a media lámina — va a ancho completo,
  como la Figura 2.
