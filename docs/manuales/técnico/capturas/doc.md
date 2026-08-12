# Capturas pendientes — Manual técnico

Las 10 capturas que faltan para completar `manual_tecnico.tex`.

**Dónde van:** en esta misma carpeta, en PNG y con el nombre exacto de la primera
columna. El documento las detecta solas: mientras falte una, dibuja un recuadro
con el nombre esperado, y en cuanto el archivo aparece la inserta sin que haya
que tocar el `.tex`.

**Modo de captura:** ventana completa del navegador. Las URLs son directas:
ábrela, deja la pantalla en el estado que describe la última columna y dispara
la captura. No hace falta recortar.

---

## Antes de empezar

| Punto | Detalle |
|---|---|
| **Sesión** | Con una cuenta **administradora**. Al revés que en el manual de usuario: aquí las secciones restringidas *deben* verse |
| **Tema** | En **modo claro**. Se imprime mejor y es como se ve por omisión |
| **Ventana** | Alrededor de **1280 × 800**. Más ancha y el texto sale diminuto: en el PDF la imagen se reduce a unos 15 cm |
| **Alto** | Solo lo visible en pantalla, **sin capturar la página completa con desplazamiento**. Una captura muy alta se encoge para caber y queda ilegible |
| **Barra del navegador** | Déjala visible: mostrar la dirección ayuda al lector. Oculta la barra de marcadores |
| **Confidencialidad** | Difumina los correos y nombres reales del listado de usuarios. El prefacio del informe compromete el anonimato de la organización |
| **Formato** | PNG |

---

## Las 10 capturas

| # | Archivo | URL | Qué debe verse |
|---|---|---|---|
| 1 | `01-menu-administrar.png` | https://gamma.cookielab.cc/modelo | El menú de la cuenta desplegado, con **Administrar** y *Cerrar sesión*. Con cuenta administradora sí debe aparecer Administrar |
| 2 | `02-usuarios-listado.png` | https://gamma.cookielab.cc/usuarios | El listado de cuentas vigentes con sus columnas de rol, estado y fecha de alta |
| 3 | `03-usuarios-nueva.png` | https://gamma.cookielab.cc/usuarios | El formulario abierto con **Nueva cuenta**: nombre, correo, contraseña y los dos interruptores |
| 4 | `04-usuarios-bajas.png` | https://gamma.cookielab.cc/usuarios | Con **Mostrar cuentas dadas de baja** marcado, de modo que se vea el bloque inferior con el botón *Restaurar* |
| 5 | `05-modelo-pantalla.png` | https://gamma.cookielab.cc/modelo | La pantalla completa: aviso de proceso excepcional, botón de iniciar y el historial de versiones |
| 6 | `06-modelo-comparacion.png` | https://gamma.cookielab.cc/modelo | La tabla de comparación de métricas tras un reentrenamiento terminado |
| 7 | `07-modelo-versiones.png` | https://gamma.cookielab.cc/modelo | El historial de versiones con sus métricas, tamaño y el botón *Revertir* |
| 8 | `08-arquitectura.png` | https://gamma.cookielab.cc/arquitectura | El diagrama de componentes visible en pantalla |
| 9 | `09-referencia.png` | https://gamma.cookielab.cc/referencia | Con las cinco pestañas visibles. Sitúate en **Esquema**, que se ve mejor que la de API |
| 10 | `10-lab.png` | https://gamma.cookielab.cc/lab | La tarjeta de análisis exploratorio con las vistas consolidadas y los tipos de material |

---

## Las tres de Modelo

Las capturas 5 a 7 dependen de que exista al menos un reentrenamiento
terminado. En una instalación recién desplegada solo aparece la versión
`inicial` y no hay comparación que mostrar.

Si en producción todavía no se ha reentrenado, tienes dos caminos:

- **Tomarlas de un entorno donde ya se corrió**, cambiando el host por el que
  corresponda. Lo que documentan es la interfaz, no los datos.
- **Ejecutar un reentrenamiento** para generarlas. Ten presente que tarda unos
  diez minutos, consume bastante memoria y deja el modelo nuevo en servicio —
  habría que revisar las métricas y revertir si empeoraron.

La captura **6** solo se puede tomar mientras un trabajo terminado sigue
seleccionado en pantalla; si recargas, se muestra el último del historial.

---

## Al terminar

```bash
cd docs/manuales/técnico
latexmk -pdf manual_tecnico.tex
```

Los recuadros de "captura pendiente" desaparecen conforme se agregan los
archivos.
