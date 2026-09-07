# GAMMA — guion de la defensa

> Este archivo y `presentation.html` estan sincronizados. Se puede editar cualquiera
> de los dos; despues hay que correr el script de la direccion correspondiente:
>
> - editaste el **deck** -> `python3 build_guion.py`
> - editaste el **guion** -> `python3 apply_guion.py`

Solo lo que se dice en voz alta. Los numeros corresponden a las laminas del deck.
El reparto (quien dice cada lamina) todavia no esta asignado.

---

# LA NECESIDAD

### 01

Buenas tardes. Somos el grupo 1, conformado por Alejandra Alvarado, Erick Marroquín y Rudy Osorio.
Les presentamos nuestro trabajo de graduación GAMMA: Gobierno Automatizado del Maestro de Materiales, desarrollado como proyecto de graduación de la Maestría en Business Intelligence and Analytics de la Universidad del Valle de Guatemala.

### 02

Anunciar el recorrido completo en una frase: primero por qué hacía falta, después qué construimos, y al final qué pasó cuando se usó. Este primer bloque responde lo primero.

### 03

El presente proyecto se desarrolla en una unidad de negocio del sector energético, con operación en varios países de Centroamérica y el Caribe. Dicha unidad administra, sobre el módulo de materiales de SAP, un catálogo de 45,397 registros activos, distribuidos en trece tipos de material.
Dentro de este proceso, un equipo de gestores de datos maestros es responsable de validar cada material antes de su creación: debe confirmarse que no exista previamente en el catálogo, que se le asigne la categoría correspondiente, y que cumpla con las especificaciones mínimas establecidas por la normativa ISO 8000.
Actualmente, esta validación se realiza de forma enteramente manual. Cabe señalar que, si bien el presente trabajo se desarrolla sobre SAP, la problemática que se expondrá a continuación es inherente a la gestión de datos maestros en general, independientemente del sistema ERP utilizado.

### 04

Al analizar este proceso se identificó que, dentro de la organización, no existe ningún mecanismo automatizado que apoye al gestor en el momento de la decisión: ni para verificar duplicados, ni para sugerir la categoría correspondiente.
Un análisis exploratorio sobre la totalidad del catálogo permitió cuantificar la problemática en tres dimensiones. En duplicidad: el 4.8 % de los registros presenta duplicidad exacta, más un 8.3 % adicional que, al no seguir la convención de separadores, representa un riesgo de duplicidad no detectable mediante búsqueda exacta.
En segundo lugar, materiales asignados a categorías que no corresponden a su naturaleza real, lo que afecta la trazabilidad del catálogo y la planificación de compras.
Y en tercer lugar, un tiempo de gestión elevado: 3.3 horas promedio por solicitud, sobre unas cuatro solicitudes diarias por gestor.
Su caracterización detallada se expone más adelante, en el análisis exploratorio.

### 05

Esta problemática no se limita al tiempo invertido por el gestor: un material mal registrado incide directamente en procesos posteriores, como la ejecución de órdenes de compra, la planificación del mantenimiento y la trazabilidad de los activos.
Es además un problema acumulativo: mientras el proceso continúe sin apoyo analítico, el catálogo seguirá incorporando inconsistencias, cuyo costo de corrección retroactiva es superior al de su prevención.
Con base en lo anterior, la solución debía combinar dos componentes: un modelo que asista al gestor en el momento mismo de la decisión, y un mecanismo que permita verificar, con evidencia cuantitativa, si esa asistencia reduce el tiempo de gestión y mejora la calidad del catálogo. Ese es el propósito de GAMMA. Antes de explicar qué construimos, toca mostrar de dónde salen estas cifras.

### 06

La fuente primaria es el maestro de materiales del módulo MM de SAP, extraído mediante exportación manual en trece archivos organizados por tipo de material, dado que no existe integración directa con el ERP.
A esta fuente se sumaron dos catálogos de referencia: el maestro de clases corporativo, con 1,538 entradas, y la tabla del clasificador UNSPSC de Naciones Unidas, que permite anclar la taxonomía interna a un referente externo estandarizado.
El corte corresponde al mandante 402, con fecha del 29 de mayo de 2026: 45,400 registros exportados, de los cuales 45,397 son los registros activos sobre los que se trabaja de aquí en adelante.
OJO — esta es la única lámina donde aparece el 45,400. En todo el resto de la presentación la cifra es 45,397. Si el tribunal pregunta por la diferencia: son tres registros inactivos descartados en la exportación.

### 07

El primer hallazgo es de composición: sobre los 45,397 registros activos, dos tipos de material —ZRPI y ZSUM— concentran por sí solos cerca de dos terceras partes del catálogo completo.
El resto se distribuye de forma considerablemente más dispersa entre los once tipos restantes.
Esta concentración es relevante porque, como se verá enseguida, los problemas de calidad no se distribuyen de manera uniforme entre tipos, sino que se concentran de forma distinta según el volumen y la naturaleza de cada uno. Eso es lo que permite priorizar la intervención en lugar de atacar el catálogo entero.

### 08

Este es el hallazgo con mayor peso en el diseño de la herramienta: 3,759 descripciones —el 8.3 % del catálogo— no siguen la convención de separadores, dos puntos o punto y coma, establecida por la organización. Un tipo de material concentra el 31.8 % de sus descripciones sin la estructura esperada.
Por qué importa: una descripción sin separador es indistinguible de otra similar mediante una búsqueda exacta en SAP. Esos 3,759 registros representan un riesgo de duplicidad que ninguna búsqueda exacta puede detectar.
Ese fue el motivo directo por el que la detección de duplicados se resolvió por similitud difusa y no por coincidencia de cadenas. Decisión de diseño número uno.
A esto se suma el problema relacionado y ya visible: 2,182 registros con duplicidad exacta en el texto breve, el 4.8 % del catálogo. Y ahí hay una distinción importante: un tipo de equipos tiene la mayor tasa relativa, 35.2 % de sus registros duplicados, mientras que ZRPI concentra el mayor volumen absoluto, 973 casos, con una tasa relativa mucho menor. Tasa y volumen priorizan de forma distinta dónde concentrar la limpieza.

### 09

Además de la duplicidad se evaluó el porcentaje de materiales marcados como bloqueados: 6,748 registros, un 14.9 % del catálogo.
El patrón se repite. Un tipo concentra el mayor porcentaje relativo, con un 46.0 % de sus registros bloqueados; pero es nuevamente ZRPI el que concentra el mayor volumen absoluto, 1,597 materiales, cerca de una cuarta parte de todos los bloqueados del catálogo.
Las cuatro dimensiones —duplicidad, bloqueo, ausencia de separador y ausencia de clase— se consolidaron en este mapa único por tipo de material, que permite ver de forma integrada dónde se concentra el riesgo combinado.
Este mapa es la evidencia que sustenta priorizar la intervención sobre los tipos de mayor riesgo, particularmente ZRPI y ZRPA.
SI PREGUNTAN POR DIEN: el 90.0 % de registros sin clase es el valor más alto del mapa, pero es un caso aislado de bajo volumen —531 registros— y no altera la priorización.

### 10

El análisis reveló algo que no estaba en el planteamiento original: 5,368 registros no tenían ninguna categoría asignada en la fuente, y más de la mitad de las clases del catálogo tienen diez materiales o menos.
Estos dos datos son los que después determinan dos decisiones del modelado. Los registros sin clase quedan fuera del conjunto de entrenamiento, porque no hay etiqueta que aprender. Y la cola larga de clases minúsculas obliga a reportar F1 macro además de exactitud: una métrica que pondere cada clase por igual es indispensable para no subestimar el error sobre las categorías minoritarias.
Decisión de diseño número dos y número tres.

### 11

Finalmente se analizó la longitud del texto breve. El promedio se ubica en 31.9 caracteres, contra un límite estructural de cuarenta que impone el propio campo de SAP.
Las descripciones se concentran contra ese límite, y ese es el origen de las abreviaturas inconsistentes entre gestores descritas en el marco teórico: ante un espacio reducido, cada gestor adopta sus propias convenciones para abreviar.
Insistir en la frase: no abrevian por descuido, abrevian porque el sistema los obliga. Esto importa porque es lo que después justifica vectorizar por caracteres y no por palabras — decisión de diseño número cuatro, y se retoma más adelante.

### 12

Estos cuatro hallazgos —duplicación, ausencia de separadores, clases faltantes y el límite de caracteres— son las cuatro decisiones que dieron forma a la arquitectura de GAMMA.
Duplicación y separadores llevan a la similitud difusa. Clases faltantes lleva al tratamiento del desbalance y a la métrica F1 macro. El límite de caracteres lleva a la vectorización por caracteres.
Cada módulo que van a ver en la metodología responde directamente a uno de estos problemas. Cuatro problemas concretos. Lo que sigue es qué nos propusimos hacer con ellos.

---

# EL PROYECTO

### 13

Cierre del bloque anterior. El tribunal ya sabe el tamaño del problema; ahora corresponde exponer qué nos propusimos hacer con él y hasta dónde llega el alcance.

### 14

El objetivo general consistió en desarrollar GAMMA, una plataforma de asistencia analítica para el flujo de creación individual de materiales en SAP. Su desarrollo articuló tres capacidades complementarias: procesamiento de lenguaje natural para la normalización de descripciones, búsqueda por similitud difusa para la detección de duplicados, y aprendizaje automático supervisado, entrenado sobre el histórico del catálogo, para la sugerencia de categoría.
La finalidad de estas capacidades es reducir el tiempo de gestión y mejorar la calidad del maestro de materiales de la unidad de negocio evaluada.

### 15

A partir del objetivo general se definieron seis objetivos específicos.
El primero, implementar un pipeline de integración del maestro mediante una arquitectura por capas —bronce, plata y oro— sobre PostgreSQL, para consolidar en un repositorio único, normalizado y trazable los trece archivos de exportación previamente dispersos.
El segundo, caracterizar los defectos de calidad ya acumulados, mediante un análisis retroactivo de duplicidad exacta y completitud de categoría, para establecer una línea base contra la cual medir la mejora.
El tercero, seleccionar el algoritmo de clasificación mediante una evaluación comparativa de siete configuraciones sobre una partición estratificada del histórico.
El cuarto, construir una plataforma web de asistencia conversacional que articulara normalización, detección de duplicados y sugerencia de categoría, conservando siempre la validación humana previa al registro en SAP.
El quinto, evaluar el efecto de la herramienta comparando los tiempos de gestión antes y después, y midiendo el acuerdo entre las sugerencias del modelo y las decisiones del gestor en producción.
Y el sexto, diseñar y ejecutar un plan de adopción cultural con gestores y jefatura, en el entendido de que una herramienta que no es adoptada no genera ningún efecto real. Ese plan fue el que sostuvo el uso activo de GAMMA durante todo el período de validación.

### 16

El alcance se circunscribe al flujo de creación individual de materiales en SAP; es decir, al mecanismo mediante el cual un gestor solicita, valida y registra un material nuevo.
El desarrollo y la validación se realizaron dentro de una única unidad de negocio, con operación en múltiples países de Centroamérica y el Caribe. Dentro de este flujo, GAMMA interviene en tres momentos: normaliza la descripción propuesta, verifica su similitud contra el catálogo para alertar sobre posibles duplicados, y sugiere la categoría más probable con base en el histórico ya clasificado.
Subrayar: GAMMA es una herramienta de asistencia y validación, no de automatización plena. No escribe directamente en SAP ni sustituye el criterio del gestor, quien conserva en todo momento el control de la decisión final.

### 17

De igual manera que es necesario precisar qué comprende el proyecto, es necesario delimitar lo que queda fuera.
La plataforma no mantiene integración en línea con el ERP, ni de lectura ni de escritura: el gestor exporta periódicamente el maestro desde SAP hacia la plataforma, y registra posteriormente en SAP las solicitudes ya validadas. Esta separación es deliberada y constituye el mecanismo de supervisión humana sobre el que se diseñó la solución.
Tampoco comprende el flujo de creación masiva, que opera mediante un mecanismo distinto y no fue intervenido. Y si bien el análisis cuantifica los duplicados y materiales mal categorizados existentes, su corrección automática queda fuera del alcance, por corresponder a un esfuerzo de limpieza de datos independiente.
Finalmente, el modelo fue entrenado y validado sobre el catálogo de esta única unidad de negocio; su extensión al resto de la corporación se plantea como la etapa siguiente, una vez confirmado su desempeño en el presente entorno. Con el encargo ya delimitado, sigue qué se construyó.

### 18

Este es el mismo diagrama que la plataforma expone a sus propios usuarios en la sección de arquitectura, no una versión hecha para la presentación.
Se lee en tres planos, de arriba hacia abajo. Acceso: el frontend en Vue entra por Nginx, que actúa como proxy inverso y resuelve la autenticación con JWT. Nada llega a los servicios internos sin pasar por ahí.
Servicios: el API en FastAPI orquesta el flujo y se ramifica en los tres módulos analíticos —duplicados, categorización y normalización—. Los tres convergen en el nodo de confirmación humana.
Datos: PostgreSQL 16 con las tres capas del medallón, sobre una sola instancia.
Señalar el nodo de confirmación humana: sin él nada avanza. Es la materialización, en la arquitectura, de la decisión de alcance que ya se explicó.

### 19

El repositorio se implementó siguiendo una arquitectura por capas sobre PostgreSQL 16.
Bronce concentra la trazabilidad completa: ingesta, predicciones, decisiones sobre duplicados y errores. Plata contiene los datos ya normalizados: el maestro, los catálogos de referencia y las solicitudes. Oro expone las vistas agregadas que alimentan el tablero.
La idea de fondo: el dato no se transforma donde se consulta, y el paso entre capas es lo que hace auditable el sistema.
Se optó por un motor relacional y no por una plataforma distribuida porque el volumen —decenas de miles de registros— no justifica esa complejidad operativa.

### 20

Para el modelado se definió una función de normalización de texto —aplicada de forma idéntica en entrenamiento y en inferencia— que convierte a mayúsculas, elimina diacríticos y estandariza los separadores de la convención de nomenclatura. Que sea la misma función importa: consultar el modelo con texto preparado de otra forma lo degrada en silencio, sin producir ningún error visible.
Dos criterios de exclusión: los materiales sin categoría asignada en la fuente —los 5,368 ya mencionados— y las clases con menos de tres ejemplos, insuficientes para entrenar y evaluar simultáneamente.
El conjunto resultante: 39,571 materiales en 1,234 clases, particionado de forma estratificada en 80 % de entrenamiento —31,656 registros— y 20 % de prueba —7,915—, preservando la proporción de cada clase en ambos subconjuntos.
OJO CON LAS DOS CIFRAS DE CLASES: 1,538 es el maestro de clases corporativo; 1,234 son las que tienen al menos tres ejemplos y por tanto las únicas que el modelo puede predecir.

### 21

El módulo de normalización se resolvió con un modelo de lenguaje de gran escala en lugar de un motor de reglas y diccionarios de abreviatura: un diccionario exigiría mantenimiento manual permanente conforme aparecen materiales de familias nuevas, mientras que un modelo fundacional alcanza desempeño competitivo sin entrenamiento específico.
Se configuró con temperatura baja, para privilegiar la consistencia sobre la variedad, y se instruyó explícitamente para no inventar especificaciones ausentes.
El diseño busca que el modelo falle por omisión y no por invención, que es el único modo de falla aceptable en un proceso de gobierno de datos.

### 22

La detección de duplicados se implementó como una consulta de similitud difusa ejecutada directamente sobre el maestro normalizado, con la extensión pg_trgm de PostgreSQL. Descompone cada descripción en trigramas y compara el grado de superposición entre el material propuesto y los ya existentes.
Esta es la respuesta directa al hallazgo del 8.3 % sin separador: por eso no se resolvió con búsqueda exacta.
El umbral de alerta se estableció en un valor deliberadamente permisivo: en una herramienta de asistencia, el costo de un falso positivo es sustancialmente menor que el de un falso negativo, que se materializa en un duplicado creado y en el costo recurrente de arrastrarlo.

### 23

La plataforma se construyó sobre PostgreSQL 16 con pg_trgm habilitada, un API en Python con FastAPI, y un frontend de página única, todo orquestado con Docker Compose.
Con la única excepción del servicio de modelo de lenguaje, que opera bajo pago por uso, la totalidad de la infraestructura es software de código abierto, lo que hace sostenible su operación más allá del período de desarrollo.
Este dato conecta con el impacto financiero que se presenta al final: el costo del proyecto es tan bajo precisamente por esto.

### 24

La selección del algoritmo se resolvió mediante una competencia entre siete configuraciones, todas sobre la misma partición y con las mismas métricas.
Primera ronda: cuatro configuraciones que combinan dos representaciones vectoriales —TF-IDF de palabras y TF-IDF de n-gramas de carácter— con regresión logística, máquina de vectores de soporte lineal y bosque aleatorio. Segunda ronda: tres familias adicionales —potenciación de gradiente sobre árboles, un clasificador de subpalabras y un transformador multilingüe con ajuste fino.
Se reportan cuatro métricas de desempeño más el tiempo de entrenamiento. Por qué cuatro y no solo exactitud: por el desbalance de clases. Como más de la mitad de las clases tiene diez materiales o menos, una métrica que pondere cada clase por igual —el F1 macro— es indispensable para no subestimar el error sobre las categorías minoritarias.

### 25

Dejar la tabla en pantalla y hablar sobre ella; no leerla.
Señalar la primera fila, y después la última columna. La configuración ganadora obtuvo el mejor resultado en exactitud, F1 macro y F1 ponderado. En Top-3 queda segunda: la regresión logística de carácter alcanza 0.9248 contra 0.9176, pero a veinte veces el tiempo de entrenamiento y con 6.5 puntos menos de F1 macro. Si preguntan por esa métrica, decirlo así, no esquivarlo.
Las dos filas que importan para el argumento: XGBoost tardó 3 horas y 42 minutos para terminar sexto, 2.6 puntos por debajo — 246 veces el tiempo del ganador. El transformador tardó más de cincuenta minutos sobre GPU y no superó a la configuración lineal en ninguna métrica.
NO usar fastText como argumento de velocidad: sus 42.8 segundos son comparables a los 54.1 del ganador, no dramáticamente menores. Su diferencia está en el desempeño, no en el tiempo.
Todas las configuraciones reciben el mismo nivel de detalle; ninguna necesita explicación individual extensa.

### 26

La configuración ganadora fue una máquina de vectores de soporte lineal sobre TF-IDF de n-gramas de carácter, calibrada.
Exactitud de 82.08 sobre 1,234 clases: el azar sería 0.08 %, así que la cifra hay que leerla contra ese fondo y no contra un problema binario. Top-3 de 91.76: en nueve de cada diez casos la clase correcta está entre las tres que se muestran al gestor.
El F1 macro promedia sin ponderar por volumen y por tanto castiga el desempeño sobre las clases pequeñas; el ponderado pesa por volumen. El ganador lidera ambas, lo que indica comportamiento uniforme a lo largo de la taxonomía y no solo un buen agregado.
Y el costo: 54.1 segundos en procesador convencional. El argumento que cierra: el sistema está pensado para reentrenarse conforme el catálogo crece; un modelo que exige horas para actualizarse es un modelo que en la práctica no se actualiza.

### 27

Dos etapas de modelado, con un preproceso delante y una salida ordenada detrás: la descripción entra, se normaliza, se convierte en vector, la máquina de vectores de soporte la clasifica, y salen las tres clases más probables con su confianza.
El detalle que importa: el vectorizador ajustado viaja dentro del artefacto, no se reconstruye. Si se reconstruyera, el vocabulario cambiaría y las dimensiones dejarían de significar lo mismo.
Y la función de normalización es literalmente la misma que se usó en entrenamiento, importada del mismo módulo. Consultar el modelo con texto preparado de otra forma lo degrada en silencio, sin producir ningún error visible.
Las dos láminas siguientes abren cada etapa: primero cómo se vectoriza, después cómo se calibra.

### 28

Esta es la decisión clave del modelo, y responde directamente al cuarto hallazgo del análisis exploratorio.
El catálogo se escribió durante años, por distintos gestores, contra un límite de cuarenta caracteres. La abreviatura inconsistente no es una anomalía: es la norma. Un vectorizador de palabras ve tres tokens sin relación; uno de caracteres ve tres textos casi idénticos.
Además captura medidas y designaciones alfanuméricas —un medio de pulgada, M12, 2X4— que un tokenizador de palabras trata como ruido, y tolera errores de digitación sin diccionario de correcciones.
Y el beneficio más sutil: no requiere vocabulario cerrado. Un material de una familia nueva, con una palabra que nunca apareció en entrenamiento, igual produce fragmentos conocidos. Con palabras sería un vector vacío.
Señalar la figura: cada palabra se rellena con espacios en los extremos y se recorren ventanas de 2 a 5 caracteres que no cruzan de una palabra a la siguiente. Aquí se ve solo el paso de tres sobre TORNILLO: TOR, ORN, RNI, NIL. Una descripción de cuarenta caracteres genera del orden de cien fragmentos, y de todo el corpus se conservan los 50,000 más frecuentes: esas son las dimensiones del vector.

### 29

Sobre la partición de prueba el modelo cometió 1,418 errores de 7,915 materiales, un 17.92 %. La matriz de confusión muestra que ese error no se distribuye de forma pareja: las clases con vocabulario propio y estable se resuelven casi sin error, mientras que las categorías genéricas —repuesto, herramienta— presentan las tasas de acierto más bajas.
Y esto tiene una implicación relevante: buena parte de ese error no es, en sentido estricto, un error de clasificación, sino la manifestación de un problema del propio catálogo, donde existen pares de clases que designan el mismo concepto y difieren únicamente en puntuación o forma de escritura.
El análisis de errores del modelo funciona, en ese sentido, como un instrumento adicional de diagnóstico sobre la calidad de la taxonomía que clasifica. Esto reaparece en las conclusiones como hallazgo no anticipado.
SI PREGUNTAN por qué no se removieron los materiales genéricos tipo ZSUM antes de entrenar: fue una decisión metodológica consciente evaluar sobre el catálogo real y no sobre una versión depurada, precisamente porque el análisis de errores revela un problema de taxonomía que una depuración previa habría ocultado.

### 30

Una SVM no da probabilidades: da distancias con signo al hiperplano. Un valor de 2.4 significa que cae bien adentro del lado positivo, pero no significa 84 por ciento.
La calibración entrena sobre una parte de los datos, observa qué distancias produce sobre la parte que no vio, y ajusta una función que traduce distancia en probabilidad fiel.
Esta etapa es la que habilita todo lo que sigue: sin probabilidades no hay umbral, y sin umbral el sistema estaría obligado a responder siempre.

### 31

Dado que el modelo produce una probabilidad asociada a cada sugerencia, se caracterizó el compromiso entre exactitud y cobertura para distintos umbrales, sobre los 7,915 materiales de la partición de prueba.
Las dos curvas están en la misma escala porcentual, a propósito, porque así se ve la forma real del intercambio: la exactitud apenas se mueve —de 82 a 99, diecisiete puntos en todo el recorrido— mientras la cobertura se desploma de 100 a 28. Se gana poca exactitud y se paga mucha cobertura, y cada punto adicional cuesta cada vez más volumen automatizado. Eso es lo que hace que elegir el umbral sea una decisión de negocio y no de estadística.
Subir el umbral no mejora el modelo: lo hace más selectivo. El modelo es el mismo, con la misma exactitud del 82 %. Lo único que cambia es cuántos casos se aceptan sin revisar.
Al 0.5 el sistema resolvería tres de cada cuatro solicitudes acertando en el 92.9 %. Al 0.8 resuelve poco más de una de cada cuatro, pero acierta en el 98.9 %: de 2,235 materiales resueltos solos se equivocaría en unos 25.
Se adoptó 0.8. La razón está en la lámina siguiente.

### 32

Una categoría incorrecta que entra al catálogo sin revisión cuesta para siempre: distorsiona los reportes de consumo, complica la planificación de compras y se propaga a todo proceso que consulte el catálogo después. Y nadie la detecta, porque nadie la está buscando. Corregirla retroactivamente cuesta más que haberla revisado.
Una sugerencia derivada a revisión solo consume la atención del gestor, que es exactamente el escenario que la herramienta está diseñada para atender. No es un fallo del sistema: es el sistema funcionando.
Como los dos errores no cuestan lo mismo, no tiene sentido tratarlos de forma simétrica. Por eso privilegiamos exactitud sobre cobertura, en un proceso cuyo propósito declarado es la calidad del dato.
Y la precisión que evita que el 28 % se lea como una limitación: el 72 % restante no queda solo. El gestor no vuelve al punto de partida ni enfrenta un catálogo de 1,234 clases; recibe tres candidatas ordenadas por probabilidad, y la correcta está entre ellas en el 91.8 % de los casos. Lo que cambia entre un régimen y otro no es si el modelo ayuda, sino quién firma la decisión.
Hasta aquí, lo que se construyó y cómo se comporta en laboratorio. Falta la prueba que importa: qué pasó cuando los gestores lo usaron de verdad.

---

# LOS RESULTADOS

### 33

Lo anterior fue evaluación en laboratorio. Este bloque presenta la operación real sobre solicitudes de producción, durante cinco semanas.

### 34

El primer resultado es el efecto medido sobre el tiempo de gestión. Durante el período previo a la implementación, el tiempo efectivo promedio por solicitud fue de 3.34 horas, con mediana de 2.82, sobre 353 solicitudes observadas entre el 15 de febrero y el 17 de junio.
Durante la operación de la plataforma ese tiempo bajó a 1.39 horas en promedio y 1.28 de mediana. Una reducción del 58.4 % sobre el promedio y del 54.7 % sobre la mediana.
La diferencia se confirmó estadísticamente significativa mediante una prueba U de Mann-Whitney, con p menor a 0.0001, y los intervalos de confianza al 95 % de ambos períodos no se traslapan: la mejora no es atribuible al azar ni a un menor volumen de trabajo durante la validación.
OJO CON LOS DOS DENOMINADORES: 98 son las solicitudes con tiempo efectivo medido; 153 son todas las solicitudes asistidas por la plataforma. Decirlo explícitamente antes de que lo pregunten.
SI PREGUNTAN por las cuatro solicitudes diarias: es el promedio diario real de la línea base completa, cuatro meses de operación medida, no una simulación.

### 35

Además de la comparación estadística se construyó un tablero operativo en Power BI, con actualización semanal, que resume el desempeño de la herramienta y de los gestores mediante seis indicadores clave.
Se eligió Power BI por dos razones concretas: conecta de forma directa a las tablas de la capa Gold sin capa intermedia, y la empresa ya cuenta con licencia Premium, así que no hay costo adicional ni necesidad de capacitar a jefatura en una herramienta nueva.
Destaca la tasa de acuerdo entre el modelo y el gestor: 88.2 %. En la gran mayoría de los casos el gestor conservó la categoría que la plataforma sugirió. La completitud de clase —la proporción de solicitudes que terminaron con categoría asignada— se ubicó en 74.5 %.
CUIDADO AL COMPARAR CON EL 82.08 % DE LABORATORIO: no son la misma métrica. El acuerdo se mide contra decisiones reales de quien conoce el catálogo; la exactitud, contra una partición retenida de los mismos datos. La conclusión defendible es que el desempeño se sostuvo frente a materiales reales — NO que el modelo «superó» a su resultado de laboratorio.
El tablero permite a la jefatura dar seguimiento continuo más allá del período de validación de este proyecto. El archivo .pbix queda editable como entregable.

### 36

La instrumentación cronometra cada paso por separado. La normalización con el modelo de lenguaje concentra el 70.5 % del tiempo de máquina, la búsqueda de duplicados el 28.7 %, y la clasificación apenas el 1.5 %.
Pero el dato que responde a la pregunta obvia es este: los 6.2 segundos de cómputo representan el 0.12 % de las 1.39 horas que dura en promedio una gestión asistida.
Decirlo con todas las letras: la mejora no viene de que la máquina calcule rápido. Viene de que el gestor recibe la descripción normalizada, los candidatos a duplicado y la categoría sugerida ya resueltos, en lugar de construir esa información con consultas manuales sucesivas en SAP.
Este es el argumento que desarma de frente la objeción «¿por qué sigue tardando 1.39 horas si la máquina responde en segundos?». Anticiparla aquí, no esperar a que la hagan.
Nota interna: el desglose por componente en segundos es aproximadamente 4.4 / 1.8 / 0.09. Verificar contra el tablero antes de la defensa; en el deck solo se presentan los porcentajes y el total.

### 37

Al cierre del período de prueba se aplicó una encuesta a la población que interactuó directamente con la plataforma: gestores y equipo de jefatura y coordinación, con una tasa de respuesta del 71.4 %.
Entre los gestores, la facilidad de uso obtuvo la calificación más alta, 5.00 sobre 5, seguida de la satisfacción general con 4.33. La reducción de tiempo percibida se ubicó en 4.00, en la misma dirección que la reducción medida en el tablero.
La jefatura calificó la alineación de la herramienta con los objetivos de calidad del área en 4.5 sobre 5.
Adelantarse a la objeción metodológica: dado el tamaño reducido de esta población, estos resultados se interpretan como el registro directo de la opinión de la mayoría de las personas involucradas, y no como una muestra estadística sobre un universo mayor.

### 38

En términos financieros, el retorno se calculó sobre el costo real de despliegue: Q1,641.65, que corresponde únicamente al hospedaje del servidor y a las horas de capacitación durante construcción, pruebas y puesta en producción.
Sobre ese costo, y proyectando el ahorro anual a partir de la reducción de tiempo medida —Q400,491 de mediana, Q507,310 de promedio—, se obtiene un retorno de 243 veces sobre la mediana y 308 sobre el promedio, con recuperación de entre 1.2 y 1.5 días.
LIDERAR CON 243×, la mediana, por ser más robusta frente a valores atípicos.
Y contextualizar la magnitud NOSOTROS, antes de que lo haga el tribunal: se trata en buena medida de un artefacto del denominador. El costo refleja el gasto marginal de un proyecto de graduación y no el de un desarrollo contratado por la vía comercial; de haberse tercerizado, la cifra sería considerablemente menor.
Lo que sí resulta estadísticamente sólido, bajo cualquiera de los dos escenarios, es que la reducción de tiempo que sustenta este ahorro es significativa y no atribuible al azar.

### 39

De estos resultados se derivan cinco conclusiones principales.
En primer lugar, se consolidó el maestro de materiales en un repositorio único, normalizado y trazable, que unificó los 45,397 registros previamente dispersos en trece archivos de exportación, y que hoy sustituye la consulta dispersa sobre hojas de cálculo que caracterizaba la operación previa.
En segundo lugar, el análisis no solo confirmó defectos de calidad de magnitud relevante, sino que aportó un hallazgo no anticipado en el planteamiento original: una fracción del error del clasificador no corresponde a fallas del modelo, sino a pares de clases que designan el mismo concepto dentro de la taxonomía. La herramienta construida para clasificar materiales resultó, adicionalmente, un instrumento de diagnóstico sobre la calidad de la propia taxonomía.
Y en tercer lugar, la configuración más simple de las siete evaluadas resultó también la más exacta, por un margen consistente, y con un costo de entrenamiento considerablemente menor al de las alternativas de mayor complejidad.

### 40

En cuarto lugar, GAMMA logró integrar los tres módulos analíticos —normalización, detección de duplicados y sugerencia de categoría— dentro del flujo real de creación de materiales, resolviendo por sí sola la mayoría de los casos dentro del umbral de confianza configurado, sin que ninguna sugerencia llegue a SAP sin la confirmación del gestor.
Y en quinto lugar, la herramienta redujo a menos de la mitad el tiempo efectivo de gestión, con un retorno de inversión inmediato bajo cualquiera de los escenarios considerados.
En síntesis: el objetivo general del proyecto se cumplió. GAMMA se desarrolló, se desplegó y operó sobre solicitudes reales, articulando efectivamente el procesamiento de lenguaje natural, la búsqueda por similitud difusa y el aprendizaje automático supervisado sobre el histórico del catálogo.

### 41

Las recomendaciones se agrupan en dos frentes. El primero, orientado a la operación inmediata, reúne seis.
NARRAR AGRUPADO, no leer una por una — el slide las muestra todas por si el tribunal quiere el detalle.
Tres apuntan a depurar la base sobre la que opera la herramienta: depurar la taxonomía de clases, que hoy contiene pares redundantes; hacer exigible la convención de separadores en el momento mismo de la captura; y resolver la categorización de los materiales que hoy carecen de clase asignada.
Una cuarta es de secuencia: consolidar la operación dentro de esta unidad de negocio antes de escalar a otras, dado que las conclusiones actuales descansan todavía sobre cinco semanas de operación en un solo entorno.
Y las dos últimas son de aprovechamiento: contrastar periódicamente el umbral configurado con el comportamiento real de la operación, y explotar la instrumentación de calidad que el sistema ya captura, hoy disponible pero aún no incorporada al seguimiento habitual del área.

### 42

El segundo frente, orientado a la continuidad técnica, reúne cinco recomendaciones.
Tres buscan fortalecer el rigor metodológico de la evaluación: adoptar una partición agrupada por descripción, que corrija el sesgo optimista que hoy introduce la duplicidad del catálogo entre entrenamiento y prueba; sustituir la partición única por validación cruzada, para acompañar cada métrica de su dispersión; y realizar una evaluación por ablación del término principal, para cuantificar cuánto del desempeño depende de la coincidencia léxica directa con el nombre de la clase.
Las dos últimas amplían el alcance analítico: cuantificar la duplicidad difusa —no solo la exacta— sobre el catálogo completo, y evaluar la incorporación del clasificador al flujo de creación masiva, que hoy queda fuera del alcance.
Estas tres primeras son honestas sobre los límites del trabajo y conviene presentarlas como tales: fortalecen la defensa en lugar de debilitarla.

### 43

Con esto concluye la presentación de este trabajo de graduación. Agradecemos nuevamente al tribunal examinador su atención, y quedamos atentos a sus preguntas y observaciones.
