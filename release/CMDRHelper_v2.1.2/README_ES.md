# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Tu copiloto para Elite Dangerous](cmdrhelper/assets/readme/cmdrhelper_readme_es.png)

**Compañero personal para Elite Dangerous -- exploración, análisis de
sistemas y datos del Commander de un vistazo**

CMDRHelper es un programa de escritorio independiente para **Elite
Dangerous** que analiza la información de los archivos Journal locales
del juego y la presenta de forma clara. El objetivo es ofrecer un
asistente personal que, durante la exploración de un sistema, muestre
rápidamente qué se conoce ya, qué cuerpos celestes son interesantes y
qué descubrimientos y cartografiados ha realizado personalmente el
Commander.

El proyecto continúa en desarrollo activo.

## Resumen de funciones

### Journals de Elite Dangerous

CMDRHelper lee los archivos Journal locales y procesa, entre otras
cosas, sistemas estelares, estrellas, planetas, lunas, Belt Clusters,
escaneos, cartografiados y señales biológicas y geológicas. Los datos
propios del Commander pueden seguir distinguiéndose de la información
externa complementaria.

### Misiones

CMDRHelper analiza los eventos de misión de los Journals de Elite
Dangerous y muestra claramente las misiones activas. Se realiza un
seguimiento del estado de las misiones y de los eventos Journal
asociados.

También pueden reconocerse las ofertas de misión que llegan durante el
juego mediante mensajes de NPC (`ReceiveText`) y tenerse en cuenta para
la posterior asignación de misiones. Como Elite Dangerous no proporciona
para todos los tipos de misión toda la información en un mismo evento
Journal, la asignación se construye progresivamente a partir de los
datos Journal disponibles.

### Vista del sistema y Explorer

Los cuerpos conocidos de un sistema se representan gráficamente y pueden
seleccionarse directamente. CMDRHelper puede mostrar, entre otras cosas:

-   nombre y tipo del cuerpo
-   distancia dentro del sistema
-   escaneado personalmente o conocido únicamente por fuentes externas
-   ya descubierto y cartografiado
-   posible primer descubrimiento y posible First Mapping
-   cartografiado por el Commander
-   cartografiado eficiente
-   señales biológicas y geológicas
-   valores de escaneo y cartografiado

Las señales BIO se resaltan claramente en el cuerpo correspondiente. La
asignación se realiza por sistema para evitar confundir BodyID
pertenecientes a sistemas estelares diferentes.

### Vista detallada de cuerpos

Al hacer clic en un cuerpo se abre una vista detallada. Dependiendo de
los datos disponibles se muestran el tipo de cuerpo, masa, distancia,
gravedad, atmósfera, vulcanismo, posibilidad de aterrizaje, estado de
terraformación, materiales, señales BIO/GEO, valor de escaneo, valor de
cartografiado y estado del descubrimiento.

La información que falta se muestra como desconocida y no se presenta
como un dato confirmado.

## Representación gráfica de los cuerpos

CMDRHelper dispone de gráficos específicos para numerosos tipos de
cuerpos, entre ellos High Metal Content Worlds, Metal Rich Bodies, Rocky
Bodies, Icy Bodies, Rocky Ice Worlds, Earth-like Worlds, Water Worlds,
Ammonia Worlds, varias clases de gigantes gaseosos, gigantes gaseosos
con vida basada en agua o amoníaco, gigantes gaseosos ricos en helio,
diferentes clases estelares y Belt Clusters.

Las imágenes PNG normales se utilizan en las vistas generales. Para
muchos cuerpos también está disponible una **textura equirectangular 2:1
`_texture.png`** para la vista detallada animada.

### Planetas 3D en rotación

Las texturas 2:1 adecuadas se proyectan sobre una esfera en rotación. El
renderizador por CPU utiliza **PySide6 y NumPy** sin dependencias
adicionales de OpenGL/PyOpenGL. Incluye proyección esférica, rotación
lenta, iluminación, oscurecimiento del borde y borde atmosférico.

### Formas de vida animadas

Para los gigantes gaseosos con vida existen diferentes animaciones:

**Water Life:** organismos flotantes de color cian/turquesa con halo y
colas en movimiento.

**Ammonia Life:** organismos específicos de color violeta/ámbar,
semitransparentes, con núcleo pulsante, filamentos cortos y movimiento
más lento.

### Belt Clusters animados

Los Belt Clusters no se representan como esferas. La vista detallada
genera un campo de asteroides procedural con asteroides individuales,
diferentes tamaños y profundidades, rotación propia, deriva individual,
efecto de paralaje, cráteres y discretos efectos de polvo y partículas.

## EDSM como fuente de datos complementaria

CMDRHelper puede distinguir los datos propios del Journal de la
información de EDSM. La fuente se marca correspondientemente como
Journal propio, EDSM o Journal propio + EDSM. Los datos propios del
Journal son especialmente importantes porque muestran qué ha escaneado o
cartografiado realmente el Commander por sí mismo.

CMDRHelper puede transferir automáticamente a EDSM los nuevos datos del
Journal. Se tiene en cuenta la lista dinámica actual EDSM Discard para
que solo se envíen los eventos que EDSM desea recibir. El progreso de la
transferencia se guarda de forma segura para cada archivo Journal. En la
primera activación, los Journals antiguos ya existentes no se vuelven a
transferir íntegramente.

El estado de EDSM se muestra directamente en la parte superior de la
vista general. Un indicador verde señala que la transferencia funciona;
los errores se muestran en rojo y además se registran en el log de
CMDRHelper.

## Base de datos local

CMDRHelper utiliza SQLite. Se aplican las siguientes reglas:

-   `cmdrhelper/database.py` es código del programa y forma parte de la
    release.
-   `data/cmdrhelper.db` contiene datos personales del Commander y
    **no** se distribuye.
-   En una instalación nueva, la base de datos local se vuelve a crear
    para el usuario correspondiente.

De este modo no se distribuyen datos personales del Commander junto con
una release.

## Diagnóstico y archivo de log

CMDRHelper mantiene su propio archivo de log rotativo para diagnóstico y
localización de errores. Se registran eventos importantes del programa,
Journal, base de datos y EDSM. El registro de EDSM se ha reducido para
que los eventos Journal simplemente descartados por EDSM no llenen
innecesariamente el log normal, mientras que las transferencias
correctas, advertencias y errores siguen siendo visibles.

## Plataformas

CMDRHelper se desarrolla con Python y PySide6 y está destinado a **Linux
y Windows**. El desarrollo se realiza principalmente en Linux; Windows
puede configurarse mediante los archivos batch incluidos.

## Requisitos

Python **3.10 a 3.13** y los paquetes indicados en `requirements.txt`:

``` text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

## Instalación en Linux

``` bash
./install.sh
./start.sh
```

Estos scripts usan exclusivamente el `venv` local de la instalación y pueden
repararlo con prudencia sin tocar datos personales.

## Instalación en Windows

Para Windows están previstos `install.bat` y `start.bat`.

`install.bat` comprueba Python 3.10–3.13, crea o repara el `venv` local e instala
`requirements.txt`. A continuación CMDRHelper se inicia mediante
`start.bat`.

## Crear una release

``` bash
./create_release.sh
```

La versión de la release se establece directamente en el script. El
archivo ZIP generado contiene el código del programa y los assets, pero
no la base de datos personal, el entorno virtual de Python ni archivos
Git, de caché o del editor.

## Versión 2.1

**La versión 2.1** mejora la biología, la vista de flota y el rendimiento con
grandes archivos de diarios. También refuerza instalación, inicio,
actualización y reversión en Windows y Linux.

### Predicciones biológicas y hábitat

-   cuando hay datos suficientes, la nueva predicción muestra Species
    concretas posibles y no solo el género. Puede mostrar varias con confianza
    **ALTA**, **MEDIA** o **BAJA**; las muestras pequeñas se tratan de forma
    conservadora.
-   una Species encontrada o identificada sustituye su predicción. Cuando se
    conocen todas las señales BIO, desaparecen las predicciones restantes.
-   el popup BIO compacto muestra valores estimados de candidatos y un total
    posible del cuerpo. Naranja/dorado significa estimado y verde confirmado;
    no se añaden bonificaciones especulativas de First Footfall.
-   temperatura, presión, composición atmosférica, radio y contexto de
    estrella/parent amplían los datos de hábitat. No hay predicción general de
    variantes o colores.

### Flota del CMDR

-   la flota se ordena ascendente o descendentemente por último uso, nombre,
    tipo, alcance de salto, carga, masa en vacío, ubicación o fecha.
-   los filtros muestran todas las naves o las equipadas con hangar de
    vehículos o fighters, detectados en módulos Loadout reales. Los SRV y
    fighters siguen siendo equipo de la nave nodriza.

-   el filtro reconoce `int_buggybay_*` y el nuevo hangar grande
    `int_mkiilargebuggybay_*`, sin inventar su contenido. `mev_rhino` se trata
    como SRV/vehículo terrestre, no como nave independiente, sin afirmar que
    siempre se conozca su hangar actual.

### Estado persistente del comandante y reinicio

-   misiones, datos bio/cartográficos pendientes, última ubicación, naves y
    loadouts, Fleet Carrier propio y patrimonio permanecen en SQLite tras
    reiniciar CMDRHelper o Elite.
-   un estado sigue conocido hasta que un evento Journal real lo cambie; la
    ausencia de información en una sesión nueva no borra datos conocidos.
-   tras una interrupción se continúa desde el último punto seguro; una última
    línea incompleta no se considera procesada.
-   v2.1 puede reconstruir una vez y de forma controlada los estados afectados
    desde Journals existentes y después continúa incrementalmente.

### Ubicaciones mineras planetarias y materiales superficiales

-   `FSSBodySignals`/`SAASignalsFound` notifican **ubicaciones mineras
    planetarias**, mostradas junto a BIO/GEO como **MINERÍA ×N** localizada. N
    es el número de Frontier para el cuerpo, no un índice calculado.
-   `Scan.Materials` se guarda por cuerpo; nombres y porcentajes se presentan
    como **materiales de superficie del cuerpo**, también en la ayuda emergente.
-   cantidad y composición general permanecen separadas; los materiales no se
    atribuyen a una ubicación minera concreta.

### Diarios, archivo y rendimiento

-   `Journal.YYMMDDHHMMSS.PART.log` y
    `Journal.YYYY-MM-DDTHHMMSS.PART.log` se procesan juntos en orden correcto,
    evitando que diarios antiguos sustituyan al CMDR o estado actual.
-   eventos Signal/Mapping de archivos incompletos se importan sin un Body Scan
    completo previo; escaneos posteriores completan los datos y se conserva la
    separación multi-CMDR.
-   un índice persistente omite diarios conocidos sin cambios. El diario activo
    se lee incrementalmente desde la última posición de byte segura; metadatos
    y SHA-256 protegen su identidad y la asignación por FID no cambia.
-   la primera indexación grande muestra cifras reales, porcentaje y pequeñas
    naves animadas en una vista responsiva. Los inicios rápidos posteriores
    normalmente no la muestran.

-   tras crear el índice solo se procesan líneas nuevas y completas. Cambios y
    posición segura se guardan juntos; un error no avanza la posición y una
    línea parcial queda pendiente.
-   el inicio rápido obtiene el CMDR activo de la sesión indexada inequívoca más
    reciente, carga de inmediato su estado y toma del índice el número de Journals.

### Instalación y actualización

-   los scripts reforzados de Windows y Linux admiten Python 3.10–3.13, usan
    exclusivamente el `venv` local y reparan con seguridad un entorno local
    dañado. Los enlaces simbólicos Linux se tratan con prudencia; nunca se usan
    entornos ajenos.
-   actualizaciones y reversiones informan claramente de fallos y protegen los
    datos personales y diarios de Elite.
-   se admite la actualización normal de v2.0 a v2.1. Para instalaciones muy
    anteriores a v2.0, guarda los ajustes; ante problemas puede ayudar una
    instalación limpia. Nunca borres los diarios de Elite ni todos los datos
    antiguos de CMDRHelper como solución genérica.
-   con archivos enormes, el primer inicio v2.1 puede tardar una vez mientras
    crea el índice; los siguientes son considerablemente más rápidos.

## Versión 2.0

La **versión 2.0** añade compatibilidad Multi-CMDR real y conserva el
planificador de rutas de la versión 1.5 y las funciones existentes.

### Multi-CMDR y Vista CMDR

-   los comandantes se identifican automáticamente mediante su FID de
    Frontier. Solo el Journal determina el comandante en vivo; elegir otro
    perfil para consultarlo no cambia la asignación ni las escrituras en vivo.
-   visitas, exploración, misiones, ubicaciones, naves, Fleet Carrier,
    patrimonio y datos biológicos y cartográficos sin vender se guardan por
    separado para cada comandante.
-   la **Vista CMDR** permite consultar sin conexión cualquier comandante
    conocido: misiones, última ubicación y nave, Fleet Carrier y ubicación,
    patrimonio y estimaciones de datos biológicos y cartográficos pendientes.

### Crónica Multi-CMDR

-   cada comandante tiene un color estable y filtros individuales o conjuntos.
-   las rutas cronológicas permanecen separadas y nunca conectan saltos de
    comandantes distintos.
-   los sistemas visitados por varios comandantes muestran visitas múltiples.

### Flotas de comandantes

-   cada comandante dispone de una flota persistente con todas sus naves
    conocidas y detalles desplegables de equipamiento, alcance, depósitos,
    carga y última ubicación.
-   la nave en vivo se resalta en verde; las demás reciben colores estables
    según su ubicación y la lista dispone de desplazamiento vertical.
-   trajes, SRV como Scarab, Scorpion y Nomad, cazas embarcados, taxis y naves
    de descenso no se registran como naves normales del comandante.

### Bases de datos existentes

Las migraciones de esquema integradas conservan las bases de datos existentes.
Los datos Multi-CMDR se separan por FID de Frontier. Si datos antiguos pueden
pertenecer a varios perfiles, CMDRHelper no adivina ni los borra de forma
general: una asignación ambigua permanece sin resolver.

CMDRHelper sigue siendo compatible con **Linux y Windows** e incluye el
planificador de rutas para naves y Fleet Carrier de la versión 1.5.

## Versión 1.5

La **versión 1.5** es una gran actualización de funciones. Incorpora el
nuevo planificador de rutas para naves y Fleet Carriers, vincula el progreso
de la ruta con el Journal de Elite Dangerous y mejora su fiabilidad y
rendimiento, especialmente en Windows.

### Planificador y rutas de nave

-   el nuevo **Planificador de rutas** calcula rutas de nave mediante Spansh
    Galaxy Plotter y muestra todos los sistemas intermedios en CMDRHelper.
-   CMDRHelper detecta en el Journal la nave, el FSD, su engineering y el
    Guardian FSD Booster activo. Los valores disponibles de depósito, carga,
    masa y FSD se transfieren automáticamente.
-   los valores detectados siguen siendo editables. Las modificaciones
    manuales se conservan durante posteriores actualizaciones de Loadout,
    carga y combustible hasta que se vuelven a aplicar expresamente los
    datos detectados.
-   los cambios de Loadout, carga y combustible actualizan únicamente las
    entradas afectadas. Los valores desconocidos permanecen visiblemente
    vacíos y no se estiman.
-   antes del cálculo se comprueba que inicio y destino coincidan exactamente
    con sistemas de Spansh. Los sistemas desconocidos reciben un mensaje
    comprensible sin iniciar un trabajo que no puede completarse.
-   el progreso utiliza eventos `FSDJump` reales del flujo Journal existente.
    Tras un salto correcto, el siguiente sistema se copia automáticamente al
    portapapeles de Qt y también puede copiarse de nuevo manualmente.

### Fleet Carrier y CTSVision

-   un modo específico **Fleet Carrier / CTSVision** utiliza Spansh Fleet
    Carrier Router.
-   las rutas de Fleet Carrier contienen datos de saltos y Tritium y pueden
    exportarse como CSV compatible con CTSVision.

### Fiabilidad del Journal y rendimiento

-   un error de acceso temporal al Journal activo ya no confirma la
    actualización antes de tiempo: el ciclo normal de sondeo vuelve a
    intentarla sin espera activa agresiva.
-   el aprendizaje BIO y cartográfico ya no vuelve a recorrer todo el
    archivo de Journals para eventos normales no relacionados. Las
    evaluaciones completas se limitan a eventos BIO o de venta pertinentes y
    a la importación de archivo prevista.
-   esto reduce el trabajo innecesario en cada adición al Journal y mejora la
    fiabilidad y la respuesta, especialmente en Windows.

## Versión 1.0.8

La **versión 1.0.8** incorpora una recomendación de salto personal para
la exploración, completa la internacionalización y mejora las ventanas
en directo del Explorador y la representación del mapa de la Crónica.

### Consejo y recomendación de salto

-   la nueva sección **«Consejo de salto»** analiza la base de datos de
    exploración local del propio usuario y muestra qué códigos de sistemas
    procedimentales pueden resultar especialmente interesantes para un
    objetivo de exploración seleccionado.
-   se pueden seleccionar, entre otros objetivos, hallazgos BIO en general,
    géneros y especies BIO conocidos, cuerpos de exploración valiosos,
    candidatos a terraformación, mundos acuáticos, mundos de tipo terrestre
    y mundos de amoníaco.
-   la clasificación tiene en cuenta los sistemas examinados anteriormente
    con un código, los aciertos, la tasa de aciertos, los hallazgos guardados
    y el tamaño de la muestra disponible. Un mínimo ajustable de sistemas
    examinados evita sobrevalorar muestras demasiado pequeñas.
-   CMDRHelper destaca códigos preferentes que conviene buscar en el mapa
    galáctico, por ejemplo combinaciones como `ZL-Z b` o `NR-C d`.
-   la recomendación se basa exclusivamente en el **historial de exploración
    propio** y en los hallazgos guardados en él. Es una orientación
    estadística y **no garantiza ningún hallazgo**.

### Internacionalización

-   la internacionalización se ha seguido completando y se ha vuelto a
    contrastar con la referencia alemana.
-   los **12 idiomas de interfaz compatibles** disponen ahora del mismo
    conjunto completo de **560 claves de traducción**.
-   se han añadido en todos los idiomas las traducciones nuevas y las que
    faltaban para el **consejo y la recomendación de salto**.
-   se han igualado el conjunto y el orden de las claves, así como los
    marcadores de formato, en todos los archivos de idioma.

### Ventanas en directo y ajustes del Explorador

-   los ajustes del Explorador incluyen nuevos tooltips explicativos para
    la aparición automática de las ventanas **«Cuerpos valiosos»** y
    **«Hallazgos BIO»**.
-   los tooltips explican cuándo aparece automáticamente cada ventana según
    el umbral de valor configurado o las señales BIO o GEO detectadas.
-   los cuerpos valiosos ya cartografiados por el Commander dejan de
    mostrarse como objetivos pendientes en la pequeña ventana en directo.
-   los cuerpos BIO completamente analizados desaparecen de su ventana; si
    el mismo cuerpo tiene una parte GEO aún no cartografiada con el DSS,
    esta continúa visible.

### Crónica

-   se ha corregido la orientación del mapa de la Crónica para que el eje Z
    positivo apunte hacia arriba. Las coordenadas Elite `StarPos` guardadas
    permanecen sin cambios.

## Versión 1.0

Con la **Versión 1.0**, CMDRHelper alcanza el primer estado de
desarrollo completo del alcance básico previsto.

Cambios y ampliaciones importantes hasta la Versión 1.0:

### Representación de cuerpos y estrellas completada

-   el material gráfico para los tipos compatibles de planetas,
    estrellas y objetos especiales se ha completado aún más.
-   clases estelares adicionales y tipos especiales de estrellas se
    representan con gráficos propios en lugar de recurrir a la
    representación estándar general.
-   para los cuerpos adecuados siguen estando disponibles texturas
    equirectangulares 2:1 en rotación dentro de la vista detallada.
-   los objetos astronómicos especiales también pueden representarse en
    la vista detallada mediante vídeos apropiados.
-   las estrellas de neutrones, enanas blancas, agujeros negros y
    agujeros negros supermasivos reciben así una representación mucho
    más individual.
-   el material gráfico y de vídeo externo utilizado se documenta con
    fuente y crédito en la sección **«Material gráfico y de vídeo /
    Media Credits»**.

### Multilingüismo completado

-   las traducciones de la interfaz de usuario se han completado para
    los idiomas compatibles y se han alineado con un conjunto común de
    claves.
-   los **12 idiomas de la interfaz** utilizan el mismo conjunto
    completo de claves de traducción.
-   la comprobación automática de traducciones verifica claves ausentes,
    adicionales y duplicadas, así como placeholders de formato
    diferentes.
-   el alemán sirve como referencia completamente mantenida para la
    interfaz de usuario y la documentación futura.

### Cambios desde la Versión 0.9.9

### Multilingüismo y control de traducciones

-   la interfaz de usuario se ha convertido a un sistema multilingüe
    centralizado.
-   CMDRHelper admite ahora **12 idiomas de interfaz**: **alemán,
    inglés, francés, italiano, noruego (Bokmål), sueco, finlandés,
    polaco, neerlandés, español, turco y griego**.
-   el idioma puede seleccionarse y guardarse en los ajustes; los
    nombres de los idiomas se muestran en el campo de selección cada uno
    en su propio idioma.
-   las traducciones que faltan utilizan una secuencia de fallback
    definida: **idioma seleccionado → inglés → alemán → clave de
    traducción**.
-   las traducciones se almacenan de forma centralizada en los archivos
    de idioma bajo `cmdrhelper/i18n/`.
-   la nueva herramienta para desarrolladores `tools/check_i18n.py`
    comprueba automáticamente:
    -   las claves `tr("...")` utilizadas en el programa,
    -   claves de traducción ausentes o adicionales,
    -   claves duplicadas,
    -   placeholders de formato diferentes como `{system}` o `{count}`.
-   en Linux, la comprobación i18n se ejecuta automáticamente al iniciar
    mediante `start.sh`. Los problemas de traducción detectados se
    notifican claramente, pero no impiden el inicio del programa.
-   el procesamiento de misiones y Journal sigue separado del idioma de
    interfaz seleccionado en CMDRHelper, para que los datos internos de
    Elite Dangerous no dependan de textos de visualización localizados.

### Explorer y mapa del sistema

-   se ha revisado la estructura Parent/Child del mapa del sistema:
    estrellas, planetas, lunas y Belt Clusters se organizan según su
    jerarquía en el Journal.
-   nueva función **«Mostrar todo»** con una vista general compacta en
    miniatura de todo el sistema.
-   los cuerpos pueden seleccionarse en la vista en miniatura; el mapa
    principal salta entonces directamente al cuerpo seleccionado.
-   navegación mejorada en mapas de sistemas grandes:
    -   la rueda del ratón desplaza el mapa horizontalmente.
    -   manteniendo pulsado el botón derecho del ratón y arrastrando
        hacia arriba/abajo, el mapa se desplaza verticalmente.
-   los tamaños visuales de los cuerpos se escalan con mayor intensidad
    según su radio real.
-   se ha mejorado aún más la representación y el marcado de BIO, GEO,
    Terraforming, primer descubrimiento y First Mapping.
-   nueva **lista de valores** en Explorer: planetas y lunas se ordenan
    línea por línea según su valor de cartografiado estimado actual.
-   la lista de valores distingue ahora claramente entre **First Mapping
    posible**, **ya cartografiado** y **cartografiado personalmente**.
-   el valor de cartografiado obtenido actualmente se resalta de forma
    específica en la lista de valores, mientras que el estado y los
    metadatos se muestran deliberadamente de forma más discreta.
-   nueva indicación **«Aún no entregado»** para los valores de
    cartografía y BIO pendientes en todos los sistemas desde la última
    venta; cartografía y BIO se reinician por separado.
-   los valores pendientes de Explorer se resaltan en amarillo en la
    ventana principal para que los datos aún no vendidos sean
    inmediatamente reconocibles.

### Ventanas live de Explorer

-   nuevas **ventanas live de libre posicionamiento para cuerpos
    valiosos y hallazgos BIO**, que aparecen automáticamente durante la
    exploración.
-   la posición y el tamaño de las ventanas live se guardan y se
    reutilizan la próxima vez que aparecen.
-   al cambiar a otro sistema estelar, las ventanas live se cierran y
    vacían automáticamente; solo vuelven a aparecer cuando se detectan
    datos adecuados en el nuevo sistema.
-   la ventana **«Cuerpos valiosos»** incluye automáticamente todos los
    planetas y lunas cuyo valor de cartografiado actualmente alcanzable
    llega al umbral seleccionado en los ajustes.
-   el mismo umbral configurable controla ahora el resaltado amarillo de
    la lista de valores, la ventana live de cuerpos valiosos y el
    **marco dorado del mapa del sistema**.
-   la **ventana live BIO** muestra de forma compacta durante el juego
    los cuerpos, géneros o especies reconocidos, el progreso del escaneo
    y los valores conocidos de Vista Genomics.
-   los hallazgos BIO utilizan la misma lógica de colores que la ventana
    principal: gris = detectado mediante DSS/FSS, blanco = primera
    muestra, amarillo = segunda muestra, verde = análisis completado.
-   cuando existen señales BIO parcialmente determinadas, un planeta se
    expande automáticamente y muestra los hallazgos individuales en
    líneas separadas; las señales aún desconocidas permanecen visibles.
-   en cuanto todas las especies BIO de un cuerpo se han analizado por
    completo, el planeta vuelve a contraerse en una línea de resumen
    verde y compacta.
-   los nombres genéricos de géneros DSS/FSS se sustituyen
    automáticamente por la especie BIO concreta en cuanto se identifica
    mediante `ScanOrganic`.
-   los valores individuales conocidos se muestran directamente junto al
    hallazgo BIO correspondiente; los cuerpos completamente conocidos
    muestran además el valor total.
-   las ventanas live tienen un fondo discretamente marrón rojizo para
    distinguirse claramente de la ventana principal de CMDRHelper
    durante el juego.

### Análisis BIO

-   los datos biológicos se analizan y muestran por separado de los
    valores normales de cartografía.
-   lista propia de **planetas BIO** con todos los cuerpos en los que se
    han detectado señales biológicas.
-   los géneros BIO de `SAASignalsFound` o `FSSBodySignals` también se
    importan retrospectivamente de Journals existentes.
-   las especies y variantes BIO concretas de `ScanOrganic` se muestran
    directamente en la lista.
-   el progreso de escaneo de cada hallazgo BIO se representa mediante
    colores:
    -   gris = conocido únicamente mediante DSS/FSS
    -   blanco = primera muestra
    -   amarillo = segunda muestra
    -   verde = tercera muestra / análisis completado
-   el valor base conocido de Vista Genomics se muestra en cuanto una
    especie BIO se ha identificado de forma inequívoca.
-   visualización del valor base de las muestras BIO completamente
    analizadas.
-   visualización del posible **valor total First Logged ×5**.
-   los valores BIO conocidos pueden complementarse utilizando datos de
    venta ya existentes.
-   las especies sin valor conocido se marcan en el análisis.
-   el estado BIO distingue entre abierto, visitado y completamente
    analizado.

### Misiones

-   se ha mejorado el procesamiento de `MissionRedirected`.
-   las misiones redirigidas pueden adoptar el nombre, un nuevo sistema
    de destino o una nueva estación de destino, así como información
    sobre el destino anterior.
-   en determinados casos las misiones también pueden reconstruirse
    aunque anteriormente no existiera una entrada `MissionAccepted`
    completa.
-   el ancho de las columnas de las misiones puede ajustarse libremente;
    los anchos seleccionados se guardan.
-   visualización de la **recompensa total de todas las misiones
    actualmente abiertas**.

### Imágenes y capturas de pantalla

-   área propia de capturas de pantalla con galería y vista previa.
-   conversión automática de nuevas capturas BMP de Elite Dangerous.
-   salida en formato PNG o JPG.
-   eliminación opcional del archivo BMP tras una conversión correcta.
-   corrección de brillo configurable del 0 al 50%.
-   uso más cómodo de la carpeta de capturas de Elite mediante
    Steam/Proton.
-   la galería también se actualiza después de eliminar archivos
    externamente.
-   visibilidad mejorada de las opciones para conversión automática y
    eliminación.

### Servicios online

-   la transferencia automática de Journals a EDSM se ha integrado aún
    más y es visible mediante el área de estado de la ventana principal.
-   estados para transferencia, espera, error y EDSM desactivado.
-   indicador de estado de Inara como preparación para una futura
    transferencia automática.

### Uso y estabilidad

-   el tipo y el tamaño de letra de la interfaz pueden seleccionarse en
    los ajustes y aplicarse a toda la interfaz después de reiniciar.
-   la página de ajustes es desplazable, de modo que todas las opciones
    sigan siendo accesibles incluso con ventanas pequeñas.
-   botón **«Salir»** visible en la barra lateral izquierda.
-   el bloqueo Single Instance evita iniciar accidentalmente una segunda
    instancia simultánea del programa.
-   vista general segura en miniatura del sistema sin renderizar
    directamente el widget Explorer ya visible.
-   diversas mejoras en la interfaz, procesamiento del Journal, base de
    datos y proceso de actualización.

## Estado del proyecto

CMDRHelper está en desarrollo. La interfaz de usuario, el modelo de
datos y la representación todavía pueden cambiar. Se prevén más tipos de
cuerpos, funciones Journal, funciones Explorer, fuentes de datos y
cálculos. Linux y Windows seguirán siendo probados.

CMDRHelper nació como una herramienta personal y se amplía
progresivamente hasta convertirse en un helper más completo para Elite
Dangerous.

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
