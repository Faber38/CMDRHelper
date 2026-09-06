"""Spanish content for contextual help."""


HELP_TOPICS = {'overview': ('Descripción general',
              '<h2>Descripción general</h2>\n'
              '<p>La descripción general es la página de inicio de CMDRHelper. Resume la '
              'información más importante sobre el comandante actualmente activo y muestra de un '
              'vistazo si el diario, la ubicación y los servicios en línea se reconocen '
              'correctamente.</p>\n'
              '\n'
              '<h3>Comandante y barco</h3>\n'
              '<p>Aquí se muestran el comandante reconocido en Elite Dangerous Journal y el barco '
              'actualmente en uso.</p>\n'
              '<p>CMDRHelper asigna datos personales al comandante respectivo en función del ID de '
              'Frontier (FID). Esto mantiene los datos de diferentes comandantes separados unos de '
              'otros.</p>\n'
              '<p>Al cambiar de comandante, se carga la información guardada asociada al nuevo '
              'comandante.</p>\n'
              '\n'
              '<h3>diario</h3>\n'
              '<p>CMDRHelper utiliza los archivos de diario de Elite Dangerous como su principal '
              'fuente de datos.</p>\n'
              '<p>La pantalla del diario informa si se han encontrado archivos del diario y se han '
              'asignado al comandante activo. Las nuevas entradas completas del diario se procesan '
              'automáticamente durante el juego.</p>\n'
              '<p>Las áreas del diario que ya se han procesado se guardan para que CMDRHelper no '
              'tenga que volver a evaluar completamente cada diario la próxima vez que se '
              'inicie.</p>\n'
              '\n'
              '<h3>Ubicación actual</h3>\n'
              '<p>Muestra el sistema estelar conocido actualmente y, según lo que se sabe por el '
              'diario, la ubicación exacta del comandante.</p>\n'
              '<p>La ubicación se actualiza mediante eventos como saltos, atraques y otros '
              'informes de posición y se almacena comandante por comando.</p>\n'
              '\n'
              '<h3>Misiones</h3>\n'
              '<p>Esta área muestra el número de misiones abiertas actualmente conocidas.</p>\n'
              '<p>El botón o elemento del menú "Misiones" lo lleva a la vista completa de la '
              'misión con los objetivos conocidos de la misión y la información de estado.</p>\n'
              '\n'
              '<h3>Última resistencia</h3>\n'
              '<p>“Último estado” resume el último estado comandante persistente conocido. Esto '
              'permite restaurar información importante incluso después de reiniciar Elite '
              'Dangerous o CMDRHelper.</p>\n'
              '\n'
              '<h3>Sistemas finales</h3>\n'
              '<p>Aquí se muestran los sistemas visitados o reconocidos recientemente en la '
              'revista.</p>\n'
              '<p>La lista sirve como una descripción general rápida del reciente viaje del '
              'Comandante.</p>\n'
              '\n'
              '<h3>Estado en línea</h3>\n'
              '<p>Hay indicadores de estado adicionales en la parte superior de la ventana '
              'principal:</p>\n'
              '<ul>\n'
              '<li><b>Revista reconocida</b>– CMDRHelper detectó una fuente de diario válida y una '
              'identidad de comandante.</li>\n'
              '<li><b>EDSM</b>– muestra el estado actual de la transmisión EDSM para el diario '
              'activo FID.</li>\n'
              '<li><b>INARA</b>– muestra el estado actual de la transmisión Inara para el diario '
              'activo FID.</li>\n'
              '</ul>\n'
              '<p>Los datos de acceso en línea se gestionan por separado para cada comandante. Un '
              'comandante nunca usa automáticamente el API-Key de otro comandante.</p>\n'
              '\n'
              '<h3>Importante para varios comandantes</h3>\n'
              '<p>Los datos en vivo siempre dependen del comandante que fue claramente '
              'identificado por la sesión actual del diario Elite Dangerous.</p>\n'
              '<p>Simplemente mostrar un comandante diferente en una vista no cambia el comandante '
              'en vivo activo ni afecta ninguna transmisión EDSM o Inara.</p>\n'
              '\n'
              '<h3>Consejo</h3>\n'
              '<p>Si el comandante, el barco o la ubicación no coinciden con el estado actual del '
              'juego, primero revisa la pantalla del diario en la parte superior y luego revisa la '
              'carpeta del diario configurada en "Configuración".</p>'),
 'missions': ('Misiones',
              '<h2>Misiones</h2>\n'
              '<p>La vista de misión muestra las misiones del comandante visto actualmente '
              'conocidas por Elite Dangerous Journal. CMDRHelper guarda los datos de la misión '
              'comandante por comando para que las misiones abiertas se conserven incluso después '
              'de reiniciar Elite Dangerous o CMDRHelper.</p>\n'
              '\n'
              '<h3>Misiones abiertas</h3>\n'
              '<p>Nuevas misiones estan saliendo<code>MissionAccepted</code>asumido y guardado '
              'permanentemente.</p>\n'
              '<p>Mientras no haya un evento de misión final, la misión permanecerá abierta. Es '
              'posible que una nueva sesión de juego sin una lista de misiones no elimine '
              'automáticamente las misiones abiertas conocidas.</p>\n'
              '\n'
              '<h3>Estado de la misión</h3>\n'
              '<p>CMDRHelper procesa, entre otros, los siguientes cambios de estado:</p>\n'
              '<ul>\n'
              '<li>Misión aceptada</li>\n'
              '<li>Misión completada</li>\n'
              '<li>Misión fallida</li>\n'
              '<li>Misión abortada</li>\n'
              '<li>Objetivo de la misión desviado</li>\n'
              '<li>Progreso en misiones de carga/depósito apoyadas</li>\n'
              '</ul>\n'
              '<p>Un evento final sólo cambia la misión asociada.</p>\n'
              '\n'
              '<h3>Misiones del Diario</h3>\n'
              '<p>Elite Dangerous proporciona información de la misión sobre varios eventos del '
              'diario. CMDRHelper fusiona estos eventos en un estado de misión persistente.</p>\n'
              '<p>Un evento real de misión completa puede servir como una instantánea autorizada. '
              'Si falta un evento de este tipo, las misiones abiertas más antiguas no se cerrarán '
              'solo por este motivo.</p>\n'
              '\n'
              '<h3>Destinos y lugares</h3>\n'
              '<p>En la medida que Elite proporciona la información en el diario, CMDRHelper '
              'muestra:</p>\n'
              '<ul>\n'
              '<li>Sistema de destino</li>\n'
              '<li>Estación de destino o destino</li>\n'
              '<li>Planeta o cuerpo objetivo</li>\n'
              '<li>Designación de la misión</li>\n'
              '<li>progreso conocido</li>\n'
              '<li>estado actual</li>\n'
              '</ul>\n'
              '<p>No todas las misiones proporcionan toda la información. Los datos faltantes no '
              'los inventa CMDRHelper.</p>\n'
              '\n'
              '<h3>Persistencia y reinicio</h3>\n'
              '<p>Las misiones abiertas se guardan en la base de datos relacionada con el '
              'comandante.</p>\n'
              '<p>Esto significa que se retienen incluso si:</p>\n'
              '<ul>\n'
              '<li>Elite Dangerous finaliza y se reinicia más tarde</li>\n'
              '<li>CMDRHelper está cerrado en el medio</li>\n'
              '<li>La nueva sesión del diario inicialmente no contiene ningún evento de '
              'misión.</li>\n'
              '</ul>\n'
              '<p>Sólo un evento de misión documentado cambia el estado guardado.</p>\n'
              '\n'
              '<h3>Varios comandantes</h3>\n'
              '<p>Las misiones están estrictamente separadas por comandante.</p>\n'
              '<p>Un evento de misión sólo se asigna al comandante cuya sesión de diario se ha '
              'identificado de forma única. Las misiones de otro comandante no se pueden mostrar '
              'ni modificar.</p>\n'
              '\n'
              '<h3>Misiones huérfanas o que ya no son válidas</h3>\n'
              '<p>Si los datos del diario más antiguos o una importación anterior mantienen '
              'abierta una misión aunque ya no exista en el juego, se puede utilizar la función de '
              'limpieza/restablecimiento de misiones huérfanas existentes.</p>\n'
              '<p>Esta función solo debe usarse si está claro que la misión mostrada ya no está '
              'activa.</p>\n'
              '\n'
              '<h3>Servicios en línea</h3>\n'
              '<p>Los eventos de misión admitidos también se pueden transmitir a Inara si se '
              'configura un acceso Inara válido y activado para el diario activo FID.</p>\n'
              '<p>Una conexión Inara faltante o inalcanzable no afecta el almacenamiento de la '
              'misión local.</p>\n'
              '\n'
              '<h3>Consejo</h3>\n'
              '<p>Si una misión no aparece o muestra un estado incorrecto, primero verifique si '
              'Elite Dangerous ya ha escrito el evento de misión correspondiente en el '
              'diario.</p>\n'
              '<p>CMDRHelper solo puede mostrar información que el diario realmente proporciona o '
              'que ya ha sido almacenada de eventos de misiones únicos anteriores.</p>'),
 'explorer': ('Explorador',
              '<h2>Explorador</h2>\n'
              '<p>El Explorer evalúa los sistemas y cuerpos celestes descubiertos y escaneados por '
              'el comandante activo. Combina sus propios datos del diario Elite Dangerous con '
              'información adicional ya disponible y muestra datos de exploración, cartografía, '
              'señales biológicas/geológicas y datos de minería a cielo abierto juntos.</p>\n'
              '\n'
              '<h3>Sistema actual</h3>\n'
              '<p>El nivel actual de conocimiento sobre el sistema se resume en el área '
              'superior.</p>\n'
              '<p>Estos incluyen, entre otros:</p>\n'
              '<ul>\n'
              '<li>cuerpos bien conocidos e incluso registrados en la revista</li>\n'
              '<li>señales existentes</li>\n'
              '<li>Valores de escaneo</li>\n'
              '<li>valor cartográfico ya alcanzado</li>\n'
              '<li>valor total posible si está completamente mapeado</li>\n'
              '<li>Estado de BIO y valores de BIO estimados</li>\n'
              '<li>Cartografía y datos BIO que aún no han sido enviados</li>\n'
              '</ul>\n'
              '<p>Los valores mostrados se basan en los datos realmente disponibles. La '
              'información faltante no se presenta como un descubrimiento separado.</p>\n'
              '\n'
              '<h3>Mapa del sistema</h3>\n'
              '<p>El mapa del sistema representa gráficamente estrellas, planetas, lunas y otros '
              'cuerpos conocidos en el sistema actual.</p>\n'
              '<p>Se puede hacer clic en un cuerpo para abrir su vista detallada.</p>\n'
              '<p>La pantalla muestra, entre otras cosas, el tipo de cuerpo, la distancia y, si '
              'están disponibles, los valores de escaneo y cartografía, así como propiedades '
              'especiales de exploración.</p>\n'
              '\n'
              '<h3>ORGÁNICO ×N</h3>\n'
              '<p>BIO ×N denota el número de señales biológicas de un cuerpo reportadas por el '
              'juego.</p>\n'
              '<p>Inicialmente, el número sólo indica cuántas señales biológicas o géneros se '
              'informaron. No significa automáticamente que ya se hayan encontrado o analizado '
              'todas las especies biológicas.</p>\n'
              '<p>Los descubrimientos orgánicos propios y reales se mantienen por separado.</p>\n'
              '\n'
              '<h3>GEO×N</h3>\n'
              '<p>GEO ×N muestra la cantidad de señales geológicas de un cuerpo reportadas por el '
              'juego.</p>\n'
              '<p>Estos pueden incluir, por ejemplo, características geológicas como fumarolas o '
              'géiseres. CMDRHelper solo muestra la información que aparece en los datos del '
              'diario/cuerpo existentes.</p>\n'
              '\n'
              '<h3>ABBAU ×N</h3>\n'
              '<p>ABBAU ×N muestra el número de sitios mineros planetarios de un cuerpo informado '
              'por Elite Dangerous.</p>\n'
              '<p>Ejemplo:</p>\n'
              '<p><b>ABBAU ×24</b></p>\n'
              '<p>significa que para este organismo se han reportado 24 sitios mineros '
              'planetarios.</p>\n'
              '<p>El número no dice qué materia prima se puede extraer en un solo lugar.</p>\n'
              '\n'
              '<h3>Hallazgos mineros propios</h3>\n'
              '<p>Si el comandante realmente realizó minería a cielo abierto con el Rhino, el '
              'CMDRHelper almacena los hallazgos personales documentados por separado.</p>\n'
              '<p>Se hace una distinción entre:</p>\n'
              '<ul>\n'
              '<li>productos realmente obtenidos, p.e. B. Cobre en toneladas</li>\n'
              '<li>Materiales secundarios recolectados durante la minería.</li>\n'
              '<li>Materiales generales de la superficie del cuerpo.</li>\n'
              '</ul>\n'
              '<p>Un ejemplo de hallazgo personal sería:</p>\n'
              '<p><b>Cobre – 56 toneladas</b></p>\n'
              '<p>Esta información significa que este comandante realmente extrajo allí 56 '
              'toneladas de cobre.</p>\n'
              '<p>Los hallazgos mineros personales se guardan para cada comandante y no se mezclan '
              'con los hallazgos de otros comandantes.</p>\n'
              '\n'
              '<h3>Materiales de la superficie del cuerpo</h3>\n'
              '<p><code>Scan.Materials</code>Describe la composición general del material de la '
              'superficie de un cuerpo.</p>\n'
              '<p>Por ejemplo, el hierro, el níquel, el azufre u otros materiales se pueden '
              'mostrar con valores porcentuales.</p>\n'
              '<p>Estos valores no deben confundirse con las materias primas de un depósito minero '
              'planetario. Frontier no proporciona ninguna asociación directa documentada entre '
              'estos materiales generales del cuerpo y el contenido de un sitio minero individual '
              'en el Diario.</p>\n'
              '\n'
              '<h3>Terraformación</h3>\n'
              '<p>El símbolo o etiqueta de terraformación muestra que un cuerpo se considera '
              'candidato a terraformación según los datos disponibles.</p>\n'
              '\n'
              '<h3>Primer descubrimiento</h3>\n'
              '<p>El primer indicador de descubrimiento identifica los cuerpos para los cuales, '
              'según los datos disponibles, es posible un primer descubrimiento o ha sido '
              'documentado en consecuencia en la propia revista del organismo.</p>\n'
              '<p>La calificación final se basa en las condiciones reportadas por Elite Dangerous '
              'o los datos disponibles.</p>\n'
              '\n'
              '<h3>Primer mapeo</h3>\n'
              '<p>CMDRHelper distingue entre:</p>\n'
              '<ul>\n'
              '<li>El primer mapeo puede estar disponible</li>\n'
              '<li>mapeado por el comandante</li>\n'
              '<li>Primer mapeo reclamado por el comandante</li>\n'
              '</ul>\n'
              '<p>Esto hace posible ver si un cuerpo ya ha sido mapeado y si su comandante reclama '
              'el estado de primer mapeo.</p>\n'
              '\n'
              '<h3>bar campestre</h3>\n'
              '<p>El indicador de aterrizabilidad identifica los cuerpos en los que, según datos '
              'conocidos, es posible aterrizar.</p>\n'
              '\n'
              '<h3>Marcos dorados / cuerpos valiosos</h3>\n'
              '<p>En la pantalla del explorador se pueden destacar cuerpos especialmente '
              'valiosos.</p>\n'
              '<p>El marco dorado sirve como orientación visual rápida para cuerpos por encima del '
              'umbral de valor proporcionado en CMDRHelper.</p>\n'
              '<p>No reemplaza la visualización detallada del valor del cuerpo.</p>\n'
              '\n'
              '<h3>Lista de valores</h3>\n'
              '<p>La Lista de valores proporciona una vista más compacta de los cuerpos conocidos '
              'y sus valores de exploración/cartografía.</p>\n'
              '<p>Es particularmente adecuado para comparar rápidamente cuerpos interesantes o '
              'valiosos en un sistema.</p>\n'
              '\n'
              '<h3>ORGÁNICO / GEO / DEGRADACIÓN</h3>\n'
              '<p>Esta visión agrupa cuerpos con señales de degradación biológica, geológica o '
              'planetaria.</p>\n'
              '<p>Esto significa que no es necesario buscar cuerpos interesantes individualmente '
              'en el mapa completo del sistema.</p>\n'
              '<p>Si tiene sus propios datos de minería a cielo abierto, sus hallazgos mineros '
              'personales también pueden ser visibles.</p>\n'
              '\n'
              '<h3>Detalle del cuerpo</h3>\n'
              '<p>Al hacer clic en un cuerpo se abre la vista detallada.</p>\n'
              '<p>Hasta donde se sabe, allí puede aparecer lo siguiente:</p>\n'
              '<ul>\n'
              '<li>Tipo de cuerpo</li>\n'
              '<li>masa</li>\n'
              '<li>distancia</li>\n'
              '<li>Gravedad</li>\n'
              '<li>atmósfera</li>\n'
              '<li>Landabilidad</li>\n'
              '<li>Estado de terraformación</li>\n'
              '<li>Señales BIO/GEO</li>\n'
              '<li>sitios mineros planetarios</li>\n'
              '<li>Materiales de superficie</li>\n'
              '<li>propios hallazgos mineros</li>\n'
              '<li>Valor de escaneo</li>\n'
              '<li>valor cartográfico</li>\n'
              '<li>valor actual</li>\n'
              '</ul>\n'
              '<p>No todo el mundo tiene toda la información.</p>\n'
              '\n'
              '<h3>Previsiones BIO</h3>\n'
              '<p>CMDRHelper puede estimar posibles descubrimientos biológicos basándose en los '
              'datos existentes sobre cuerpos adecuados.</p>\n'
              '<p>Las predicciones no son garantía de que una especie en particular esté realmente '
              'presente. Sirven como ayuda para la toma de decisiones en materia de '
              'exploración.</p>\n'
              '<p>Los valores BIO estimados también son predicciones y se tratan por separado de '
              'los hallazgos reales confirmados.</p>\n'
              '\n'
              '<h3>Aún no enviado</h3>\n'
              '<p>CMDRHelper mantiene cartografía conocida relacionada con el comandante y datos '
              'BIO que aún no se han enviado.</p>\n'
              '<p>Las ventas de cartografía y las regalías biológicas se contabilizan utilizando '
              'los eventos de revista correspondientes.</p>\n'
              '<p>Los datos cartográficos que ya se han vendido no deberían volver a aparecer '
              'abiertos después de la reconstrucción.</p>\n'
              '\n'
              '<h3>mostrar auto</h3>\n'
              '<p>Las sugerencias de Explorer compatibles, como Valuable Bodies o BIO Finds, se '
              'pueden mostrar automáticamente usando los interruptores en la barra lateral '
              'izquierda.</p>\n'
              '<p>Estas pequeñas ventanas en vivo sirven como sugerencias adicionales mientras '
              'juegas y no reemplazan la vista completa del Explorador.</p>\n'
              '<p>«Cargo» muestra el contenido confirmado del Ship o SRV determinado por la Journal-FID activa. El Cargo del SRV nunca se adopta como Cargo del Ship; los Limpets cuentan para la ocupación total y se muestran por separado en la tabla Nombre | Cantidad.</p>\n'
              '\n'
              '<h3>Varios comandantes</h3>\n'
              '<p>Los resultados personales de exploración, cartografía, hallazgos BIO y propios '
              'hallazgos de minería a cielo abierto se asignan al comandante respectivo.</p>\n'
              '<p>Las propiedades astronómicas globales de un cuerpo (por ejemplo, el número de '
              'yacimientos mineros planetarios conocidos) siguen siendo propiedades del propio '
              'cuerpo.</p>\n'
              '\n'
              '<h3>Consejo</h3>\n'
              '<p>Si tienes un cuerpo interesante, vale la pena hacer clic en la vista detallada. '
              'Este es el mejor lugar para diferenciar entre datos corporales generales, posibles '
              'resultados de exploración y hallazgos reales documentados por su propio '
              'comandante.</p>'
              """

<h3>★ Favoritos</h3>
<p>El botón «★ Favoritos» en la parte superior del Explorer abre una ventana de favoritos independiente y reutilizable. En ella guardas sistemas, planetas/lunas y lugares en la superficie para el comandante activo.</p>
<p>La lista desplazable, ordenada alfabéticamente por nombre, muestra el nombre, tipo, sistema, cuerpo y latitud/longitud cuando corresponda, categoría y una pequeña vista previa de imagen. La búsqueda de texto libre y los filtros de tipo y categoría se pueden combinar. La búsqueda abarca nombre, sistema, cuerpo y nota.</p>
<p>«Abrir / Mostrar» muestra los datos guardados, la nota y una vista previa de imagen más grande. «Mostrar en Explorer» abre la vista general del sistema o los detalles del cuerpo existentes si el favorito pertenece al sistema actual del Explorer y hay datos correspondientes disponibles. Para otros sistemas siguen visibles los datos guardados del favorito; no se calcula ninguna ruta entre sistemas.</p>

<h3>Guardar un sistema, planeta o la ubicación actual</h3>
<ul>
<li>«★ Guardar sistema actual» guarda el sistema actual sin coordenadas de superficie.</li>
<li>«★ Guardar planeta / luna» permite seleccionar un planeta o una luna conocidos del sistema actual. Este favorito tampoco recibe coordenadas de superficie.</li>
<li>«★ Guardar ubicación actual» está en la parte superior de la ventana de favoritos, junto a las otras dos opciones de guardado, y también está disponible en el navegador planetario. En la ventana de favoritos, el botón permanece siempre visible y se desactiva si no hay datos actuales válidos de posición planetaria y un comandante activo. Al pulsarlo se fijan comandante, sistema, cuerpo, latitud y longitud. Los movimientos posteriores en el juego no cambian estos valores en el diálogo abierto.</li>
</ul>
<p>Introduce un nombre de tu elección y selecciona exactamente una categoría: Bio, Geo, Minería, Vista, Lugar de aterrizaje, Interesante u Otros. La nota y la imagen son opcionales. Los identificadores técnicos conocidos se incorporan internamente; no tienes que introducirlos. La latitud o longitud 0,0 también son coordenadas válidas.</p>
<p>«Editar» cambia nombre, categoría, nota e imagen. Se conservan sistema, cuerpo y coordenadas guardadas. Para guardar otro lugar en la superficie, crea un nuevo favorito en esa posición.</p>

<h3>Imágenes de favoritos</h3>
<p>Las imágenes de favoritos están separadas del apartado Imágenes. «Elegir imagen …» admite PNG, JPEG y WebP. Solo al guardar, CMDRHelper copia la imagen seleccionada a su propia carpeta de imágenes de favoritos. El archivo original no se mueve ni se modifica.</p>
<p>«Usar última captura» vuelve a leer en cada clic la carpeta de origen de capturas configurada y busca capturas legibles con nombres de archivo típicos de Elite. Sin una configuración, se tienen en cuenta las carpetas habituales de capturas Elite en Windows o Steam/Proton. También se busca en la carpeta del comandante activo dentro del destino de conversión configurado para encontrar las capturas Elite convertidas correspondientes. Así puede encontrarse una captura convertida aunque se haya eliminado su BMP original. Para determinar la captura más reciente cuenta una fecha y hora inequívoca en el nombre de archivo o, en su defecto, la fecha del archivo; en las imágenes convertidas cuenta la hora de captura guardada en el nombre y no la hora de conversión. CMDRHelper no realiza capturas por sí mismo ni busca en carpetas de imágenes arbitrarias.</p>
<p>Antes de usarla se muestran el nombre del archivo, la fecha y hora de captura y una vista previa recién cargada. Confirma con «Usar esta imagen». Si no se encuentra una captura adecuada, puedes seguir usando «Elegir imagen …». Las capturas BMP de Elite se guardan como una copia PNG interna.</p>
<p>Puedes sustituir una imagen en el diálogo de edición o deseleccionarla con «Quitar imagen». Al guardar se elimina la copia interna que ya no se utiliza. Si falta un archivo de imagen, el favorito sigue siendo utilizable sin vista previa.</p>

<h3>Destino del favorito y comandante</h3>
<p>Para los lugares en la superficie, «▶ Ir al destino» pasa el cuerpo, latitud, longitud y nombre del favorito guardados al navegador planetario existente. El nuevo destino sustituye al anterior. Los favoritos no tienen lógica de navegación propia. El navegador sigue decidiendo por sí mismo: los datos planetarios válidos y correspondientes activan la navegación; de lo contrario, espera esos datos.</p>
<p>Los favoritos pertenecen exclusivamente al comandante activo. Al cambiar de comandante se actualiza la lista y se descarta cualquier diálogo de edición abierto. Un destino que aún se gestione como destino favorito del comandante anterior se termina. La selección de comandantes de la crónica no amplía esta lista de favoritos.</p>
<p>«Eliminar» exige confirmación y elimina únicamente el registro del favorito y su copia interna de imagen. Se conservan la captura original o la imagen original seleccionada y todos los datos del Explorer, del diario y de los cuerpos.</p>"""),
 'chronicle': (
        'Crónica',
        """<h2>Crónica</h2>
<p>La crónica es la historia personal de viajes y descubrimientos del comandante. Utiliza la información del diario almacenada permanentemente para encontrar sistemas que ya han sido visitados, representarlos espacialmente y buscar descubrimientos conocidos.</p>

<h3>Sistemas visitados</h3>
<p>La Crónica muestra los sistemas visitados y sus ubicaciones en la galaxia conocida por el Comandante.</p>
<p>Si están disponibles, se tienen en cuenta la primera y la última visita, así como la información corporal conocida.</p>
<p>Con un período activo, el número de visitas, la primera visita y la última visita en la vista del mapa se refieren a las visitas reales a sistemas seleccionadas por el filtro.</p>
<p>Por lo tanto, la crónica no es sólo un mapa, sino también una herramienta para encontrar destinos de viajes y descubrimientos anteriores.</p>

<h3>mapa 3D</h3>
<p>Los sistemas visitados están representados espacialmente utilizando sus coordenadas galácticas X/Y/Z.</p>
<p>Las instrucciones de funcionamiento se encuentran directamente encima del mapa:</p>
<ul>
<li>Mantenga presionado el botón izquierdo del mouse → rotar vista</li>
<li>mantén pulsado el botón central del ratón y arrastra → dibuja una ventana de zoom</li>
<li>Mantenga presionado el botón derecho del mouse → mover vista</li>
</ul>
<p>La pantalla de eje pequeño ayuda a orientarse en el espacio.</p>

<h3>Posición actual</h3>
<p>Con "Posición actual", la vista del mapa se puede alinear o regresar a la ubicación actualmente conocida del comandante activo.</p>
<p>Primero se aplican los filtros actuales. La vista solo se centra en el sistema actual si está incluido en el mapa resultante.</p>
<p>De lo contrario, aparece «El sistema actual no está incluido en esta selección de filtros.» Esto no elimina los filtros.</p>

<h3>Alinear</h3>
<p>«Alinear» restablece la orientación a una vista superior del plano galáctico. El desplazamiento y el zoom se conservan.</p>
<p>Esto resulta útil si muchas rotaciones han hecho que el mapa sea difícil de interpretar.</p>

<h3>Actualizar Crónica</h3>
<p>«Actualizar Crónica» vuelve a cargar los datos de la crónica con los filtros combinados actuales y actualiza la vista. El texto libre, los límites de fecha activados y los filtros mineros se vuelven a evaluar juntos; los filtros activos no se ignoran.</p>
<p>La función no cambia archivos de diario ni crea nuevos datos de exploración. Simplemente actualiza la visualización del historial en función de los datos existentes del CMDRHelper.</p>

<h3>Búsqueda de texto libre</h3>
<p>El contenido ya conocido se puede buscar utilizando el campo "Historial de búsqueda...".</p>
<p>La búsqueda tiene en cuenta, si está disponible en la base de datos, entre otras cosas:</p>
<ul>
<li>Nombres del sistema</li>
<li>Características del cuerpo</li>
<li>datos biológicos</li>
<li>Materiales</li>
<li>datos del códice</li>
</ul>
<p>El texto libre, el período y la minería comparten una misma zona de filtros. «Aplicar» evalúa juntos los filtros establecidos. Intro en el campo de texto libre inicia el mismo filtrado combinado que «Aplicar».</p>

<h3>Período Desde/Hasta (UTC)</h3>
<p>Activa «Desde» y «Hasta» mediante sus respectivas casillas y elige la fecha deseada. También puedes usar un solo límite. Sin la casilla activada no hay restricción temporal por ese lado; si ninguna de las dos está activada, no se limita el período.</p>
<ul>
<li><b>Desde:</b> Desde el comienzo del día natural UTC seleccionado, inclusive.</li>
<li><b>Hasta:</b> Se incluye todo el día natural UTC seleccionado, hasta el instante anterior al comienzo del día siguiente.</li>
</ul>
<p>UTC es el tiempo universal coordinado. Los límites de fecha se refieren a días naturales UTC, no a los días de tu zona horaria local.</p>
<p>Se filtran las visitas reales a sistemas de <code>system_visits</code>. Se requiere una visita real del comandante correspondiente dentro del período. Los valores almacenados <code>first_seen</code> y <code>last_seen</code> no sustituyen una visita real: no basta con que el período esté entre una primera visita anterior y una última visita posterior.</p>
<p>El período filtra visitas, no eventos individuales de descubrimiento, BIO, GEO o minería. La información de hallazgos conocidos y las cantidades extraídas siguen siendo totales almacenados. Desde/Hasta se pueden usar solos o junto con texto libre y minería.</p>
<p>Si Desde es posterior a Hasta, aparece «La fecha Desde no puede ser posterior a la fecha Hasta.» No se inicia ninguna consulta a la base de datos. Corrige los límites de fecha y vuelve a aplicar los filtros.</p>

<h3>Resultados de la búsqueda</h3>
<p>Los aciertos se muestran en la lista de resultados existente debajo de la tarjeta de crónica.</p>
<p>Dependiendo del tipo de golpe, puede aparecer sistema y cuerpo, así como información adicional.</p>
<p>Se puede utilizar un hit para encontrar el sistema u organismo correspondiente que ya se conoce y abrir la información detallada existente.</p>

<h3>Sin resultados</h3>
<p>Si un filtrado válido no encuentra coincidencias, se vacían el mapa y las rutas. La lista de resultados se vacía y se oculta, la vista de detalles se restablece y se cierra cualquier ventana abierta de detalles de un sistema de la crónica.</p>
<p>Los resultados antiguos no permanecen visibles. En ese caso, comprueba la combinación de texto de búsqueda, período y filtros mineros, así como el comandante utilizado para la vista correspondiente.</p>

<h3>Yacimientos mineros planetarios</h3>
<p>El filtro "Sitios de minería planetaria" se puede utilizar para buscar específicamente cuerpos conocidos para los cuales Elite Dangerous ha informado sitios de minería planetaria.</p>
<p>La visualización subyacente corresponde a la conocida del Explorer:</p>
<p><b>ABBAU ×N</b></p>
<p>El número pertenece al propio cuerpo y no está relacionado con el comandante.</p>

<h3>Al menos</h3>
<p>Usando “Al menos” puedes especificar el número mínimo de ubicaciones de minería planetaria que debe tener un cuerpo.</p>
<p>Ejemplo:</p>
<p><b>Al menos 20</b></p>
<p>sólo muestra cuerpos conocidos con al menos:</p>
<p><b>ABBAU ×20</b></p>
<p>De este modo es posible localizar zonas mineras especialmente extensas.</p>

<h3>Mis hallazgos mineros</h3>
<p>En el caso de los “hallazgos mineros propios”, la búsqueda se limita a los cadáveres en los que se demuestra que el comandante en cuestión realizó él mismo actividades de minería a cielo abierto.</p>
<p>Esta información proviene de su historial personal de minería a cielo abierto y está estrictamente separada por comandante.</p>
<p>Por lo tanto, un cuerpo puede tener señales globales ABBAU ×N sin que su propio comandante haya eliminado nada allí.</p>

<h3>Mercancía</h3>
<p>Si está activado “Hallazgos mineros propios”, también está disponible la selección “Materia prima”.</p>
<p>La lista sólo contiene productos que el comandante en cuestión ya ha obtenido de la minería a cielo abierto.</p>
<p>Esta no es una lista teórica de todas las posibles materias primas mineras.</p>
<p>Para FABER38, la lista puede incluir, por ejemplo:</p>
<ul>
<li>Todo</li>
<li>cobre</li>
</ul>
<p>Si más adelante se extraen materias primas adicionales, aparecerán automáticamente en su selección personal.</p>

<h3>Búsqueda dirigida de materias primas.</h3>
<p>Por ejemplo, si se selecciona "Cobre" y luego se presiona "Aplicar", el historial solo mostrará cuerpos en los que el comandante en cuestión haya extraído cobre de manera demostrable.</p>
<p>Ejemplo:</p>
<p><b>Prua Hypai NV-E c28-66 / 2 — ABBAU ×24 — cobre 56 toneladas</b></p>
<p>Esto significa que la crónica se puede utilizar como base de datos de localización personal: una materia prima ya extraída se puede volver a encontrar más tarde.</p>

<h3>Todas las materias primas</h3>
<p>En “Materia prima: Todo” se tienen en cuenta todos los descubrimientos personales de minería a cielo abierto que coincidan.</p>
<p>Si en un cuerpo se conocen varias mercancías, se pueden mostrar junto con las cantidades obtenidas hasta el momento.</p>
<p>Ejemplo:</p>
<p><b>ABBAU ×24 — Helio-3 18 t, cobre 56 t</b></p>
<p>Las cantidades son los valores mineros personales del comandante respectivo, que en realidad están documentados a partir de los eventos del diario.</p>
<p>Incluso con un período activo, las cantidades personales extraídas siguen siendo cantidades totales almacenadas. <b>Cobre 56 t</b> no significa automáticamente <b>56 t en el período seleccionado</b>. El período exige una visita al sistema correspondiente, pero no limita la cantidad extraída que se muestra a ese período.</p>

<h3>Combinar filtros</h3>
<p>El texto libre, los límites Desde/Hasta activados y los filtros mineros se pueden combinar. Un resultado debe cumplir conjuntamente las condiciones establecidas.</p>
<p>Por ejemplo:</p>
<ul>
<li>Sitios mineros planetarios activos</li>
<li>Al menos 20</li>
<li>Hallazgos mineros propios activos</li>
<li>Materia prima cobre</li>
</ul>
<p>busca cuerpos conocidos con al menos 20 sitios mineros planetarios donde el comandante en cuestión ya ha extraído cobre.</p>
<p>También se tiene en cuenta cualquier texto de búsqueda adicional. Si además hay un período, el comandante consultado debe haber visitado realmente el sistema correspondiente durante ese período; la extracción del cobre no tiene por qué haber ocurrido en ese período.</p>

<h3>Aplicar</h3>
<p>«Aplicar» ejecuta un filtrado combinado con todos los filtros de búsqueda, período y minería establecidos actualmente:</p>
<ul>
<li>Texto libre</li>
<li>Desde, si está activado</li>
<li>Hasta, si está activado</li>
<li>Yacimientos mineros planetarios</li>
<li>Cantidad mínima</li>
<li>Mis hallazgos mineros</li>
<li>Mercancía, si «Mis hallazgos mineros» está activado</li>
</ul>
<p>Intro en el campo de texto libre ejecuta exactamente el mismo filtrado. Sin texto libre ni filtros mineros, se carga el mapa normal para los comandantes marcados en el mapa, limitado por Desde/Hasta si corresponde.</p>

<h3>Restablecer</h3>
<p>«Restablecer» devuelve la zona común de filtros a su estado inicial:</p>
<ul>
<li>Se borra el texto libre.</li>
<li>Desde y Hasta se desactivan; los campos de fecha vuelven a mostrar la fecha de hoy y quedan desactivados.</li>
<li>Yacimientos mineros planetarios se desactiva.</li>
<li>La cantidad mínima se establece en 0.</li>
<li>Mis hallazgos mineros se desactiva.</li>
<li>Mercancía vuelve a «Todos».</li>
</ul>
<p>Se conserva la selección de comandantes. Después se vuelve a cargar la crónica normal para esta selección del mapa; se restablecen los resultados de búsqueda anteriores y las vistas de detalles.</p>

<h3>Selección de comandante</h3>
<p>La crónica puede mostrar datos de varios comandantes conocidos.</p>
<p>Hay dos conceptos de selección diferentes:</p>
<ul>
<li><b>Selección de comandantes del mapa:</b> Las casillas de comandantes determinan qué rutas de comandantes se muestran en el mapa normal sin búsqueda de texto libre o minera. Se tiene en cuenta cualquier período activado.</li>
<li><b>Comandante consultado:</b> Las búsquedas personales de texto libre o mineras usan al comandante consultado (<code>viewed_commander_id</code>), o en su defecto al comandante activo. Las listas personales de mercancías también dependen de ese comandante.</li>
</ul>
<p>Sin embargo, la información personal, como sus propios hallazgos mineros y listas de materias primas, siempre se evalúan por separado para el comandante que realmente está viendo.</p>
<p>Un comandante no ve en su selección de materias primas ningún descubrimiento minero que pertenezca exclusivamente a otro comandante.</p>

<h3>Todos los comandantes</h3>
<p>La visualización del mapa/crónica puede tener en cuenta a varios comandantes.</p>
<p>«Todos los comandantes» se refiere a la selección de comandantes del mapa. Las casillas de comandantes no amplían automáticamente las búsquedas personales de texto libre o mineras a varios comandantes.</p>
<p>Esto no cambia la asignación personal de datos relacionados con el comandante. Las propiedades astronómicas globales de un sistema o cuerpo siguen siendo compartidas, los hallazgos personales permanecen separados.</p>

<h3>Ayuda de búsqueda/leyenda</h3>
<p>Se puede acceder a información adicional sobre la búsqueda de crónicas y el significado de la visualización a través de “Ayuda de búsqueda/leyenda”.</p>
<p>Al hacer clic en un término de búsqueda, se coloca en el campo de búsqueda y se ejecuta junto con los filtros de período y minería ya establecidos.</p>
<p>Esta ayuda principal contextual complementa las breves instrucciones de funcionamiento disponibles allí.</p>

<h3>Consejo</h3>
<p>La crónica es especialmente adecuada para encontrar lugares interesantes descubiertos durante un viaje más largo.</p>
<p>Para la minería a cielo abierto, por ejemplo, puede responder:</p>
<p>“¿En qué planeta he extraído cobre alguna vez?”</p>
<p>o:</p>
<p>"¿Cuáles de mis planetas conocidos tienen un número particularmente alto de sitios mineros?"</p>""",
    ),
 'jump_tip': ('punta de salto',
              '<h2>punta de salto</h2>\n'
              '<p>La punta de salto apoya la exploración al evaluar los datos del sistema ya '
              'conocidos y resaltar los sistemas de destino interesantes.</p>\n'
              '<p>La función pretende ser una ayuda para la toma de decisiones. No garantiza que '
              'un sistema recomendado contenga realmente hallazgos raros o particularmente '
              'valiosos.</p>\n'
              '\n'
              '<h3>Base de la evaluación</h3>\n'
              '<p>CMDRHelper utiliza información de diarios y bases de datos existentes para '
              'evaluar patrones conocidos en nombres y clases de sistemas.</p>\n'
              '<p>Se pueden tener en cuenta, entre otras cosas, abreviaturas de sistemas, tipos de '
              'cuerpos ya conocidos y hallazgos anteriores.</p>\n'
              '\n'
              '<h3>Abreviatura del sistema</h3>\n'
              '<p>Muchos sistemas generados por procedimientos en Elite Dangerous contienen '
              'combinaciones de letras y números que identifican grupos de sistemas '
              'específicos.</p>\n'
              '<p>CMDRHelper puede evaluar estadísticamente estas abreviaturas y mostrar en qué '
              'grupos se produjeron hallazgos interesantes con mayor frecuencia según los datos '
              'conocidos hasta la fecha.</p>\n'
              '\n'
              '<h3>Reevaluar</h3>\n'
              '<p>Con “Reevaluar” se vuelve a analizar la base de datos existente.</p>\n'
              '<p>Se utilizan los datos guardados del comandante. La función no crea nuevos datos '
              'de élite ni modifica archivos de diario.</p>\n'
              '\n'
              '<h3>Lista de resultados</h3>\n'
              '<p>La lista de resultados muestra las abreviaturas de sistemas o candidatos más '
              'interesantes según la evaluación actual.</p>\n'
              '<p>Dependiendo de la base de datos existente, puede haber información sobre:</p>\n'
              '<ul>\n'
              '<li>clases planetarias interesantes</li>\n'
              '<li>descubrimientos biológicos</li>\n'
              '<li>Mundos acuáticos</li>\n'
              '<li>cuerpos terraformables</li>\n'
              '<li>otros resultados de exploración notables</li>\n'
              '</ul>\n'
              '<p>aparecer.</p>\n'
              '\n'
              '<h3>Probabilidad en lugar de garantía</h3>\n'
              '<p>Un valor alto o una buena clasificación sólo significa que un determinado patrón '
              'se asoció más a menudo con hallazgos interesantes en los datos evaluados hasta '
              'ahora.</p>\n'
              '<p>No es una garantía.</p>\n'
              '<p>Un sistema recomendado puede seguir careciendo de interés, mientras que un '
              'sistema de baja calificación puede contener hallazgos valiosos.</p>\n'
              '\n'
              '<h3>Base de datos propia</h3>\n'
              '<p>La punta de salto funciona con los datos ya conocidos del comandante.</p>\n'
              '<p>Cuantos más sistemas y organismos se registren a lo largo del tiempo, mayor será '
              'la base de datos personal para la evaluación.</p>\n'
              '<p>Esto significa que la clasificación puede cambiar más adelante.</p>\n'
              '\n'
              '<h3>Varios comandantes</h3>\n'
              '<p>Las evaluaciones personales se manejan comandante por comando.</p>\n'
              '<p>Los datos de otro comandante no deben falsificar la calificación personal sin '
              'que nadie se dé cuenta.</p>\n'
              '<p>Por otro lado, los datos maestros astronómicos globales se pueden compartir '
              'siempre que no representen hallazgos personales relacionados con el '
              'comandante.</p>\n'
              '\n'
              '<h3>Uso en la práctica</h3>\n'
              '<p>La punta de salto es especialmente adecuada si hay varios destinos posibles para '
              'elegir y se desea ayuda adicional para la toma de decisiones.</p>\n'
              '<p>No reemplaza a un planificador de rutas completo y no calcula una ruta óptima y '
              'segura.</p>\n'
              '<p>El elemento de menú "Planificador de ruta" está disponible para la planificación '
              'de rutas específicas.</p>\n'
              '\n'
              '<h3>Consejo</h3>\n'
              '<p>Utilice la punta de salto como ayuda adicional para la exploración:</p>\n'
              '<p>“Según mis datos anteriores, ¿qué sistema parece más interesante?”</p>\n'
              '<p>No como una predicción:</p>\n'
              '<p>"Se garantiza que habrá un hallazgo específico en este sistema".</p>'),
 'route_planner': ('Planificador de ruta',
                   '<h2>Planificador de ruta</h2>\n'
                   '<p>El planificador de rutas permite planificar viajes más largos en barco o '
                   'Fleet Carrier. CMDRHelper puede utilizar datos de ruta externos de Spansh y '
                   'preparar la ruta planificada para su uso posterior.</p>\n'
                   '\n'
                   '<h3>Empezar y terminar</h3>\n'
                   '<p>Para el cálculo de la ruta se requiere un sistema de inicio y destino.</p>\n'
                   '<p>En la medida de lo posible, CMDRHelper puede utilizar el sistema conocido '
                   'actual del Commander como punto de partida. El inicio y el final deben '
                   'verificarse antes del cálculo.</p>\n'
                   '\n'
                   '<h3>Enviar o Fleet Carrier</h3>\n'
                   '<p>El planificador de rutas diferencia entre viajes con un barco normal y con '
                   'un Fleet Carrier.</p>\n'
                   '<p>Ambos utilizan diferentes requisitos y métodos de cálculo. Por lo tanto, se '
                   'debe seleccionar el tipo de ruta adecuado antes de planificar.</p>\n'
                   '\n'
                   '<h3>Ruta del barco</h3>\n'
                   '<p>Para una ruta de barco se tienen en cuenta las propiedades de salto '
                   'conocidas o introducidas para el barco activo.</p>\n'
                   '<p>Dependiendo de los datos disponibles, se pueden incorporar a la '
                   'planificación datos FSD, datos del barco, masa, combustible y otros parámetros '
                   'del salto.</p>\n'
                   '<p>Una ruta calculada es una ayuda para la planificación. Los cambios en el '
                   'barco o su masa pueden cambiar la distancia de salto real que se puede '
                   'alcanzar en el juego.</p>\n'
                   '\n'
                   '<h3>Ruta del transportista de flota</h3>\n'
                   '<p>Los Fleet Carrier tienen reglas de salto diferentes a las de los barcos '
                   'normales.</p>\n'
                   '<p>CMDRHelper utiliza la planificación del transportista designado Spansh para '
                   'las rutas correspondientes.</p>\n'
                   '<p>La ruta se utiliza para planificar la secuencia de salto. El consumo real '
                   'de tritio y la autonomía disponible también pueden depender de la masa y del '
                   'estado actual del portador.</p>\n'
                   '\n'
                   '<h3>Spansh</h3>\n'
                   '<p>Para el cálculo de la ruta real, CMDRHelper puede utilizar el servicio '
                   'externo Spansh.</p>\n'
                   '<p>La solicitud se procesa en segundo plano para que la interfaz permanezca '
                   'operativa durante un cálculo más largo.</p>\n'
                   '<p>CMDRHelper no tiene influencia sobre la disponibilidad o tiempo de '
                   'respuesta del servicio externo.</p>\n'
                   '\n'
                   '<h3>cálculo</h3>\n'
                   '<p>Después de iniciar un cálculo, la solicitud se transmite al planificador de '
                   'ruta seleccionado.</p>\n'
                   '<p>Dependiendo de la ruta y servicio, el cálculo puede tardar algún tiempo. '
                   'Durante este tiempo no se debe iniciar innecesariamente ningún segundo cálculo '
                   'idéntico.</p>\n'
                   '\n'
                   '<h3>Resultado</h3>\n'
                   '<p>Una ruta calculada correctamente muestra los sistemas previstos o los '
                   'puntos de salto en su orden.</p>\n'
                   '<p>Dependiendo del tipo de ruta, aparece información adicional sobre la '
                   'distancia, los saltos, el combustible o el tritio y otros datos de ruta '
                   'disponibles.</p>\n'
                   '\n'
                   '<h3>Ruta y comandante actual.</h3>\n'
                   '<p>El sistema y el barco actuales se pueden utilizar, siempre que se conozcan '
                   'claramente en el AppState activo, para la asignación previa o para apoyar la '
                   'planificación.</p>\n'
                   '<p>Sin embargo, la ruta real sigue siendo un plan y no cambia ningún dato del '
                   'diario o del comandante.</p>\n'
                   '\n'
                   '<h3>Exportación CTSVision</h3>\n'
                   '<p>Las rutas calculadas de los transportistas de flotas se pueden exportar '
                   'como CSV para CTSVision.</p>\n'
                   '<p>Esto significa que una ruta de transporte planificada en CMDRHelper se '
                   'puede utilizar en CTSVision para el control de salto o el procesamiento de '
                   'rutas allí.</p>\n'
                   '<p>La exportación no cambia la ruta en CMDRHelper.</p>\n'
                   '\n'
                   '<h3>archivo CSV</h3>\n'
                   '<p>El archivo exportado contiene los datos de ruta necesarios para CTSVision '
                   'en el orden previsto.</p>\n'
                   '<p>El archivo no debe modificarse estructuralmente de forma incontrolada '
                   'después de la exportación si luego va a ser leído por CTSVision.</p>\n'
                   '\n'
                   '<h3>Errores y servicios externos.</h3>\n'
                   '<p>Si no se puede contactar con Spansh o el servicio devuelve un error, '
                   'CMDRHelper muestra el mensaje de error correspondiente.</p>\n'
                   '<p>Un error en el cálculo de ruta en línea no cambia los datos del diario o '
                   'del comandante local.</p>\n'
                   '\n'
                   '<h3>Planificador de ruta y consejo de salto</h3>\n'
                   '<p>El consejo de salto y el planificador de rutas cumplen diferentes '
                   'tareas:</p>\n'
                   '<ul>\n'
                   '<li>Jump tip evalúa posibles objetivos de exploración interesantes en función '
                   'de los datos existentes.</li>\n'
                   '<li>El planificador de rutas calcula una ruta específica entre el inicio y el '
                   'destino.</li>\n'
                   '</ul>\n'
                   '<p>Por lo tanto, un buen consejo de salto no forma parte automáticamente de '
                   'una ruta óptima.</p>\n'
                   '\n'
                   '<h3>Varios comandantes</h3>\n'
                   '<p>Si se utilizan datos relacionados con el comandante, como el sistema actual '
                   'o el barco, estos provienen del AppState activo en vivo y deben asignarse '
                   'claramente allí.</p>\n'
                   '<p>Simplemente mirar a otro comandante en la vista CMDR no cambia el '
                   'planificador de ruta a su sistema o barco.</p>\n'
                   '<p>El cálculo de una ruta en sí no cambia los datos personales de otro '
                   'comandante.</p>\n'
                   '\n'
                   '<h3>Consejo</h3>\n'
                   '<p>Antes de un viaje largo, compruebe siempre de nuevo:</p>\n'
                   '<ul>\n'
                   '<li>Sistema de arranque</li>\n'
                   '<li>Sistema de destino</li>\n'
                   '<li>Tipo de ruta barco/transportista</li>\n'
                   '<li>para rutas de barcos, el barco subyacente, FSD y parámetros de salto</li>\n'
                   '<li>para rutas de transporte, la reserva de tritio disponible</li>\n'
                   '</ul>\n'
                   '<p>En el caso de viajes con flotas, es aconsejable prever también reservas '
                   'suficientes para el viaje de vuelta o para desvíos no planificados.</p>'),
 'images': ('Fotos',
            '<h2>Fotos</h2>\n'
            '<p>La sección “Imágenes” gestiona las capturas de pantalla tomadas con Elite '
            'Dangerous. CMDRHelper puede reconocer automáticamente nuevas grabaciones, procesarlas '
            'y almacenarlas en una galería basada en el comandante.</p>\n'
            '\n'
            '<h3>Carpeta de origen</h3>\n'
            '<p>La carpeta de origen es la carpeta donde Elite Dangerous guarda sus capturas de '
            'pantalla en formato BMP.</p>\n'
            '<p>CMDRHelper puede monitorear esta carpeta en busca de nuevos archivos BMP. Para que '
            'funcione el procesamiento automático, se debe configurar la carpeta de captura de '
            'pantalla correcta.</p>\n'
            '\n'
            '<h3>Carpeta de destino</h3>\n'
            '<p>La carpeta de destino es la carpeta raíz común para las imágenes procesadas por '
            'CMDRHelper.</p>\n'
            '<p>El usuario configura esta carpeta raíz. CMDRHelper crea automáticamente las '
            'subcarpetas relacionadas con Commander requeridas durante el procesamiento.</p>\n'
            '\n'
            '<h3>Procesamiento automático</h3>\n'
            '<p>Si "Convertir automáticamente" está activado y se configuran carpetas de origen y '
            'destino válidas, CMDRHelper comprueba periódicamente la carpeta de origen en busca de '
            'nuevas capturas de pantalla BMP.</p>\n'
            '<p>Cuando se activa, los archivos BMP existentes se marcan inicialmente como '
            'conocidos y no se convierten automáticamente sin que se les solicite. Para ello está '
            'disponible la función separada para convertir BMP existentes.</p>\n'
            '<p>Un archivo nuevo no se pone en cola hasta que tenga el mismo tamaño distinto de '
            'cero en dos comprobaciones consecutivas. Como resultado, una operación de escritura '
            'que todavía está en curso no se procesa inmediatamente.</p>\n'
            '\n'
            '<h3>Conversión de imágenes</h3>\n'
            '<p>Como fuente, CMDRHelper procesa archivos BMP. Se puede seleccionar “PNG” o “JPG” '
            'como formato de destino.</p>\n'
            '<p>Los archivos JPG se guardan con un nivel de calidad 95. Los archivos PNG se '
            'guardan de forma optimizada.</p>\n'
            '<p>De forma predeterminada, se conserva el archivo BMP original. Si se activa '
            '"Eliminar BMP después de la conversión", el BMP de origen solo se eliminará después '
            'de que la imagen de destino se haya guardado correctamente.</p>\n'
            '\n'
            '<h3>Iluminar imagen</h3>\n'
            '<p>El brillo se ajusta del 0 al 50 por ciento mediante un control deslizante y un '
            'campo numérico vinculado. La configuración se guarda.</p>\n'
            '<p>Se aplica automáticamente durante cada conversión iniciada a partir de entonces, '
            'tanto para archivos BMP recién monitoreados como para archivos BMP existentes '
            'iniciados manualmente. el 0 por ciento recupera el brillo original; los valores más '
            'altos aumentan el brillo de la imagen PNG o JPG generada en consecuencia.</p>\n'
            '<p>La función no es una vista previa pura y no se aplica posteriormente a una imagen '
            'seleccionada en la galería. El brillo modificado se guarda en el nuevo archivo de '
            'destino.</p>\n'
            '<p>El BMP de origen permanece sin cambios a menos que también se active la '
            'eliminación del archivo BMP. Los datos del diario, el comandante y la exploración no '
            'se modifican.</p>\n'
            '\n'
            '<h3>Almacenamiento relacionado con Commander</h3>\n'
            '<p>Se asignan nuevas capturas de pantalla al comandante que juega según la identidad '
            'del diario presente en el AppState activo en vivo.</p>\n'
            '<p>La estructura de carpetas contiene el nombre del comandante y el ID de Frontier, '
            'por ejemplo:</p>\n'
            '<p><b>FABER38_F12520967/</b></p>\n'
            '<p>El FID mantiene la tarea clara incluso con varios comandantes. Esto permite '
            'distinguir dos comandantes con el mismo nombre.</p>\n'
            '\n'
            '<h3>nombres de archivos</h3>\n'
            '<p>Las nuevas imágenes procesadas reciben un nombre con la hora de captura, el nombre '
            'del comandante y, si está disponible, el sistema estelar conocido al hacer cola.</p>\n'
            '<p>Ejemplo:</p>\n'
            '<p><b>2026-09-04_13-18-22_FABER38_Prua-Hypai-RB-D-c29-71.png</b></p>\n'
            '<p>El FID está en el nombre de la carpeta relacionada con Commander, no nuevamente en '
            'el nombre del archivo de imagen.</p>\n'
            '\n'
            '<h3>Nombres de archivos seguros</h3>\n'
            '<p>CMDRHelper desinfecta los nombres del comandante y del sistema para usarlos como '
            'componentes de archivos y carpetas.</p>\n'
            '<p>Se reemplazan el control ilegal y los caracteres de Windows, se unifican los '
            'espacios en blanco, se eliminan los puntos problemáticos o los espacios finales y se '
            'protegen los nombres reservados de Windows como CON o NUL.</p>\n'
            '\n'
            '<h3>tiempo de grabación</h3>\n'
            '<p>Para nombrar, CMDRHelper utiliza la hora de modificación del archivo BMP estable '
            'reconocido. Sólo si no se puede leer se utilizará la hora actual.</p>\n'
            '<p>Esto significa que el nombre normalmente depende del archivo fuente y no del '
            'tiempo de conversión posterior.</p>\n'
            '\n'
            '<h3>Varias imágenes en el mismo segundo</h3>\n'
            '<p>Si el nombre de archivo deseado ya existe o está reservado para una conversión en '
            'curso, CMDRHelper lo agrega '
            'continuamente<code>_2</code>,<code>_3</code>,<code>_4</code>y así sucesivamente.</p>\n'
            '<p>Esto significa que otra captura de pantalla con la misma marca de tiempo no '
            'sobrescribirá una imagen de destino existente.</p>\n'
            '\n'
            '<h3>Cambio de comandante durante el procesamiento.</h3>\n'
            '<p>Commander, FID y el sistema se capturan juntos cuando se pone en cola una captura '
            'de pantalla.</p>\n'
            '<p>Un cambio posterior de comandante no cambia la asignación de esta imagen que ya '
            'está en espera. Esto significa que una captura de pantalla de FABER38 no se escribe '
            'posteriormente en la carpeta de otro comandante.</p>\n'
            '\n'
            '<h3>galería</h3>\n'
            '<p>La galería muestra archivos PNG, JPG y JPEG de los directorios asociados con el '
            'filtro seleccionado. Regularmente se detectan imágenes nuevas, eliminadas o '
            'movidas.</p>\n'
            '<p>El filtro de la galería no cambia la ubicación de almacenamiento ni la asignación '
            'del comandante de los archivos.</p>\n'
            '\n'
            '<h3>Comandante actual</h3>\n'
            '<p>El filtro Comandante actual muestra imágenes de la carpeta del comandante que se '
            've actualmente en la vista CMDR.</p>\n'
            '<p>El comandante en cuestión sólo determina la exhibición en la galería. Por otro '
            'lado, al asignar una nueva captura de pantalla en vivo se utiliza la identidad del '
            'diario activa al ponerse en cola.</p>\n'
            '\n'
            '<h3>Todos los comandantes</h3>\n'
            '<p>El filtro "Todos los comandantes" muestra las imágenes de las subcarpetas válidas '
            'de todos los comandantes conocidos juntos. También se tiene en cuenta la carpeta '
            'especial para grabaciones sin identidad reconocida.</p>\n'
            '<p>Los archivos no se mueven ni se fusionan.</p>\n'
            '\n'
            '<h3>No asignado</h3>\n'
            '<p>El filtro No asignado muestra archivos de imagen compatibles ubicados directamente '
            'en la carpeta raíz de destino compartida.</p>\n'
            '<p>En particular, las imágenes más antiguas sin subcarpetas relacionadas con '
            'Commander siguen siendo visibles. CMDRHelper no intenta adivinar su afiliación '
            'después del hecho.</p>\n'
            '\n'
            '<h3>Imágenes existentes</h3>\n'
            '<p>Las imágenes que ya existen en la carpeta raíz no se mueven ni se les cambia el '
            'nombre automáticamente.</p>\n'
            '<p>Permanecen accesibles a través de "No asignados" siempre que estén disponibles '
            'como PNG, JPG o JPEG.</p>\n'
            '\n'
            '<h3>Seleccionar y ver imagen</h3>\n'
            '<p>Un simple clic en una imagen de vista previa muestra la imagen escalada en el área '
            'de vista previa y muestra su nombre de archivo.</p>\n'
            '<p>Un doble clic abre el archivo con la aplicación del sistema operativo configurada '
            'para imágenes.</p>\n'
            '<p>Se pueden marcar varias imágenes al mismo tiempo. Cuando cambia el tamaño de la '
            'ventana, la vista previa de la imagen actual se reescala para ajustarse.</p>\n'
            '\n'
            '<h3>Eliminar imagen</h3>\n'
            '<p>Las imágenes marcadas se pueden eliminar usando “Eliminar seleccionados” o la '
            'tecla Eliminar. Antes de eliminar aparece una consulta de seguridad; Sin selección, '
            'primero se indica la selección necesaria.</p>\n'
            '<p>Solo los archivos de destino PNG/JPG/JPEG seleccionados se eliminan de los '
            'directorios del filtro de galería actual. El archivo fuente BMP original no se ve '
            'afectado.</p>\n'
            '\n'
            '<h3>Abrir carpeta de destino</h3>\n'
            '<p>"Abrir carpeta de destino" abre la ubicación de almacenamiento en el administrador '
            'de archivos y crea la carpeta raíz compartida si es necesario.</p>\n'
            '<p>El filtro "Current Commander" abre su subcarpeta Commander existente. Si aún no '
            'existe o hay otro filtro activo, se abrirá la carpeta raíz compartida.</p>\n'
            '\n'
            '<h3>Seguridad de las rutas de imágenes</h3>\n'
            '<p>Antes de eliminar, CMDRHelper comprueba la ruta canónica de cada archivo. Debe '
            'estar dentro de la carpeta de destino configurada y directamente en un directorio '
            'permitido por el filtro de galería actual.</p>\n'
            '<p>Los enlaces simbólicos no se utilizan como carpetas de comandante ni como imágenes '
            'de galería y no se eliminan a través de la galería. Se rechazan los caminos fuera del '
            'área de destino y los caminos transversales.</p>\n'
            '\n'
            '<h3>Si no se detectó ningún comandante</h3>\n'
            '<p>Si Commander y FID faltan al poner en cola una nueva grabación, el archivo no se '
            'pondrá en espera y no se asignará a un Commander conocido.</p>\n'
            '<p>Estará en la subcarpeta.<b>DESCONOCIDO_DESCONOCIDO/</b>procesado; el nombre del '
            'archivo también utilizado para el Commander<b>DESCONOCIDO</b>. Esta carpeta se puede '
            'ver a través de Todos los comandantes, no a través del filtro de carpeta raíz no '
            'asignada.</p>\n'
            '\n'
            '<h3>Varios comandantes</h3>\n'
            '<p>Se aplican dos reglas distintas a la gestión de imágenes:</p>\n'
            '<ul>\n'
            '<li><b>Guardar nuevas imágenes:</b>La identidad del diario activo con Commander y FID '
            'cuando está en cola determina la carpeta de destino.</li>\n'
            '<li><b>Ver imágenes:</b>El comandante visto o el filtro de galería seleccionado '
            'determina las imágenes visibles.</li>\n'
            '</ul>\n'
            '<p>Esto significa que se puede ver la galería de otro comandante mientras se juega a '
            'FABER38 sin que acaben nuevas capturas de pantalla en la carpeta del comandante en '
            'cuestión.</p>\n'
            '\n'
            '<h3>Consejo</h3>\n'
            '<p>Una carpeta raíz de captura de pantalla compartida es suficiente. CMDRHelper '
            'separa automáticamente las imágenes recién procesadas en Commander y FID.</p>\n'
            '<p>Con "Comandante actual", "Todos los comandantes" y "No asignados" puedes cambiar '
            'entre la galería personal, las subcarpetas de todos los comandantes y las imágenes '
            'más antiguas en la carpeta raíz.</p>\n'
            '<p>Un brillo más alto puede ayudar con fotografías oscuras; Afecta a la imagen de '
            'destino recién creada durante la conversión.</p>'),
 'commander_view': ('Vista CMDR',
                    '<h2>Vista CMDR</h2>\n'
                    '<p>La vista CMDR resume la información personal almacenada permanentemente de '
                    'un comandante.</p>\n'
                    '<p>También le permite cambiar entre los comandantes conocidos CMDRHelper y '
                    'ver sus propios datos. La información personal se separa mediante el ID '
                    'Frontier (FID).</p>\n'
                    '\n'
                    '<h3>Seleccionar comandante</h3>\n'
                    '<p>Si conoces varios comandantes, puedes usar la selección anterior para '
                    'determinar de quién se muestra la información guardada. Este comandante es el '
                    'comandante considerado.</p>\n'
                    '<p>La pantalla lo marca como “Live Active” o “View Only”.</p>\n'
                    '\n'
                    '<h3>Considerado Commander y Live Commander</h3>\n'
                    '<p>Seleccionar otro comandante en la vista CMDR no lo convierte en el '
                    'comandante de diario activo.</p>\n'
                    '<p>El comandante en vivo se determina exclusivamente a partir de la sesión '
                    'del diario Elite Dangerous actualmente identificada de forma única. De esta '
                    'manera se puede ver el historial de otro comandante mientras Elite Dangerous '
                    'continúa ejecutándose con FABER38.</p>\n'
                    '\n'
                    '<h3>Identificación de Frontier (FID)</h3>\n'
                    '<p>El FID es el identificador estable Frontier de un comandante.</p>\n'
                    '<p>CMDRHelper lo utiliza y el ID del comandante interno se resuelve a partir '
                    'de él para separar de forma segura los datos personales. Los comandantes con '
                    'nombres similares o idénticos también permanecen separados.</p>\n'
                    '\n'
                    '<h3>Descripción general</h3>\n'
                    '<p>La pestaña "Descripción general" solo muestra información guardada '
                    'permanentemente para el comandante en cuestión:</p>\n'
                    '<ul>\n'
                    '<li>Nombre del comandante, FID y estado “En vivo activo” o “Solo ver”</li>\n'
                    '<li>primera y última hora conocida</li>\n'
                    '<li>Número de sistemas visitados, descubrimientos biológicos y geográficos, '
                    'entradas de códices y ventas de cartografía</li>\n'
                    '<li>Última ubicación conocida y número de misiones abiertas</li>\n'
                    '<li>barco actual o último</li>\n'
                    '<li>Fleet Carrier y ubicación del transportista</li>\n'
                    '<li>Activos</li>\n'
                    '<li>biodatos abiertos y datos cartográficos abiertos, incluidas estimaciones '
                    'existentes</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Activos/Créditos</h3>\n'
                    '<p>El campo "Activos" muestra el saldo de crédito guardado más recientemente '
                    'del comandante en cuestión de un evento de diario apropiado, con el formato, '
                    'por ejemplo<b>1.234.567 millones</b>.</p>\n'
                    '<p>CMDRHelper no agrega ingresos ni gastos ficticios si no hay un estado de '
                    'diario nuevo y seguro.</p>\n'
                    '\n'
                    '<h3>Monedas mercenarias</h3>\n'
                    '<p>Las monedas mercenarias provienen de los campos MercCoins proporcionados '
                    'por Elite Dangerous.<code>Statistics → Bank_Account</code>y se guardan '
                    'relacionados con el comandante como una instantánea Frontier.</p>\n'
                    '<p>Visibles son:</p>\n'
                    '<ul>\n'
                    '<li>Actual</li>\n'
                    '<li>Total gastado</li>\n'
                    '<li>Ingeniería</li>\n'
                    '<li>equipo</li>\n'
                    '<li>Informado por Frontier: obtenido en general</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Actual y ediciones</h3>\n'
                    '<p>Programas “actuales”<code>MercCoins_Actual</code>. El “gasto total” toma '
                    'el relevo<code>MercCoins_Total_Gastado</code>.</p>\n'
                    '<p>“Ingeniería” y “Equipo” muestran las acciones reportadas por separado por '
                    'Frontier<code>MercCoins_Gastado_En_Ingeniería</code>y<code>MercCoins_Gastado_En_MercGear</code>.</p>\n'
                    '<p>Para FABER38, por ejemplo, un inventario actual de<b>1.275</b>, en '
                    'total<b>220</b>gastado y lejos<b>220</b>reportado para ingeniería.</p>\n'
                    '\n'
                    '<h3>En general merecido</h3>\n'
                    '<p>"Reportado por Frontier: obtenido en general" '
                    'muestra<code>MercCoins_Total_Ganado</code>. CMDRHelper no calcula su propio '
                    'balance a partir de esto.</p>\n'
                    '<p>El valor acumulado de Frontier no tiene que coincidir matemáticamente con '
                    'el inventario actual y los gastos reportados. Por ejemplo, se pueden informar '
                    'al mismo tiempo 1275 actuales, 25 ganados en total y 220 gastados en '
                    'total.</p>\n'
                    '<p>CMDRHelper no corrige estos valores, pero muestra los contadores Frontier '
                    'individuales sin cambios.</p>\n'
                    '\n'
                    '<h3>¿Por qué no tener su propio balance MercCoins?</h3>\n'
                    '<p>Elite Dangerous no proporciona un registro de asiento de diario único para '
                    'cada recibo o gasto individual de monedas mercenarias. Los MercCoins aparecen '
                    'como totales en Statistics.</p>\n'
                    '<p>Por lo tanto, un historial de reservas calculado por uno mismo no sería '
                    'fiable. En su lugar, CMDRHelper guarda la última instantánea conocida de '
                    'Frontier.</p>\n'
                    '\n'
                    '<h3>Misiones</h3>\n'
                    '<p>La pestaña "Misiones" muestra las misiones guardadas del comandante en '
                    'cuestión como una tabla con estado, nombre de la misión, objetivo, tiempo de '
                    'vencimiento y recompensa.</p>\n'
                    '\n'
                    '<h3>exploración</h3>\n'
                    '<p>La pestaña Exploración muestra biodatos abiertos, datos de cartografía '
                    'abierta, biodescubrimientos, primeros pasos, cuerpos automapeados y '
                    'cartografiados de manera eficiente, y la cantidad de sistemas visitados.</p>\n'
                    '<p>La pestaña dedicada "Crónica" dentro de la vista CMDR sigue siendo '
                    'actualmente un marcador de posición. La crónica completa se puede encontrar '
                    'en el elemento del menú principal del mismo nombre.</p>\n'
                    '\n'
                    '<h3>Barcos/Flota</h3>\n'
                    '<p>La pestaña "Barcos" muestra inicialmente el barco activo o utilizado más '
                    'recientemente con el nombre del barco, el tipo de barco, la ubicación y el ID '
                    'del barco.</p>\n'
                    '<p>Los barcos salvados del comandante en cuestión aparecen debajo como '
                    'tarjetas ampliables. Se pueden ordenar de forma ascendente o descendente '
                    'por:</p>\n'
                    '<ul>\n'
                    '<li>último o utilizado actualmente</li>\n'
                    '<li>Nombre del barco o tipo de barco</li>\n'
                    '<li>rango máximo de salto</li>\n'
                    '<li>Capacidad de carga o masa vacía</li>\n'
                    '<li>última ubicación o hora conocida</li>\n'
                    '</ul>\n'
                    '<p>También puedes filtrar por todos los barcos, barcos con un hangar para '
                    'vehículos o barcos con un hangar para cazas.</p>\n'
                    '\n'
                    '<h3>Detalles del barco</h3>\n'
                    '<p>Un mapa de barco abierto muestra, si se guarda, ID del barco, ID del '
                    'barco, ubicación, última vez, alcance máximo de salto, FSD y refuerzo '
                    'Guardian, masa, carga y capacidades del tanque, así como el tiempo y el '
                    'estado de carga.</p>\n'
                    '<p>Si los datos del módulo están disponibles, también se resumen los hangares '
                    'de vehículos y cazas, el generador de escudo y el refuerzo de escudo, los '
                    'refuerzos del escudo Guardián, las armas, los refuerzos del casco y del '
                    'módulo y las cabinas de pasajeros.</p>\n'
                    '<p>El estado del equipamiento puede ser completo, incompleto o obsoleto. La '
                    'información faltante se muestra como “–” y no se completa.</p>\n'
                    '\n'
                    '<h3>Fleet Carrier</h3>\n'
                    '<p>Para un Fleet Carrier personalizado guardado, la vista muestra el nombre '
                    'del operador, el distintivo de llamada, el ID del operador, la última '
                    'ubicación y la hora de la última actualización.</p>\n'
                    '\n'
                    '<h3>Estado comandante persistente</h3>\n'
                    '<p>La información importante del comandante permanece guardada '
                    'permanentemente. Esto permite que los valores conocidos se muestren '
                    'nuevamente después de reiniciar CMDRHelper o Elite Dangerous sin volver a '
                    'evaluar completamente cada diario.</p>\n'
                    '<p>Los nuevos eventos de diario únicos actualizan el estado guardado.</p>\n'
                    '\n'
                    '<h3>Reconstrucción histórica</h3>\n'
                    '<p>Para funciones que se agregan más adelante, CMDRHelper puede buscar una '
                    'vez en áreas de diario existentes que están claramente asignadas a un '
                    'comandante información que ya se conoce.</p>\n'
                    '<p>Por ejemplo, se pueden adoptar instantáneas MercCoins más antiguas. Las '
                    'comprobaciones repetidas no tienen como objetivo producir datos duplicados y '
                    'no alteran las posiciones normales de lectura del diario.</p>\n'
                    '\n'
                    '<h3>Varios comandantes</h3>\n'
                    '<p>En particular, los siguientes permanecen separados en términos de '
                    'comandantes:</p>\n'
                    '<ul>\n'
                    '<li>Activos y misiones</li>\n'
                    '<li>Cartografía propia y hallazgos orgánicos.</li>\n'
                    '<li>Historia de la minería a cielo abierto y monedas mercenarias.</li>\n'
                    '<li>Credenciales en línea</li>\n'
                    '<li>capturas de pantalla relacionadas con el comandante</li>\n'
                    '</ul>\n'
                    '<p>Sin embargo, las propiedades astronómicas globales de un sistema o cuerpo '
                    'se pueden utilizar juntas.</p>\n'
                    '\n'
                    '<h3>Impacto en otras vistas</h3>\n'
                    '<p>Al cambiar el comandante en cuestión se actualiza la propia vista CMDR, la '
                    'selección de materia prima de minería personal de la crónica y, con el filtro '
                    'adecuado, la galería de capturas de pantalla.</p>\n'
                    '<p>No reemplaza al Live Commander real para el procesamiento de diarios o '
                    'cargas en línea.</p>\n'
                    '\n'
                    '<h3>Inara y EDSM</h3>\n'
                    '<p>Los accesos Inara y EDSM se administran por separado por comandante y FID, '
                    'respectivamente.</p>\n'
                    '<p>Simplemente mirar a un comandante no inicia una transmisión con su '
                    'API-Key. Solo el diario activo FID es relevante para las cargas en vivo.</p>\n'
                    '<p>Los datos de acceso se gestionan en “Configuración” en el área de '
                    'servicios online.</p>\n'
                    '\n'
                    '<h3>Consejo</h3>\n'
                    '<p>Utilice la vista CMDR si desea ver la información personal guardada de un '
                    'comandante específico.</p>\n'
                    '<p><b>Vista CMDR = ¿A quién quiero ver?</b></p>\n'
                    '<p><b>Active Journal-FID = ¿Quién está jugando actualmente?</b></p>\n'
                    '<p>Esta separación evita que se mezclen datos personales o cargas en línea de '
                    'diferentes comandantes.</p>'),
 'settings': ('Ajustes',
              '<h2>Ajustes</h2>\n'
              '<p>El área "Configuración" determina cómo funciona CMDRHelper con Elite Dangerous, '
              'archivos de diario, base de datos, servicios en línea, interfaz y '
              'actualizaciones.</p>\n'
              '<p>Los cambios en las credenciales y rutas deben realizarse con cuidado. Las '
              'configuraciones relacionadas con Commander se administran por separado mediante el '
              'ID Frontier si es necesario.</p>\n'
              '\n'
              '<h3>diario</h3>\n'
              '<p>La carpeta del diario es una de las configuraciones más importantes. Debe '
              'apuntar a la carpeta donde Elite Dangerous se '
              'encuentra<code>Diario*.log</code>archivos del perfil de Windows o Proton '
              'utilizado.</p>\n'
              '<p>Las revistas proporcionan, entre otras cosas:</p>\n'
              '<ul>\n'
              '<li>Identidad, ubicación y viajes del comandante.</li>\n'
              '<li>Misiones, barcos y activos</li>\n'
              '<li>Exploración, cartografía y datos BIO</li>\n'
              '<li>Minería a cielo abierto, monedas mercenarias y otros estados apoyados</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Visualización y funcionamiento del diario</h3>\n'
              '<p>El grupo de revistas muestra el conjunto de carpetas, el número de revistas '
              'encontradas, las revistas más antiguas y más recientes, el nombre del archivo más '
              'reciente y la hora de la última entrada leída.</p>\n'
              '<p>“Seleccionar carpeta de diario” cambia la carpeta. "Leer ahora" activa la '
              'actualización normal de inmediato.</p>\n'
              '<p>Las sesiones claramente identificables se asignan mediante FID. Las nuevas '
              'entradas completas se procesan de forma incremental; Las posiciones de lectura '
              'seguras evitan que cada revista se vuelva a leer innecesariamente en su totalidad '
              'la próxima vez que se inicie.</p>\n'
              '\n'
              '<h3>base de datos</h3>\n'
              '<p>CMDRHelper almacena permanentemente los datos requeridos en una base de datos '
              'local SQLite. Esto incluye datos globales del sistema y del cuerpo, así como '
              'información asignada explícitamente a un comandante.</p>\n'
              '<p>La página de configuración muestra estadísticas sobre los datos guardados. La '
              'base de datos no debe editarse manualmente mientras se ejecuta CMDRHelper.</p>\n'
              '\n'
              '<h3>Importar archivo de diario</h3>\n'
              '<p>“Importar archivo de diario” compara completamente los archivos de diario de la '
              'carpeta de diario establecida con la base de datos. Las áreas de diario ya '
              'conocidas se tienen en cuenta en función de la información de importación guardada '
              'y no se duplican ciegamente como datos nuevos.</p>\n'
              '<p>Durante una importación visible manualmente, se muestran el progreso, el número '
              'y el archivo procesado actualmente. Una vez finalizado, CMDRHelper informa datos '
              'importados o ya conocidos o un error.</p>\n'
              '<p>La importación de archivos también sirve para volver a aprender información '
              'histórica respaldada de revistas claramente asignadas.</p>\n'
              '\n'
              '<h3>Datos relacionados con el comandante</h3>\n'
              '<p>CMDRHelper separa la información personal según el FID y el ID interno asociado '
              'del Commander. Estos incluyen, entre otros, misiones, activos, MercCoins, '
              'exploración personal y acceso en línea.</p>\n'
              '<p>No se puede asignar arbitrariamente a un comandante una sesión de diario '
              'desconocida o ambigua.</p>\n'
              '\n'
              '<h3>Servicios en línea</h3>\n'
              '<p>CMDRHelper es compatible con EDSM y Inara. Ambos accesos se procesan y guardan '
              'por separado para cada comandante conocido o cada FID.</p>\n'
              '<p>La selección en la configuración solo determina qué acceso se está editando o '
              'probando actualmente. Sólo el comandante claramente identificado por la sesión de '
              'diario activa puede enviar en vivo.</p>\n'
              '\n'
              '<h3>Acceso EDSM para</h3>\n'
              '<p>“EDSM acceso para:” selecciona el comandante a editar. La selección mostrará '
              '"configurado" o "no configurado" dependiendo de si está almacenado un API-Key.</p>\n'
              '<p>Son visibles el nombre del comandante, el campo oculto API-Key, "Usar EDSM", una '
              'prueba de conexión y su último estado de prueba.</p>\n'
              '<p>Cada comandante necesita su propio acceso EDSM apropiado. La selección no cambia '
              'el cargador en vivo a este comandante.</p>\n'
              '\n'
              '<h3>Utilice y pruebe EDSM</h3>\n'
              '<p>“Usar EDSM” habilita o deshabilita el servicio para el FID seleccionado. Las '
              'credenciales faltantes o desactivadas no afectan el procesamiento del diario '
              'local.</p>\n'
              '<p>“Probar conexión EDSM” comprueba los datos de acceso actualmente visibles en el '
              'formulario. Una prueba exitosa confirma la conexión, pero no cambia el diario '
              'activo FID ni el Live Commander.</p>\n'
              '\n'
              '<h3>Acceso Inara para</h3>\n'
              '<p>“Inara Acceso para:” sigue el mismo principio multi-CMDR. La activación, el '
              'nombre del comandante Inara y API-Key se guardan por separado para cada FID.</p>\n'
              '<p>También en este caso la selección muestra “configurado” o “no configurado”. Una '
              'clave de un comandante no se usa automáticamente para otro comandante.</p>\n'
              '\n'
              '<h3>Utilice y pruebe Inara</h3>\n'
              '<p>Con Inara configurado y habilitado para el diario activo FID, CMDRHelper puede '
              'transmitir los eventos de viaje, ubicación, misión y barco admitidos. No todos los '
              'eventos del diario se envían a Inara.</p>\n'
              '<p>“Probar conexión Inara” verifica los datos de acceso visibles actualmente sin '
              'cambiar el comandante en vivo.</p>\n'
              '\n'
              '<h3>Bandeja de salida Inara</h3>\n'
              '<p>Los eventos Inara admitidos se marcan persistentemente en una bandeja de salida '
              'antes de la transmisión de red.</p>\n'
              '<p>Los errores temporales permiten conservar estas entradas para intentos '
              'posteriores. El trabajador solo procesa la bandeja de salida del diario '
              'exclusivamente activo FID; No se incluyen las entradas de otros comandantes.</p>\n'
              '\n'
              '<h3>Estado en línea en el encabezado</h3>\n'
              '<p>EDSM muestra actualmente:</p>\n'
              '<ul>\n'
              '<li><b>EDSM</b>– no se puede utilizar ni desactivar para el FID activo</li>\n'
              '<li><b>EDSM está esperando</b>– configurado y sin transmisión en curso</li>\n'
              '<li><b>Transmisión EDSM</b>– la última ejecución del procesamiento EDSM finalizó '
              'sin errores; La información sobre herramientas indica si se enviaron eventos, se '
              'procesaron datos del diario o no se encontraron datos nuevos.</li>\n'
              '<li><b>Error EDSM</b>– el último estado de transmisión es incorrecto</li>\n'
              '</ul>\n'
              '<p>Actualmente no existe un estado adicional etiquetado por separado "EDSM activo" '
              'para EDSM.</p>\n'
              '<p>Inara distingue con mayor precisión:</p>\n'
              '<ul>\n'
              '<li><b>INARA fuera</b>– deshabilitado para el diario activo FID</li>\n'
              '<li><b>INARA listo</b>– configurado, pero aún sin transmisión confirmada en esta '
              'sesión</li>\n'
              '<li><b>transmisión INARA</b>– el trabajador está enviando actualmente</li>\n'
              '<li><b>INARA activo</b>– la última transferencia real fue confirmada '
              'exitosamente</li>\n'
              '<li><b>Error INARA</b>– el último intento de transferencia falló</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Seguridad API-Key</h3>\n'
              '<p>Las API-Key son credenciales personales. Los campos de entrada están ocultos; Se '
              'almacenan relacionados con el comandante en la configuración de la aplicación y no '
              'en la base de datos CMDRHelper.</p>\n'
              '<p>Las claves no deben publicarse, compartirse en capturas de pantalla ni agregarse '
              'a repositorios públicos.</p>\n'
              '\n'
              '<h3>Imágenes/Capturas de pantalla</h3>\n'
              '<p>La carpeta de origen, la carpeta de destino, PNG/JPG, el procesamiento '
              'automático, la eliminación de BMP y el brillo del 0 al 50 por ciento se encuentran '
              'exclusivamente en el menú principal de Imágenes, no en la página de '
              'Configuración.</p>\n'
              '<p>La ayuda contextual "Imágenes" describe estas opciones en detalle.</p>\n'
              '\n'
              '<h3>superficie</h3>\n'
              '<p>El grupo de interfaz incluye la apariencia, el idioma, la fuente, el tamaño de '
              'fuente y el umbral de valor para cuerpos valiosos del explorador.</p>\n'
              '\n'
              '<h3>Modo oscuro y claro</h3>\n'
              '<p>Puede cambiar directamente entre apariencia oscura y clara. El tema se aplica '
              'inmediatamente a la interfaz y al sistema existente y a las tarjetas de historial y '
              'se guarda.</p>\n'
              '\n'
              '<h3>Idioma</h3>\n'
              '<p>La interfaz ofrece doce idiomas para elegir. “Guardar idioma” guarda la '
              'selección; Luego es necesario reiniciar CMDRHelper para una conversión '
              'completamente uniforme de los widgets existentes.</p>\n'
              '\n'
              '<h3>Fuente y tamaño de fuente</h3>\n'
              '<p>Se puede seleccionar y guardar la familia de fuentes y el tamaño de fuente de 7 '
              'a 24 pt.</p>\n'
              '<p>Ambos cambios solo tendrán pleno efecto después de reiniciar. La interfaz lo '
              'indica explícitamente.</p>\n'
              '\n'
              '<h3>Umbral de valor</h3>\n'
              '<p>El umbral de valor del Explorer determina el valor crediticio estimado a partir '
              'del cual los cuerpos se destacan como particularmente valiosos. El cambio se guarda '
              'inmediatamente y actualiza la pantalla del Explorador correspondiente.</p>\n'
              '\n'
              '<h3>Ocultar automáticamente</h3>\n'
              '<p>“Cuerpos preciosos” y “Hallazgos BIO” están firmemente ubicados en la barra '
              'lateral izquierda, no en la página de Configuración.</p>\n'
              '<p>Los interruptores se guardan y controlan las pequeñas ventanas de sugerencias en '
              'vivo admitidas durante la exploración. El umbral de valor para Valuable Bodies se '
              'establece en la configuración de la interfaz.</p>\n'
              '\n'
              '<p>La ventana Cargo utiliza exclusivamente el snapshot Cargo confirmado para la Journal-FID activa. El commander consultado en CMDR View y viewed_commander_id no afectan a esta ventana en vivo. Para un Ship muestra ocupado / máximo · libre; si CargoCapacity es desconocida, no se estima ningún valor.</p>\n'
              '\n'
              '<h3>Actualizaciones</h3>\n'
              '<p>El grupo de actualización muestra la versión instalada y el estado de GitHub. '
              'Check Now busca manualmente una nueva versión programada de CMDRHelper; Además, '
              'después del inicio se realiza un control automático diferido.</p>\n'
              '<p>Si hay una nueva versión disponible, CMDRHelper le preguntará antes de '
              'descargarla e instalarla. Una actualización de base de datos anunciada se muestra '
              'por separado en este cuadro de diálogo.</p>\n'
              '\n'
              '<h3>Descargar progreso</h3>\n'
              '<p>La descarga se ejecuta en segundo plano. Si se conoce el tamaño total, '
              'CMDRHelper muestra el nombre del archivo, los MiB recibidos y totales, el '
              'porcentaje, la tasa de transferencia y el tiempo restante estimado.</p>\n'
              '<p>Sin un tamaño total conocido, la barra de progreso funciona en modo ocupado y '
              'continúa mostrando la cantidad de datos recibidos y, si es determinable, la '
              'velocidad. Antes de la instalación, se verifica el ZIP descargado.</p>\n'
              '\n'
              '<h3>Cancelar actualización</h3>\n'
              '<p>“Cancelar descarga” finaliza una descarga en curso de forma controlada. No se '
              'instalará una descarga cancelada, incompleta o no válida.</p>\n'
              '\n'
              '<h3>Actualización en Windows</h3>\n'
              '<p>En Windows, el proceso de actualización real continúa independientemente de la '
              'consola de inicio original. Por lo tanto, un apagado de la consola no debería '
              'finalizarla involuntariamente.</p>\n'
              '<p>Si se produce un error después de que hayan comenzado los cambios de archivos, '
              'la copia de seguridad de reversión existente intenta restaurar la versión '
              'anterior.</p>\n'
              '\n'
              '<h3>Reiniciar después de la actualización</h3>\n'
              '<p>Después de una instalación exitosa, el actualizador CMDRHelper se reinicia a '
              'través de la ruta de inicio prevista y verifica brevemente si el nuevo proceso se '
              'está ejecutando de manera estable.</p>\n'
              '<p>Si una versión requiere una actualización única de la base de datos, el archivo '
              'del diario también se reevaluará después del reinicio.</p>\n'
              '\n'
              '<h3>Varios comandantes</h3>\n'
              '<p><b>Selección de configuración = ¿De quién estoy editando el acceso en '
              'línea?</b></p>\n'
              '<p><b>Active Journal-FID = ¿Quién puede transmitir en vivo?</b></p>\n'
              '<p>Ni la selección de cuenta en línea ni la vista CMDR pueden cambiar a un usuario '
              'que subió contenido en vivo a un comandante de solo visualización.</p>\n'
              '\n'
              '<h3>Ayuda</h3>\n'
              '<p>"? Ayuda" se encuentra en la barra lateral izquierda encima de "auto show" y '
              'abre la ayuda del área del menú principal actualmente visible.</p>\n'
              '<p>En el área "Configuración", el botón abre esta ayuda de configuración '
              'directamente.</p>\n'
              '\n'
              '<h3>Consejo</h3>\n'
              '<p>Si está reinstalando o tiene problemas, verifique primero:</p>\n'
              '<ul>\n'
              '<li>carpeta de diario correcta e identidad de comandante reconocida</li>\n'
              '<li>idioma deseado, tema, fuente y umbral de valor del explorador</li>\n'
              '<li>Acceso en línea al FID correcto</li>\n'
              '<li>En caso de problemas con la imagen, carpetas de origen y de destino en el menú '
              'principal “Imágenes”</li>\n'
              '</ul>\n'
              '<p>Si hay varios comandantes, preste siempre atención a a qué FID se aplican los '
              'datos visibles de acceso en línea.</p>'),
    "planet_navigation": (
        'Navegación planetaria',
        """<h2>Navegación planetaria</h2>
<p>El navegador planetario sirve exclusivamente para volar hasta una latitud/longitud concreta en un planeta o una luna. Defines un objetivo mediante coordenadas y obtienes la distancia y la dirección para llegar a él.</p>
<p>No es un planificador de rutas interestelares y no se encarga de la navegación entre sistemas ni de los saltos. Tú pilotas tu nave.</p>

<h3>Abrir el navegador e introducir un objetivo</h3>
<p>En la vista general, abre «Navegación planetaria» y selecciona «Introducir objetivo …».</p>
<ul>
<li><b>Cuerpo celeste:</b> Selecciona el planeta o la luna de destino en la lista o utiliza el cuerpo ya detectado. También puedes escribir su nombre si aún no figura en la lista. En caso de duda, utiliza el nombre completo, incluido el del sistema.</li>
<li><b>Latitud:</b> Introduce la latitud del objetivo entre −90° y +90°.</li>
<li><b>Longitud:</b> Introduce la longitud del objetivo entre −180° y +180°. Presta atención al signo de ambas coordenadas.</li>
<li><b>Nombre del objetivo:</b> Opcionalmente, puedes introducir una denominación para reconocer tu objetivo más fácilmente.</li>
</ul>
<p>«Establecer objetivo» confirma los datos introducidos. No tienes que introducir identificadores técnicos como BodyID y SystemAddress; no son datos habituales que deba introducir el usuario.</p>

<h3>¿Cuándo se activa la brújula?</h3>
<p>En cuanto hay un objetivo establecido y Elite proporciona datos válidos de posición planetaria para el cuerpo correspondiente, la navegación se activa automáticamente. No tienes que pulsar un botón de inicio aparte.</p>
<p>Si aún faltan esos datos o corresponden a otro cuerpo, el navegador espera mostrando «Esperando coordenadas planetarias …». Puedes introducir un objetivo incluso antes de recibir esos datos.</p>

<h3>Globo planetario: más de 380 km</h3>
<p>Cuando la distancia al objetivo es superior a 380 km, el navegador muestra el globo planetario.</p>
<ul>
<li>El <b>círculo blanco</b> marca tu posición.</li>
<li>El <b>pequeño punto del objetivo</b> es naranja cuando el objetivo está en el lado visible del planeta.</li>
<li>Si el objetivo está en la cara posterior oculta, el punto se muestra en rojo.</li>
<li>Tu posición permanece fija en la representación. El planeta y el objetivo se muestran con respecto a tu posición y orientación.</li>
</ul>
<p>La flecha blanca apunta hacia delante; la amarilla indica la dirección relativa del objetivo. El globo es una ayuda esquemática para orientarte, no una vista del terreno geográficamente precisa. Un punto rojo significa la cara posterior del globo, no automáticamente «detrás de tu nave».</p>

<h3>Cuadrícula en perspectiva: hasta 380 km inclusive</h3>
<p>A una distancia del objetivo de hasta 380 km inclusive, la pantalla cambia automáticamente a una cuadrícula inclinada en perspectiva. Si la distancia vuelve a superar los 380 km, reaparece el globo.</p>
<p>Las líneas transversales forman una <b>cuadrícula de distancias en intervalos de 50 km</b>. El punto del objetivo se dibuja dentro de la cuadrícula según la distancia y la dirección relativa. La perspectiva ayuda durante la aproximación posterior; la inclinación hace que los espacios parezcan más juntos hacia el fondo. Para el rumbo concreto que debes seguir, observa también el rumbo al objetivo y la dirección relativa.</p>

<h3>Leer correctamente los valores de navegación</h3>
<ul>
<li><b>Distancia al objetivo:</b> La indicación grande muestra la distancia restante hasta el objetivo a lo largo de la superficie planetaria idealizada.</li>
<li><b>Coordenadas del objetivo:</b> El par de coordenadas introducido para el objetivo, primero latitud y después longitud. Permanece sin cambios mientras te mueves.</li>
<li><b>Coordenadas actuales:</b> Tu último par de coordenadas confirmado por Elite, también latitud / longitud.</li>
<li><b>Distancia sobre la superficie:</b> La misma distancia sobre la superficie que la distancia al objetivo, posiblemente redondeada con mayor precisión en la vista detallada. No es una segunda ruta ni una distancia espacial directa por el aire.</li>
<li><b>Marcación:</b> La dirección absoluta hacia el objetivo desde tu posición actual, expresada como ángulo de brújula: 000° es norte, 090° este, 180° sur y 270° oeste.</li>
<li><b>Rumbo:</b> Tu orientación actual, tal como la proporciona Elite. Indica hacia dónde estás orientado y no tiene por qué coincidir todavía con la marcación.</li>
<li><b>Dirección relativa:</b> La diferencia entre tu orientación y la marcación, por ejemplo «23° a la derecha», «10° a la izquierda» o «Todo recto». A 180°, el objetivo está detrás de ti.</li>
<li><b>Rumbo al objetivo:</b> La marcación destacada como rumbo absoluto al que puedes girar en el HUD de Elite. No es un ángulo de giro adicional.</li>
</ul>
<p>Ejemplo: con un rumbo de 051° y un rumbo al objetivo de 074°, gira 23° a la derecha hasta que tu brújula de Elite indique aproximadamente 074°. Durante el vuelo, la marcación y el rumbo al objetivo pueden cambiar; guíate por los valores actualizados.</p>
<p>En la misma posición que el objetivo, en un polo o en el punto exactamente opuesto del planeta, la dirección puede ser indeterminada. En ese caso, el navegador muestra el aviso correspondiente en vez de un rumbo inventado.</p>

<h3>Tamaño de la ventana</h3>
<p>La ventana del navegador se puede redimensionar libremente. El globo o la cuadrícula en perspectiva se adaptan proporcionalmente al espacio disponible. El tamaño mínimo mantiene legibles los valores detallados; el globo sigue siendo redondo. La posición y el tamaño de la ventana se guardan.</p>

<h3>Activar el HUD de navegación</h3>
<p>A la izquierda de la ventana principal, marca la casilla bajo <b>mostrar automáticamente → HUD de navegación</b>. Con una navegación planetaria válida, el HUD aparece directamente sobre la ventana visible de Elite en primer plano.</p>
<p>Muestra tres líneas:</p>
<ul>
<li>dirección relativa</li>
<li>rumbo al objetivo</li>
<li>distancia</li>
</ul>
<p>El HUD es transparente, deja pasar los clics y no toma el foco: no tapa el juego con una superficie opaca, no intercepta los clics del ratón y no quita a Elite el foco de entrada al aparecer automáticamente.</p>
<p>Sin navegación válida o una dirección inequívoca, se vuelve invisible automáticamente. También se oculta si Elite está minimizado o no está en primer plano. La casilla de la barra lateral puede seguir marcada; expresa tu preferencia por la visualización automática, no la visibilidad actual.</p>
<p>El HUD es solo una visualización adicional. El navegador normal funciona de forma independiente, incluso si el HUD está desactivado o no está disponible.</p>

<h3>Establecer un nuevo objetivo</h3>
<p>En el mismo cuerpo puedes volver a abrir «Introducir objetivo …» en cualquier momento y establecer otras coordenadas. El nuevo objetivo sustituye al objetivo de navegación anterior. Con datos de posición correspondientes, la brújula se actualiza inmediatamente.</p>
<p>«Finalizar navegación» elimina el objetivo actual. Para otra aproximación, simplemente establece un nuevo objetivo.</p>

<h3>Actualidad de los datos y límites</h3>
<p>La navegación se basa en los datos de estado proporcionados por Elite. Las actualizaciones pueden llegar con retraso según el estado del juego. El indicador de antigüedad del navegador muestra cuánto tiempo ha pasado desde el último mensaje de estado confirmado.</p>
<p>La distancia sobre la superficie describe el arco más corto sobre una esfera idealizada. No es una ruta por el terreno ni por carretera. El navegador no conoce los obstáculos ni las alturas del terreno a lo largo del trayecto; la altitud de vuelo, una velocidad segura y evitar los obstáculos siguen siendo tu responsabilidad.</p>

<h3>Consejo</h3>
<p>Antes de la aproximación, comprueba el nombre del cuerpo y los signos de las coordenadas del objetivo. Después, alinéate con el rumbo al objetivo en la brújula de Elite y observa la dirección relativa y la distancia. Si el navegador está esperando, comprueba si Elite ya proporciona coordenadas planetarias para el cuerpo de destino.</p>""",
    ),
}

DIALOG_TITLE = 'Ayuda – {area}'
CLOSE_LABEL = 'Cerrar'
