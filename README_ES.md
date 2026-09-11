# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Tu copiloto para Elite Dangerous](cmdrhelper/assets/readme/cmdrhelper_readme_es.png)

**Compañero personal para Elite Dangerous – exploración, navegación y datos del comandante de un vistazo**

CMDRHelper es una aplicación de escritorio independiente que analiza los diarios locales de Elite Dangerous y usa datos de posición planetaria de `Status.json`. Te ayuda a identificar cuerpos interesantes, volver a lugares guardados y consultar tus viajes y descubrimientos. Los datos personales se conservan tras reiniciar y se separan por comandante.

## Novedades de la versión 3.3

- Nuevo análisis de sistemas basado en tu experiencia personal de exploración.
- Modo de juego Abierto / Solo / Grupo privado directamente en el resumen.
- Copia los nombres de los sistemas recientes con un clic.
- Datos históricos y análisis más claros y comprensibles.
- Importación de archivos de diario más fiable cuando se amplían posteriormente.

El anterior consejo de salto pasa a llamarse Análisis e incluye Análisis del sistema y los datos históricos existentes. El análisis compara un destino con tu historial personal: el código de masa proporciona la estimación inicial, que la región y la familia refinan con cautela. Un índice de potencial de 100 corresponde a tu media histórica personal del potencial de exploración atenuado, no a una probabilidad porcentual. La base de datos y la solidez de la evidencia se muestran separadas de la valoración; el número final no influye en la puntuación y BIO es actualmente solo informativo.

## Novedades de v3.2 respecto a v3.1

- Gestión de materiales de ingeniería: los 146 materiales Raw, Manufactured y Encoded, con grados, capacidades y casos especiales. Existencias actualizadas por comandante, búsqueda, filtros, cinco fondos discretos y anchura/orden de columnas guardados. Una cantidad desconocida sigue siendo distinta de cero.

- Inventario Odyssey: la cuarta pestaña contiene 223 identidades de catálogo de bienes, componentes, datos y consumibles. Taquilla, mochila y total fiable permanecen separados; se muestran pilas de misión, estado y usos de ingeniería. Las cantidades positivas aparecen en dorado. Los nombres sin traducir utilizan el inglés.

- Búsqueda de comerciantes de materiales (Buscar comerciante → Abrir planificador de rutas): bajo petición, Spansh busca Raw, Manufactured y Encoded por separado desde el sistema actual del comandante. Se excluyen carriers y se verifican los detalles de las estaciones. La distancia en ly es directa entre sistemas; los datos comunitarios no garantizan acceso. Enviar al planificador solo fija el sistema de destino, sin iniciar una ruta. No hay búsqueda de comerciantes Odyssey.

- Vista general del sistema: la nueva presentación al estilo Elite sustituye la miniatura anterior en Explorer y Crónica. Estrellas y planetas forman la estructura principal y las lunas se ramifican debajo; los sistemas múltiples siguen siendo legibles. Zoom, desplazamiento, ajuste a la ventana y clic en los cuerpos permiten consultar detalles.

- Cinturones de asteroides compactos: los grupos se reúnen en cinturones en la vista general y los mapas habituales de Explorer y Crónica. Se conservan todos los datos individuales de los grupos.

- Cartografía corregida: un escaneo posterior al cartografiado DSS ya no reinicia valores de exploración sin vender, hora de cartografiado ni eficiencia. Los registros erróneos se reparan al iniciar desde journals disponibles y atribuidos inequívocamente. Sin esas fuentes, la reparación queda pendiente; no hace falta borrar la base de datos.

- Planificador mejorado: el origen sigue el sistema actual hasta que introduces uno manualmente; vaciar el campo restaura el seguimiento. Naves y carriers utilizan direcciones ID64 verificadas exactamente, sin elegir nombres parecidos. «Unable to find route» indica que no se encontró ruta; comprueba destinos, alcance y ajustes.

- Mejor información de actualización: la ventana Sí/No muestra las versiones instalada y disponible y hasta seis novedades si hay resumen. Las listas largas se desplazan y las acciones siguen accesibles. Esta presentación llega con v3.2; un cliente v3.1 sin modificar todavía no la muestra.

## v3.1 (v3.0.3 → v3.1)

- El progreso BIO es compacto: 1/3 amarillo, 2/3 azul y 3/3 verde; el estado completado «Completado» también es verde. En «mostrar automáticamente», GEO tiene un interruptor propio que se guarda: solo BIO, solo GEO o ambos juntos. Los anchos de columna ajustados manualmente en la tabla compartida BIO / GEO / ABBAU del Explorador se conservan al reabrir y reiniciar. La restauración de columnas de las ventanas emergentes es más robusta; los valores inválidos se sustituyen por anchos predeterminados seguros.

- Descubrimiento y cartografiado se separan y se refieren al momento de tu escaneo: «Ya descubierto al realizar tu escaneo» y «Ya cartografiado al realizar tu escaneo». Los datos ausentes siguen como Desconocido. Los candidatos a First Discovery y First Mapping solo se refieren al escaneo; un No histórico no demuestra que el cuerpo siga sin descubrir o cartografiar hoy. Tu cartografiado no confirma una primicia oficial. La presencia en EDSM permanece separada.

- «HUD de estado EDSM» en «mostrar automáticamente» está DESACTIVADO por defecto. Al entrar en un sistema aparece un mensaje sobre Elite durante unos 2,5 segundos. «EDSM: CONOCIDO» significa una coincidencia EDSM válida para el sistema. «EDSM: NO CONOCIDO» significa una respuesta EDSM válida sin coincidencia. «EDSM: SIN RESPUESTA» significa un error de red, HTTP, tiempo de espera agotado o respuesta inválida, nunca una ausencia confirmada de coincidencia. La presencia en EDSM no equivale a un descubrimiento oficial en Elite; no se prometen nombres de primeros descubridores o informantes. El mensaje funciona independientemente de los HUD de navegación y carga.

- El historial de visitas incluye Location, FSDJump y CarrierJump durante la lectura en directo del diario. Varios eventos de posición en una misma estancia ininterrumpida cuentan como una visita: A → A → A cuenta una vez. Se conserva un regreso real: A → B → C → A cuenta cuatro visitas.

- Al finalizar tu propio cartografiado DSS se guardan de forma fiable la hora, las sondas utilizadas y el objetivo de eficiencia. Los escaneos posteriores ya no hacen perder los datos existentes.

- La ventana de carga adapta automáticamente su altura al contenido. Con muchas entradas la altura se limita y la tabla permite desplazamiento; se conservan el ancho elegido y la posición. El interruptor existente «HUD de carga» está ahora en «mostrar automáticamente», sin otro interruptor en la ventana de carga.

- En instalaciones existentes normalmente basta con instalar la actualización → iniciar CMDRHelper. Las correcciones históricas necesarias de datos BIO, visitas y metadatos DSS se ejecutan automáticamente; se crea una copia de seguridad de la base antes de las reparaciones que escriben datos. Las reparaciones tienen versiones y son idempotentes: las revisiones completadas no se ejecutan íntegramente en cada inicio. La reconstrucción requiere diarios de Elite que aún existan, sean legibles y se puedan asignar inequívocamente a un comandante. No se inventan fuentes ausentes ni se consideran un éxito; las reparaciones pendientes se reintentan al iniciar de nuevo. Normalmente no hace falta borrar la base, usar scripts manuales ni reimportar.

## Explorer

El Explorer muestra el sistema actual en tres vistas:

- **Mapa del sistema:** representación gráfica de estrellas, planetas y lunas conocidos. Un clic en un cuerpo abre sus detalles. «Mostrar todo» abre el resumen del sistema.
- **Lista de valores:** La lista de valores muestra estimaciones según el escaneo guardado, no pagos pendientes garantizados. Las bonificaciones de primicia siguen sin confirmarse. Las ayudas del mapa y la lista y los detalles del cuerpo usan los mismos estados situados en el tiempo.
- **BIO / GEO / ABBAU:** señales biológicas y geológicas, lugares de extracción planetaria y hallazgos personales confirmados.

Los análisis distinguen las señales notificadas de los hallazgos personales reales. **BIO ×N** es el número de señales notificadas, no una confirmación de especies totalmente analizadas. **MINERÍA ×N** cuenta lugares de extracción planetaria sin revelar sus recursos individuales. Las mercancías extraídas personalmente, los materiales secundarios recogidos durante la extracción y la composición general de materiales del cuerpo permanecen separados.

El Explorer también muestra valores BIO estimados, progreso de análisis propios y datos cartográficos y BIO sin vender. Los valores se basan en la información disponible del diario y de los cuerpos; los datos ausentes no se presentan como descubrimientos propios. Los datos EDSM adicionales son información externa que debe distinguirse de los hallazgos personales.

Los detalles del cuerpo incluyen propiedades físicas disponibles, atmósfera, anillos, materiales e información de descubrimiento. Las representaciones usan texturas adecuadas y animaciones para ciertos objetos astronómicos especiales. El área Cargo muestra la carga y capacidad conocidas de la nave o SRV en uso; en el Rhino, carga y hallazgos mineros personales siguen siendo datos diferentes.

En la parte superior del Explorer están **★ Favoritos | Navegación planetaria | Mostrar todo**. Favoritos y navegación planetaria abren sus propias ventanas; las tres vistas del Explorer siguen disponibles.

## Navegación planetaria

El navegador planetario ayuda exclusivamente a volar a una **latitud/longitud concreta en un planeta o luna**. Para viajar entre sistemas estelares existe un planificador de rutas separado.

### Introducir un destino y volar

Selecciona el cuerpo de destino o usa el actual, detectado automáticamente cuando sea posible. Introduce latitud, longitud y, opcionalmente, un nombre. No tienes que introducir datos técnicos como BodyID o SystemAddress. **0,0** también es una coordenada válida.

En cuanto Elite proporciona datos válidos de posición planetaria para el cuerpo correspondiente, la brújula se activa automáticamente. Sin datos correspondientes, el navegador muestra un estado de espera. Puedes fijar nuevas coordenadas de destino en el mismo cuerpo en cualquier momento; sustituyen el destino anterior.

### Visualización durante la aproximación

| Distancia al destino | Visualización |
| --- | --- |
| **Más de 380 km** | Globo planetario con tu posición como círculo blanco y el destino como un pequeño punto. El destino es naranja en la cara visible y rojo en la cara oculta. La posición del jugador permanece fija en la representación; planeta y destino se muestran respecto a ella. |
| **Hasta 380 km inclusive** | Cambio automático a una cuadrícula en perspectiva inclinada con **intervalos de distancia de 50 km** y la posición del destino dibujada dentro para continuar la aproximación. |

La ventana del navegador se puede redimensionar libremente. Globo o cuadrícula se adaptan proporcionalmente al espacio disponible; los valores detallados siguen siendo legibles.

### Comprender los valores de navegación

- **Coordenadas del destino:** latitud y longitud guardadas del destino.
- **Coordenadas actuales:** tu última posición planetaria válida.
- **Distancia al destino / Distancia sobre la superficie:** distancia calculada al destino sobre la superficie esférica; el valor grande y el detallado muestran la misma distancia con distinto redondeo.
- **Demora:** dirección absoluta desde la posición actual al destino.
- **Heading:** tu orientación actual notificada por Elite.
- **Dirección relativa:** diferencia entre heading y demora, por ejemplo «23° a la derecha», «a la izquierda» o «recto».
- **Rumbo al objetivo:** rumbo absoluto al que puedes girar en el HUD de Elite. Coincide con la demora y no es un ángulo relativo de giro adicional.

Ejemplo: **Heading 051° → Rumbo al objetivo 074° = 23° a la derecha**.

La navegación depende de los datos de estado del juego; las actualizaciones pueden llegar con retraso según su estado. La distancia sobre la superficie no es una ruta por terreno o carretera. No se consideran obstáculos ni elevaciones del terreno a lo largo del trayecto.

## HUD de navegación

A la izquierda, en **mostrar automáticamente → HUD de navegación**, puedes activar una visualización adicional opcional directamente sobre Elite. Con navegación planetaria válida muestra:

- dirección relativa,
- rumbo al objetivo absoluto,
- distancia.

El HUD es transparente, deja pasar los clics y no toma el foco: no quita al juego clics de ratón ni foco de entrada. Sin navegación válida se vuelve invisible automáticamente; la casilla lateral puede permanecer activada. El navegador normal funciona independientemente del HUD.

El HUD se ha probado en el juego bajo **Linux/X11** y **Windows 11 con Elite**. En Windows, la asignación de varios monitores usa su geometría y la posición de la ventana de Elite, no nombres de monitor coincidentes.

## Favoritos

**Explorer → ★ Favoritos** abre una ventana independiente y reutilizable. Los favoritos pertenecen al **comandante activo**. Cambiar de comandante actualiza la vista; la selección de comandantes en la crónica no amplía la lista de favoritos.

### Guardar tres tipos

La fila superior de acciones ofrece:

| Acción | Favorito guardado |
| --- | --- |
| **★ Guardar sistema actual** | El sistema actual sin coordenadas de superficie. |
| **★ Guardar planeta / luna** | Un planeta o luna conocidos seleccionados del sistema actual, sin coordenadas de superficie. |
| **★ Guardar ubicación actual** | Un lugar en superficie con sistema, cuerpo, latitud y longitud actuales. |

El botón de ubicación siempre permanece visible y solo está disponible con datos actuales válidos de posición planetaria y un comandante activo. **El clic fija comandante, sistema, cuerpo y coordenadas antes de abrir el diálogo de edición.** Los movimientos posteriores en el juego no cambian esa posición. El mismo proceso de guardado está disponible en el navegador planetario. Los identificadores internos conocidos se incorporan automáticamente; no se inventan coordenadas.

Elige un nombre y exactamente una categoría: **Bio, Geo, Minería, Vista, Lugar de aterrizaje, Interesante u Otros**. Nota e imagen son opcionales.

### Buscar, ver y editar

La lista desplazable, ordenada alfabéticamente por nombre, muestra nombre, tipo, sistema, cuerpo y coordenadas cuando corresponda, categoría y una pequeña vista previa. **Búsqueda de texto libre y filtros por tipo y categoría** se pueden combinar. La búsqueda abarca nombre, sistema, cuerpo y nota.

**Abrir / Mostrar** muestra datos guardados, nota y una vista previa más grande. **Mostrar en Explorer** usa el resumen de sistema o detalles del cuerpo existentes si el favorito pertenece al sistema actual del Explorer y hay datos correspondientes. Para otros sistemas siguen disponibles los datos guardados del favorito.

**Editar** cambia nombre, categoría, nota e imagen. Sistema, cuerpo y coordenadas guardadas no se sustituyen por valores en directo. Para otra posición, crea un nuevo favorito de superficie.

**Eliminar** requiere confirmación y borra únicamente el registro del favorito y su copia interna de imagen. Se conservan los datos del Explorer, del diario y de los cuerpos.

### Imágenes de favoritos y última captura

Las imágenes de favoritos están **totalmente separadas del apartado normal Imágenes**. CMDRHelper administra su propia copia interna en la carpeta de imágenes de favoritos (`data/favorites/images/` con la disposición habitual de datos). El original no se mueve ni se modifica.

- **Elegir imagen …** acepta PNG, JPEG o WebP y muestra una vista previa. La copia interna se crea solo al guardar.
- **Usar última captura** vuelve a escanear la carpeta de origen real de capturas con cada clic. También tiene en cuenta las capturas Elite convertidas correspondientes en la carpeta del comandante activo dentro del destino de conversión configurado. Así, una captura nueva sigue disponible aunque la conversión automática ya haya borrado su BMP.
- Se ofrecen archivos legibles con nombres Elite o de conversión adecuados, no imágenes arbitrarias de carpetas generales. El orden usa una hora de captura inequívoca en el nombre del archivo o, en su defecto, la fecha del archivo. Para imágenes convertidas se usa la hora de captura guardada en el nombre, no la hora de conversión.
- Antes de aceptar una captura encontrada, ves nombre del archivo, fecha y hora de captura y una vista previa recién cargada. Confirma con **Usar esta imagen**. Si no hay una captura adecuada, la selección manual sigue disponible. CMDRHelper no realiza capturas por sí mismo.

Una imagen puede sustituirse o retirarse después. Las copias internas que ya no se necesitan se eliminan al guardar o borrar el favorito. **Las acciones de favoritos nunca eliminan la captura original ni una imagen original seleccionada.** Si falta un archivo de imagen interno, el favorito sigue siendo utilizable sin vista previa.

### Favorito de superficie como destino

**▶ Ir al destino** pasa cuerpo, latitud, longitud y nombre del favorito guardados al navegador planetario existente y sustituye su destino anterior. Los favoritos no tienen lógica de navegación propia. Los datos planetarios válidos correspondientes inician la navegación; de lo contrario, el navegador espera como siempre.

Los favoritos de otros comandantes no pueden usarse como destinos propios. Cambiar de comandante termina un destino que siga gestionándose como favorito del comandante anterior. Los favoritos de sistema y cuerpo muestran información existente, sin planificación de rutas propia.

## Crónica

La crónica es tu historial guardado de viajes y hallazgos. Su **mapa de viaje 3D** muestra sistemas visitados y rutas de comandantes. Los detalles de sistemas y cuerpos ayudan a encontrar de nuevo información conocida sobre BIO, GEO, materiales, Codex y minería.

### Filtros combinados

**Aplicar** o **Intro en el campo de texto libre** ejecuta juntos todos los filtros establecidos:

- texto libre,
- opcionalmente **Desde** y **Hasta**,
- **Yacimientos mineros planetarios** y **Al menos**,
- **Mis hallazgos mineros** y **Mercancía**.

Un término de **Ayuda de búsqueda / Leyenda** se incorpora al campo de búsqueda y se ejecuta junto con los filtros de período y minería ya establecidos.

### Período en UTC

Desde y Hasta se activan con sus respectivas casillas. También puede usarse un único límite; sin casilla activada no hay restricción temporal en ese lado. **Desde** incluye el inicio del día natural UTC seleccionado. **Hasta** abarca el día UTC seleccionado completo. UTC es la base horaria común, no tu hora de calendario local.

Son decisivas las **visitas reales a sistemas**: al menos una visita guardada debe estar dentro del período. Que un sistema se conozca por primera o última vez no sustituye una visita. Con un período activo, número de visitas, primera y última visita en el mapa se refieren a las visitas filtradas.

El período filtra visitas, no eventos individuales de descubrimiento, BIO, GEO o minería. La información conocida de hallazgos y las cantidades mineras personales siguen siendo **totales** guardados. **«Cobre 56 t» con un período activo no significa automáticamente «56 t durante este período».** Si Desde es posterior a Hasta, aparece un error y no se inicia ninguna consulta a la base de datos.

### Comandante y actualización

La **selección de comandantes del mapa** determina las rutas mostradas. Las búsquedas personales de texto libre y minería se refieren, en cambio, al comandante consultado o activo. Las casillas del mapa no amplían automáticamente las búsquedas personales a varios comandantes.

**Actualizar crónica** recarga los datos y vuelve a ejecutar los filtros activos. **Posición actual** aplica primero el estado actual de los filtros y centra el sistema actual solo si está incluido en el mapa resultante. En caso contrario aparece un aviso; los filtros se conservan.

**Restablecer** vacía el texto libre, desactiva Desde/Hasta y restablece los campos de fecha visibles. Se desmarcan las casillas mineras, la cantidad mínima pasa a 0 y la mercancía a Todas. La selección de comandantes permanece; después se carga la crónica normal.

Si **no hay resultados**, se vacían mapa y rutas, se vacía y oculta la lista de resultados, se restablecen los detalles y se cierra cualquier ventana abierta de detalles de sistema de la crónica. Los resultados antiguos no permanecen visibles.

### Manejar el mapa

- Arrastrar con el botón izquierdo: girar.
- Arrastrar con el botón derecho: desplazar.
- Arrastrar con el botón central: trazar un recuadro de zoom.
- Rueda del ratón: zoom.
- **Alinear:** restablecer la orientación a la vista galáctica desde arriba; desplazamiento y zoom se conservan.

## Imágenes y conversión automática de capturas

En **Imágenes** configuras la carpeta de origen de capturas Elite y el destino de conversión. La conversión automática transforma los nuevos BMP en **PNG o JPEG**. Hay un aclarado ajustable. Los BMP ya presentes al iniciar no se convierten retroactivamente solo por activar la supervisión; para ellos existe la conversión manual.

Los nombres de archivos convertidos contienen hora de captura, comandante y sistema y se almacenan por comandante. La asignación automática sigue al comandante del diario activo. Otra selección en la galería no cambia ese comandante activo.

La opción de **eliminar el BMP original tras una conversión correcta** pertenece exclusivamente a esta conversión y tiene su propio ajuste. Es independiente de la gestión de imágenes de favoritos.

La galería muestra las imágenes convertidas correspondientes con vista previa. Al volver a mostrarse se lee de nuevo; actualizar también tiene en cuenta los archivos actuales. Selección y vista previa grande se actualizan juntas. Si desaparece la imagen seleccionada, se elige otra existente o se vacía la vista previa. Imágenes también tiene selección de imágenes y eliminación con confirmación propias.

## Otras vistas

- **Resumen:** comandante activo, nave, ubicación, detección del diario, misiones abiertas y estado en línea.
- **Misiones:** misiones abiertas guardadas de forma persistente con destinos conocidos, progreso y estado de finalización. Los datos ausentes no se completan ni inventan.
- **CMDR:** patrimonio, rangos, estadísticas, MercCoins, naves/flota y ubicación conocida del Fleet Carrier. Los MercCoins se muestran como totales notificados por Frontier, no como saldo calculado por la aplicación.
- **Planificador de rutas:** planificación separada para nave y Fleet Carrier con Spansh. Las rutas calculadas de carrier se pueden exportar en CSV para CTSVision. El cálculo requiere conexión al servicio externo.

## Comandante, datos locales y servicios en línea

CMDRHelper identifica al comandante activo por el ID de Frontier de la sesión de diario actual. Exploración personal, misiones, patrimonio, favoritos y credenciales en línea se guardan por separado. Consultar otro comandante no cambia el comandante en directo ni la asignación de sus envíos.

La base SQLite local conserva sistemas, cuerpos e historial personal tras los reinicios. Las nuevas entradas completas del diario se procesan durante el juego; las posiciones de lectura guardadas evitan releer innecesariamente. Si ubicación o comandante no coinciden, revisa primero la detección del diario y su carpeta en los ajustes.

**EDSM** puede proporcionar datos de sistema adicionales. Los datos de diario compatibles pueden enviarse a **EDSM e Inara** si el servicio está configurado y activado con las credenciales propias del comandante activo. Un comandante no usa automáticamente la clave API de otro. El almacenamiento local funciona independientemente de una conexión en línea disponible.

## Idiomas y ayuda contextual

La interfaz admite **12 idiomas**: **DE, EN, FR, IT, NO, SV, FI, PL, NL, ES, TR, EL** – alemán, inglés, francés, italiano, noruego, sueco, finés, polaco, neerlandés, español, turco y griego.

Actualmente hay **937 claves UI-i18n por idioma**. **? Ayuda** ofrece **10 temas detallados de ayuda contextual en los 12 idiomas**. Favoritos forma parte de la ayuda del Explorer; navegación planetaria tiene un tema propio accesible directamente desde el navegador. La ayuda usa el idioma actual de la interfaz y conserva alemán como alternativa si falta un catálogo o entrada.

## Requisitos

| Plataforma | Python |
| --- | --- |
| **Windows** | **Python 3.10 o posterior, x64 obligatorio.** Sin límite superior artificial para versiones existentes. Después deciden las comprobaciones reales de paquetes e importaciones. |
| **Linux** | **Python 3.10 o posterior**, 64 bits recomendado. Debe estar disponible el módulo venv correspondiente a la versión de Python. |

Los paquetes necesarios están en `requirements.txt`:

```text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

La instalación descarga estas dependencias. Los archivos locales de Elite deben ser accesibles para analizar diarios y navegar por planetas. En Linux Elite puede ejecutarse mediante Steam/Proton; configura las rutas reales de diarios y capturas en CMDRHelper. El soporte del HUD para Linux descrito arriba se refiere a X11.

## Instalación en Linux

Extrae el proyecto o la versión completos y ejecuta en la carpeta del proyecto:

```bash
./install.sh
./start.sh
```

Los scripts usan exclusivamente el `venv` local de esta instalación. Resuelven enlaces simbólicos de scripts, comprueban Python y pip y pueden reparar un entorno local dañado sin tocar datos personales ni diarios de Elite. No instalan automáticamente paquetes del sistema ausentes; el instalador informa si falta el módulo venv. El procedimiento existente de Linux permanece sin cambios.

## Instalación en Windows

1. Extrae el ZIP completo en una carpeta propia.
2. Ejecuta **install.bat**, que llama al archivo incluido **install-windows.ps1**.
3. Tras una instalación correcta, inicia CMDRHelper con **start.bat**.

Se acepta un **Python existente desde 3.10, x64**, sin límite superior artificial. Una futura versión de Python no se rechaza solo por su número. Un Python existente adecuado o un venv local utilizable evita una instalación automática innecesaria de Python.

Si no hay Python adecuado, el instalador ofrece, tras tu consentimiento, instalarlo automáticamente mediante **winget**. Se elige deliberadamente la serie fija **Python 3.14 x64** para ello; esta elección es independiente de la regla abierta para versiones ya existentes. Si la instalación automática no es posible, el instalador informa del error.

El instalador crea, comprueba o repara solo el **venv local de esta copia de CMDRHelper**, instala las dependencias y ejecuta **pip check** y comprobaciones de importación de **PySide6, PySide6.QtWidgets, numpy y PIL**. Solo estas pruebas reales determinan la utilidad del entorno. Si fallan, la instalación se interrumpe con un error comprensible. Otros entornos virtuales no se reparan ni sustituyen.

## Diagnóstico y paquetes de distribución

Ante problemas ayudan los indicadores de diario y estado en línea y los archivos de registro de la carpeta `logs`. Los datos personales se almacenan localmente; una copia de seguridad de favoritos debe incluir sus copias internas de imágenes además de la base de datos.

Para crear tu propio paquete de distribución está disponible `./create_release.sh`. La versión del programa se gestiona centralmente en `cmdrhelper/version.py` y la lee el script de distribución. El paquete contiene código y recursos, sin base personal, venv, archivos Git ni caché.

## Material gráfico y de vídeo / Media Credits

CMDRHelper utiliza para algunos objetos astronómicos especiales
visualizaciones del **NASA Scientific Visualization Studio (NASA SVS)**.
Los respectivos medios siguen siendo propiedad de sus titulares de
derechos y se acreditan conforme a la información indicada en las
páginas de NASA SVS.

### Estrella de neutrones

-   Archivo de CMDRHelper: `star_neutron.webm`
-   Fuente: NASA Scientific Visualization Studio, **Neutron Star
    Animations** (SVS ID 20267)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animadores: Walt Feimer (KBR Wyle Services, LLC) y Lisa Poje (USRA)
-   Fuente: https://svs.gsfc.nasa.gov/20267/

### Agujero negro

-   Archivo de CMDRHelper: `black_hole.mp4` o la extensión de vídeo
    utilizada en el proyecto
-   Fuente: NASA Scientific Visualization Studio, **Black Hole Accretion
    Disk Visualization** (SVS ID 13326)
-   Credit: **NASA's Goddard Space Flight Center/Jeremy Schnittman**
-   Fuente: https://svs.gsfc.nasa.gov/13326/

### Agujero negro supermasivo

-   Archivo de CMDRHelper: `black_hole_supermassive.mp4` o la extensión
    de vídeo utilizada en el proyecto
-   Fuente: NASA Scientific Visualization Studio (SVS ID 14576)
-   Credit: **NASA's Goddard Space Flight Center/J. Schnittman and B.
    Powell**
-   Fuente: https://svs.gsfc.nasa.gov/14576/

### Enana blanca

-   Archivo de CMDRHelper: `star_white_dwarf.webm`
-   Medio de NASA utilizado: **White Dwarf establishing shot**
    (`WDStar_4k_60fps_ProRes.webm`)
-   Fuente: NASA Scientific Visualization Studio, **Type Ia Supernovae
    Animations** (SVS ID 20344)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animadora: Adriana Manrique Gutierrez (USRA)
-   Producer: Scott Wiessinger (USRA)
-   Fuente: https://svs.gsfc.nasa.gov/20344/

La mención de estas fuentes y créditos no significa que CMDRHelper esté
respaldado, certificado o publicado por NASA. Para la reutilización de
los medios de NASA se aplican las indicaciones y directrices de
reproducción correspondientes de las fuentes originales.

## Licencia

CMDRHelper es software libre y se publica bajo la **GNU General Public
License Version 3 (GPL-3.0)**.

El código fuente puede utilizarse, modificarse y redistribuirse conforme
a las condiciones de la GPL-3.0. La distribución de versiones derivadas
también está sujeta a las condiciones de la GPL-3.0.

Copyright © 2026 **Holger Mangold (Faber38)**.

Las condiciones completas de la licencia se encuentran en el archivo
`LICENSE`.

## Nota sobre Elite Dangerous

CMDRHelper es un proyecto independiente de la comunidad/aficionado y no
es un producto oficial de Frontier Developments.

**Elite Dangerous** y los nombres y contenidos asociados pertenecen a
sus respectivos titulares de derechos.
