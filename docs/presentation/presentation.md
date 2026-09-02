<!--
GAMMA — deck de apoyo
Texto mínimo por diseño: la lámina sostiene una idea, la voz sostiene el contenido.
Fuente completa: doc.md (mismo directorio).
Separador de lámina: ---   ·   Notas del orador: bloque "Note:" (reveal.js)
-->

# GAMMA

### Gobierno Automatizado del Maestro de Materiales

Note:
- Presentarse y decir en una frase qué es GAMMA: asistente inteligente en el flujo de creación de materiales SAP.
- Anunciar el recorrido: qué construimos, cómo elegimos el modelo, y cómo funciona el que ganó.

---

## El punto de partida

# 45,397
materiales

# 3.3 h
por solicitud

# 1,234
categorías posibles

Note:
- Catálogo de una unidad de negocio del sector energético, Centroamérica y el Caribe.
- Cada solicitud permanecía 3.3 horas dentro del rol del gestor.
- No existía ningún mecanismo automatizado que dijera si el material ya existía ni qué categoría le tocaba.
- La búsqueda manual en SAP —el paso que GAMMA automatiza— consumía entre 5 y 10 minutos por solicitud.

---

## GAMMA hace tres cosas

### Normaliza · Compara · Clasifica

Note:
- Normaliza la descripción con un modelo de lenguaje, según la convención ISO 8000 de la corporación.
- Compara contra el catálogo por similitud difusa para alertar duplicados.
- Clasifica la categoría con un modelo supervisado entrenado sobre el histórico.
- Insistir: asiste, no sustituye. No escribe en SAP. La decisión final es del gestor.

---

## Arquitectura

<!-- Diagrama: el publicado en la plataforma, sección /arquitectura -->

Note:
- Aclarar que es el mismo diagrama que la plataforma expone a sus usuarios, no uno hecho para la presentación.
- Leerlo en tres planos, de arriba hacia abajo:
  - Acceso: frontend Vue → Nginx → JWT. Nada entra sin pasar por ahí.
  - Servicios: el API orquesta y se ramifica en duplicados, categorización y normalización. Los tres convergen en confirmación humana.
  - Datos: PostgreSQL 16 con el medallón.
- Señalar el nodo de confirmación humana: sin él nada avanza.

---

## Medallón

### Bronze · Silver · Gold

Note:
- La idea de fondo: el dato no se transforma donde se consulta. Cada capa tiene una responsabilidad y el paso entre capas es lo que hace auditable el sistema.
- Todo sobre una sola instancia de PostgreSQL.

---

## Bronze

### Lo crudo y la memoria

Note:
- Recibe los archivos de SAP tal cual, con marca de tiempo. Aquí no se corrige nada.
- Y registra todo lo que el sistema hace: ingestas, predicciones, decisiones sobre duplicados, interacciones con el LLM, errores.
- Frase clave: la trazabilidad no fue un añadido posterior, es una propiedad estructural.
- Cualquier registro se audita hasta el archivo del que vino; cualquier sugerencia se reconstruye con la entrada que la produjo y la decisión que recibió.

---

## Silver

### Donde el API trabaja

Note:
- Mapeo explícito entre los encabezados de SAP y el modelo de datos: columnas repetidas, valores compuestos código-descripción.
- Resolución de llaves foráneas: cada material con su clase y unidad; cada clase con su tipo y su UNSPSC. Trece archivos dispersos quedan en un modelo relacional único.
- Carga idempotente por UPSERT: reprocesar actualiza, no duplica.
- Índice invertido de trigramas sobre el texto breve: sin él, cada búsqueda de duplicados recorrería la tabla completa.

---

## Gold

### No almacena. Calcula.

Note:
- Son vistas en tiempo real sobre silver. El tablero no puede desincronizarse de la operación porque no hay proceso de refresco que falle.
- Agregan por semana: tiempos por módulo, calidad de las predicciones, duplicados, ahorro, actividad por gestor.
- Dos detalles: el ahorro está parametrizado en una tabla, se recalcula sin reescribir SQL.
- Y todas las vistas excluyen las cuentas administrativas: el tráfico de desarrollo y demos contaminaría la medición.

---

## El API

### Publicar la capacidad,
### no repartir el archivo

Note:
- El problema: un modelo entrenado es un archivo. Así solo lo usa quien tenga Python, las mismas versiones, el artefacto y la misma función de preprocesamiento. Es decir, solo nosotros. Eso no es una herramienta de la organización, es un activo de sus autores.
- Detrás de un endpoint HTTP, cualquier cliente lo consume enviando una descripción. El gestor lo usa sin saber que existe.
- Esa fue la forma de democratizarlo.
- Además garantiza: mismo preprocesamiento que en entrenamiento, una sola versión vigente para todos, acceso con token, y registro automático de cada predicción.
- La inferencia va dentro del API, no en un servicio aparte: 0.09 segundos. No había nada que ganar separándola.

---

## El experimento

# 7
configuraciones

Note:
- Cuatro familias: modelos lineales sobre representaciones dispersas, métodos de ensamble, un clasificador de subpalabras y un transformador multilingüe con ajuste fino.
- Todas sobre la misma partición y las mismas métricas.
- El conjunto: 39,571 materiales, 1,234 clases, tras descartar los que no tenían categoría en la fuente y las clases con menos de tres ejemplos.
- Cuatro métricas de desempeño más el tiempo de entrenamiento — y el tiempo entró como criterio de selección, no como dato de color.

---

## Resultados

| | Exactitud | F1 macro | Top-3 | Tiempo |
|---|---:|---:|---:|---:|
| **LinearSVC + carácter** | **0.8208** | **0.7072** | 0.9176 | **54 s** |
| XGBoost | 0.8145 | 0.6821 | 0.9200 | 3 h |
| Random Forest | 0.8133 | 0.7029 | 0.9063 | 46 s |
| Reg. logística palabra | 0.8095 | 0.6689 | 0.9135 | 29 s |
| Reg. logística carácter | 0.8080 | 0.6423 | 0.9248 | 18 min |
| Transformer | 0.7995 | 0.5654 | 0.8953 | 54 min |
| fastText | 0.7780 | 0.6275 | 0.8865 | 43 s |

Note:
- Dejar la tabla en pantalla y hablar sobre ella; no leerla.
- Señalar la primera fila y luego la última columna.

---

## Ganó el más simple

# 54 s
### frente a 3 horas

Note:
- La SVM lineal sobre caracteres superó a los ensambles y al aprendizaje profundo.
- XGBoost: más de tres horas para quedar seis décimas abajo.
- El transformador: sesenta veces el tiempo, sobre GPU, mientras el ganador entrena en CPU. Y no lo superó.
- El argumento que cierra: el sistema está pensado para reentrenarse conforme el catálogo crece. Un modelo que exige horas para actualizarse es un modelo que en la práctica no se actualiza.
- Y es coherente con el problema: textos cortos, muy estructurados, vocabulario técnico acotado. No hay ambigüedad sintáctica que justifique más capacidad.

---

## El modelo ganador

### Texto libre → una de 1,234 clases

Note:
- Aclarar qué no hace: no entiende el material, no sabe qué es un tornillo.
- Lo que aprendió de 31,656 ejemplos es qué patrones de caracteres aparecen en las descripciones de cada clase.
- Un texto nuevo se resuelve buscando a qué patrón conocido se parece más.
- Está implementado como un pipeline de dos etapas serializado en un solo artefacto: el vectorizador ajustado viaja dentro, no se reconstruye.

---

## Vectorización

### Caracteres, no palabras

Note:
- El texto se parte en secuencias de 2 a 5 caracteres, sin cruzar de una palabra a la siguiente.
- Cada descripción produce del orden de cien fragmentos.
- Se pesa cada fragmento por lo raro que es en el catálogo: lo que aparece en todas las descripciones baja, lo que aparece en pocas clases sube. Ahí es donde el modelo se fija en lo distintivo.
- Vocabulario acotado a 50,000 fragmentos, y cada vector se escala a longitud unitaria para que una descripción larga y una corta se comparen por composición y no por tamaño.
- El resultado: un vector disperso de 50,000 dimensiones por descripción.

---

## Por qué caracteres

### TORNILLO · TORNILO · TORN

Note:
- Esta es la decisión clave y responde a cómo está escrito el catálogo.
- Para un vectorizador de palabras son tres tokens distintos y sin relación. Para uno de caracteres son tres textos muy parecidos.
- El catálogo se escribió durante años, por distintos gestores, contra un límite de cuarenta caracteres. La tolerancia a la abreviatura no es un lujo, es un requisito.
- Además captura medidas y designaciones alfanuméricas —1/2", M12, 2X4— que un tokenizador de palabras trata como ruido.
- Y no requiere vocabulario cerrado: un material de una familia nueva igual produce fragmentos conocidos.

---

## El clasificador

# 1,234
fronteras

Note:
- Una SVM lineal busca el hiperplano que separa una clase de las demás dejando el mayor margen posible.
- Mayor margen significa que no toma cualquier frontera que separe, sino la que queda más lejos de los ejemplos de ambos lados. Eso es lo que le da capacidad de generalizar.
- Con 1,234 clases se entrena un separador por clase, uno contra el resto. Gana el que deja la descripción más adentro de su lado.
- Por qué basta lineal: en 50,000 dimensiones las clases tienden a ser linealmente separables. Añadir capacidad no compra separabilidad que ya se tiene, y sí compra sobreajuste y costo.

---

## Calibración

### Distancia → probabilidad

Note:
- Una SVM no da probabilidades, da distancias con signo al hiperplano. Un 2.4 no significa 84 %.
- La calibración entrena sobre una parte, observa qué distancias produce sobre la parte que no vio, y ajusta una función que traduce distancia en probabilidad fiel: de los casos a los que asigna 0.9, cerca del 90 % es correcto.
- Sin esta etapa no existiría el umbral. Es lo que convierte un clasificador en un sistema capaz de decir: de esto estoy seguro, de esto no.

---

## Punto de operación

| Umbral | Exactitud | Cobertura |
|---|---:|---:|
| Sin umbral | 0.8208 | 100 % |
| 0.5 | 0.9294 | 73.9 % |
| 0.6 | 0.9517 | 65.1 % |
| 0.7 | 0.9678 | 54.1 % |
| **0.8** | **0.9888** | **28.2 %** |

Note:
- El mecanismo: cada predicción llega con una confianza. Las que superan el umbral el sistema las resuelve solo; las que no, las deriva a revisión.
- El compromiso: subir el umbral no mejora el modelo, lo hace más selectivo. Menos casos pasan, pero los que pasan son más confiables.
- La pregunta de diseño no es cuál umbral es el correcto, sino qué combinación conviene a este proceso.
- Elegimos 0.8: resuelve poco más de una de cada cuatro solicitudes, acertando en el 98.9 %.

---

## Los dos errores
## no cuestan lo mismo

Note:
- Una categoría incorrecta que entra al catálogo sin revisión cuesta para siempre: distorsiona reportes de consumo, complica la planificación de compras, se propaga a todo proceso que consulte el catálogo después. Nadie la detecta porque nadie la está buscando.
- Una sugerencia derivada a revisión solo consume la atención del gestor — que es exactamente el escenario que la herramienta está diseñada para atender. No es un fallo del sistema, es el sistema funcionando.
- Por eso no tiene sentido tratarlos de forma simétrica. Privilegiamos exactitud sobre cobertura.

---

## El 72 % restante
## no queda solo

### 3 candidatos, no 1,234

Note:
- Esta es la precisión que evita que el 28 % se lea como una limitación.
- Las solicitudes derivadas a revisión conservan todo el valor de la herramienta: el gestor no vuelve al punto de partida.
- Recibe tres candidatos ordenados por probabilidad, y la exactitud sobre esas tres es del 91.76 %.
- Lo que cambia entre un régimen y otro no es si el modelo ayuda, sino quién firma la decisión.
- Si preguntan por la validez del umbral: las predicciones correctas se concentran en confianza alta y las incorrectas se dispersan hacia valores bajos. Esa forma es lo que hace legítimo el punto de operación.

---

## En operación

# 0.09 s
inferencia · 1.5 % del tiempo

# 88.2 %
acuerdo modelo–gestor

Note:
- El desglose de tiempo de máquina: la normalización con LLM se lleva 4.37 s, los duplicados 1.78 s, la clasificación 0.09 s.
- El núcleo analítico del trabajo consume el 1.5 % del cómputo. Una arquitectura más pesada habría desplazado ese costo sin dar mejor desempeño.
- Sobre 153 solicitudes asistidas, el gestor conservó la categoría sugerida en el 88.2 % de los casos.
- Ese número es una validación independiente del laboratorio: mide contra decisiones reales de quien conoce el catálogo, no contra una partición de los mismos datos. Y que supere al 82.08 % indica que el desempeño se sostuvo con materiales reales.

---

## Limitaciones

### Léxico · Etiquetas · Corte · Cola larga

Note:
- Correspondencia léxica: la convención hace que el término principal coincida a menudo con el nombre de la clase. Parte del acierto viene de ahí. Cuantificarlo exige una evaluación por ablación, que queda pendiente.
- Etiquetas: entrenamos sobre decisiones de los propios gestores. Es la mejor referencia disponible, no una verdad de campo independiente. El techo lo pone la consistencia de esas decisiones.
- Corte: los resultados son sobre una fotografía del catálogo a una fecha. No se puede inferir el desempeño sobre familias no representadas.
- Cola larga: las clases con menos de tres ejemplos quedan fuera del espacio de predicción.

---

# Gracias

Note:
- Cerrar con la idea que sostiene toda la sección: la configuración más simple resultó también la más exacta, y el costo de mantenerla es lo que la hace sostenible en la operación.
- Quedar disponible para preguntas.
