🔢Rompecabezas del 15.
@DxMorgan @ArgentSimia @PuzzleSimBotMay 17, 2026
🧩 1. Concepto General del Juego
El juego está basado en el clásico Fifteen Puzzle. Consiste en una cuadrícula interactiva de 4x4 que contiene 15 botones numerados (del 1 al 15) y un casillero vacío (representado por un espacio en blanco " ").

Mecánica Touch: No hay flechas estorbando. El usuario presiona directamente cualquier número que esté al lado (arriba, abajo o a los costados) del espacio vacío, y la pieza se desliza instantáneamente a esa posición.
Garantía Matemático-IA: El bot cuenta con un algoritmo de validación de inversiones. Esto asegura que cada vez que se mezcla un tablero, la posición inicial sea 100% resoluble, eliminando la posibilidad de que el juego quede trabado en un callejón sin salida imposible.
🎮 2. Las 3 Modalidades de Juego (Lobby Adaptativo)
El comando principal es /puzzgame. Dependiendo de cómo lo ejecute el usuario y quién presione el botón único de ⚔️ Aceptar Desafío, el bot conmuta su comportamiento en tres modos inteligentes:

👤 Modo Solitario (Solo)
Cómo se activa: El usuario escribe /puzzgame a secas en el grupo (o en su chat privado con el bot) y él mismo presiona el botón del Lobby.
Dinámica: El bot interpreta que el anfitrión quiere jugar solo. Transforma el mensaje del lobby en su tablero personal. El juego registra activamente sus movimientos y expone el cronómetro en vivo en la cabecera.
🤝 Modo Desafío Abierto
Cómo se activa: El anfitrión escribe /puzzgame a secas en el grupo y cualquier otro miembro del chat presiona el botón.
Dinámica: El bot cierra el lobby y despliega dos tableros independientes pero idénticamente desordenados (mismo mapa espejo). El de arriba lleva el nombre del anfitrión y el de abajo el del invitado. Compiten en simultáneo para ver quién tiene más velocidad y precisión.
🎯 Modo Duelo Directo (Por Réplica)
Cómo se activa: El anfitrión selecciona un mensaje de un usuario específico del grupo y le da Responder (Reply) escribiendo /puzzgame.
Dinámica: El bot lee el ID del usuario replicado y congela el derecho de admisión del Lobby. Si un tercero intenta "colarse" presionando el botón, el bot le lanza una alerta flotante en la pantalla avisando que es un Duelo Privado. El duelo solo inicia si el desafiado estricto acepta el reto (el anfitrión mantiene el derecho de presionar el botón para cancelar e irse a Modo Solo si lo ignoran).
🛡️ Filtro Anti-Spoofing (Seguridad de botones): En cualquiera de los modos multijugador, el ID de cada jugador viaja encriptado en los metadatos de su cuadrícula. Si el Jugador B intenta clickear o arruinar el tablero del Jugador A, el bot detecta el cruce de identidades y lo ignora por completo, garantizando partidas limpias de sabotajes.

🏆 3. Sistema de Rankings y Estadísticas (Aislado por Chat)
El cambio estructural más importante es que la base de datos se ramifica por el chat_id. Los récords de un grupo no se mezclan con los de otro, ni con los juegos casuales en el chat privado del bot. Cada chat es una liga independiente.

🥇 El Ranking Grupal (/puzztop)
Determina quiénes son los mejores de ese grupo específico y muestra un podio de hasta 15 lugares ordenados bajo las siguientes reglas competitivas:

Prioridad 1 - Menor cantidad de movimientos: La tabla se rige por la precisión. Quien resuelva el puzzle con menos clicks se adueña de la cima. Esto anula las ventajas de quienes tienen mejor señal de internet o menos lag.
Prioridad 2 - Tiempo de desempate: Si dos usuarios (o el mismo) logran empatar en cantidad de movimientos, el bot revisa los segundos de duración de la partida y pone arriba al más veloz.
Multi-récord: Al premiar el desempeño de la partida y no al usuario como individuo, un jugador habilidoso puede monopolizar varios puestos del Top 15 general si registra múltiples partidas brillantes.
📊 Las Estadísticas Personales (/puzzrank)
Al ejecutar el comando (o responderle a otro usuario con él), el bot expone la tarjeta del perfil deportivo local del jugador dentro de ese grupo:

Partidas finalizadas: Cuántas veces logró solucionar el puzzle con éxito en esa sala.
Top 5 de Tiempos: Una lista ordenada de sus 5 cronómetros más rápidos.
Top 5 de Movimientos: Una lista ordenada de sus 5 mejores marcas de precisión de clicks.
🏁 4. Cierre de Partida y Acta de Resultados 1v1
En los modos competitivos (Desafío Abierto y Duelo Directo), la partida termina por K.O. Técnico en el instante en que cualquiera de los dos jugadores hace el click final que ordena el tablero.

En ese milisegundo, el bot ejecuta un protocolo de cierre automático:

Congelamiento: Desactiva los botones de ambos tableros del grupo sustituyendo las acciones por callbacks muertos (puzz_ignore) para que nadie pueda seguir moviendo piezas después del cierre.
Cálculo de Eficacia (%): El bot analiza el tablero del perdedor en ese instante exacto y calcula mediante lógica matemática cuántas piezas llegó a acomodar en su lugar real (del 1 al 15).
Envío de Reporte Final: Envía una burbuja de texto independiente al chat grupal con el resumen definitivo para el historial:
Bloque Ganador: Expone su mención, sus movimientos totales y el tiempo formateado de manera legible (ej: 2min 15s), coronándolo con un 100% ordenado.
Bloque Perdedor: Expone su mención, cuántos movimientos llegó a meter en su pantalla y expone el porcentaje de progreso en el que se quedó al momento de la derrota (ej: 64% ordenado).
Este sistema convierte al juego en una adicción para los grupos, ideal para resolver discusiones, armar competencias internas o simplemente ver quién es el más ágil de la comunidad.

