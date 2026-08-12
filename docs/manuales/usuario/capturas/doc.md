# Capturas pendientes — Manual de usuario

Las 14 capturas que faltan para completar `manual_usuario.tex`.

**Dónde van:** en esta misma carpeta, en PNG y con el nombre exacto de la primera
columna. El documento las detecta solas: mientras falte una, dibuja un
recuadro con el nombre esperado, y en cuanto el archivo aparece la inserta sin que
haya que tocar el `.tex`.

**Modo de captura:** ventana completa del navegador. Las URLs de la tabla son
directas: ábrela, deja la pantalla en el estado que describe la última columna y
dispara la captura. No hace falta recortar.

Si prefieres tomarlas de tu entorno local, sustituye el host por
`http://localhost:8089`; las rutas son las mismas.

---

## Antes de empezar

| Punto | Detalle |
|---|---|
| **Sesión** | Usa una cuenta **de gestor, no de administrador**. Un admin ve secciones extra (Arquitectura, Referencia, Lab, Modelo) que no deben salir en un manual de usuario |
| **Tema** | En **modo claro**. Se imprime mejor y es como se ve por omisión |
| **Ventana** | Alrededor de **1280 × 800**. Más ancha que eso y el texto sale diminuto: en el PDF la imagen se reduce a unos 15 cm de ancho |
| **Alto** | Solo lo visible en pantalla, **sin capturar la página completa con desplazamiento**. Una captura muy alta se encoge para caber y queda ilegible |
| **Barra del navegador** | Déjala visible: mostrar la dirección ayuda al lector. Oculta la barra de marcadores, que solo estorba |
| **Confidencialidad** | Si aparecen nombres de gestores o solicitantes reales, difumínalos. El prefacio del informe compromete el anonimato de la organización |
| **Formato** | PNG |

---

## Las 14 capturas

| # | Archivo | URL | Qué debe verse |
|---|---|---|---|
| 1 | `01-login.png` | https://gamma.cookielab.cc/login | Formulario de acceso con los campos de correo y contraseña |
| 2 | `02-barra-superior.png` | https://gamma.cookielab.cc/chat | Ventana completa del chat recién abierto. Lo que importa está arriba: logo GAMMA, enlace Datos, botón Chat, ícono de ayuda, ícono de tema y el nombre con su flecha |
| 3 | `03-menu-cuenta.png` | https://gamma.cookielab.cc/chat | La misma pantalla con el menú de la cuenta desplegado: nombre, correo y *Cerrar sesión*. **Con cuenta de gestor no debe aparecer *Administrar*** |
| 4 | `04-chat-inicio.png` | https://gamma.cookielab.cc/chat | Pantalla recién abierta, con el panel de conversaciones a la izquierda y el mensaje de bienvenida |
| 5 | `05-chat-procesando.png` | https://gamma.cookielab.cc/chat | El indicador de avance mientras el asistente trabaja. Hay que agarrarlo al vuelo: dura pocos segundos |
| 6 | `06-chat-datos-faltantes.png` | https://gamma.cookielab.cc/chat | La respuesta con la lista de datos pendientes. Provócala pidiendo algo incompleto, por ejemplo *"necesito un tornillo"* |
| 7 | `07-chat-duplicados.png` | https://gamma.cookielab.cc/chat | El listado de posibles duplicados con su porcentaje y el botón *Ninguno, continuar*. Pide algo que ya exista, por ejemplo *"valvula de bola de pvc de 3 pulgadas"* |
| 8 | `08-chat-propuesta.png` | https://gamma.cookielab.cc/chat | La tarjeta de propuesta completa: descripción corta, descripción larga, tipo de material, clase sugerida con su confianza, y los botones Confirmar y Descartar |
| 9 | `09-chat-buscar-clase.png` | https://gamma.cookielab.cc/chat | El buscador de clases abierto y con resultados en pantalla |
| 10 | `10-chat-confirmado.png` | https://gamma.cookielab.cc/chat | Una solicitud ya confirmada, en su estado final |
| 11 | `11-datos-exportar.png` | https://gamma.cookielab.cc/datos → pestaña **Exportar** | La pestaña con el filtro de estado, la casilla *Excluir ya exportados* y el listado de solicitudes |
| 12 | `12-datos-exportar-seleccion.png` | https://gamma.cookielab.cc/datos → pestaña **Exportar** | Lo mismo pero con varias solicitudes marcadas y el botón *Exportar* mostrando el conteo |
| 13 | `13-datos-importar.png` | https://gamma.cookielab.cc/datos → pestaña **Importar** | Los tres bloques de carga (UNSPSC, Clases, Maestro) con sus conteos y el botón *Seleccionar archivos .xlsx* |
| 14 | `14-ayuda.png` | https://gamma.cookielab.cc/ayuda | La pantalla completa: tarjeta del manual, guía rápida de cinco pasos y el acordeón de preguntas frecuentes |

---

## Cómo provocar cada estado del chat

Las capturas 5 a 10 son fases sucesivas de un mismo alta. Puedes sacarlas todas
en un solo recorrido:

1. Abre `/chat` y pulsa **Nueva conversación** → captura **4**.
2. Escribe algo incompleto, como *"necesito un tornillo"*. Mientras procesa,
   captura **5**; cuando responda pidiendo datos, captura **6**.
3. Completa con algo que ya exista en el catálogo, por ejemplo
   *"tornillo hexagonal de acero galvanizado 1/2 por 2 pulgadas"*. Si aparecen
   duplicados, captura **7**.
4. Pulsa **Ninguno, continuar**. Cuando llegue la propuesta, captura **8**.
5. Abre el buscador de clases → captura **9**.
6. Pulsa **Confirmar** → captura **10**.

Con la solicitud ya confirmada, ve a `/datos` → **Exportar** para las capturas
**11** y **12**.

---

## Al terminar

```bash
cd docs/manuales/usuario
latexmk -pdf manual_usuario.tex
```

Los recuadros de "captura pendiente" desaparecen conforme se agregan los
archivos. Para publicar el manual en la aplicación:

```bash
mkdir -p ../../../frontend/public/docs
cp manual_usuario.pdf ../../../frontend/public/docs/manual-gamma.pdf
```

Y en `frontend/src/pages/Ayuda.vue`, cambia la constante del inicio:

```ts
const MANUAL_URL: string | null = '/docs/manual-gamma.pdf'
```

Con eso la tarjeta de la sección Ayuda deja de decir "En preparación" y muestra
el botón de descarga.
