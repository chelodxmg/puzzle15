import asyncio
import os
import json
import random
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import telegram.error
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- CONFIGURACIÓN GENERAL ---
TOKEN = "8936249846:AAEZ6Soic6kF-kGTa2Nw43S-SuLXrYdSSos"

# RUTA CORREGIDA: Ahora es relativa al proyecto. Funciona tanto en tu PC como en servidores Linux en la web.
JSON_PATH = os.path.join(os.getcwd(), "puzzle-sim-bot.json")

# URL de tu hosting (Ej: https://tu-bot-puzzle.onrender.com). Reemplazala por la que te dé tu hoster.
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://puzzle-sim-bot.onrender.com")
PORT = int(os.environ.get("PORT", 8000)) # El puerto asignado automáticamente por el servidor gratuito

# Diccionario en memoria para almacenar las partidas activas y estados del lobby
USER_GAMES = {}

# --- FUNCIONES DE PERSISTENCIA (JSON AISLADO POR CHAT) ---
def load_stats():
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "global_top" in data or "players" in data:
            return {"legacy_migration": data}
        return data
    except Exception:
        return {}

def save_victory_stats(chat_id, user_id, username, moves, duration):
    stats = load_stats()
    cid_str = str(chat_id)
    uid_str = str(user_id)
    
    if cid_str not in stats:
        stats[cid_str] = {"global_top": [], "players": {}}
        
    chat_data = stats[cid_str]
    if "players" not in chat_data: chat_data["players"] = {}
    if "global_top" not in chat_data: chat_data["global_top"] = []
    
    display_name = username.replace("@", "") if username else f"User_{user_id}"
    
    if uid_str not in chat_data["players"]:
        chat_data["players"][uid_str] = {
            "username": display_name,
            "partidas_jugadas": 1,
            "mejores_tiempos": [duration],
            "mejores_movimientos": [moves]
        }
    else:
        player = chat_data["players"][uid_str]
        player["username"] = display_name
        player["partidas_jugadas"] += 1
        
        player["mejores_tiempos"].append(duration)
        player["mejores_tiempos"].sort()
        player["mejores_tiempos"] = player["mejores_tiempos"][:5]
        
        player["mejores_movimientos"].append(moves)
        player["mejores_movimientos"].sort()
        player["mejores_movimientos"] = player["mejores_movimientos"][:5]
        
    chat_data["global_top"].append({
        "user_id": user_id,
        "username": display_name,
        "moves": moves,
        "time": duration
    })
    chat_data["global_top"].sort(key=lambda x: (x["moves"], x["time"]))
    chat_data["global_top"] = chat_data["global_top"][:15]

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4, ensure_ascii=False)

# --- UTILERÍAS DE JUEGO ---
def format_time(seconds):
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    rem_seconds = seconds % 60
    if rem_seconds == 0:
        return f"{minutes}min"
    return f"{minutes}min {rem_seconds}s"

def calculate_completion_percentage(board):
    target = list(range(1, 16)) + [0]
    matches = sum(1 for a, b in zip(board, target) if a == b)
    return int((matches / 16) * 100)

def is_solvable(board):
    inversions = 0
    flat_board = [x for x in board if x != 0]
    for i in range(len(flat_board)):
        for j in range(i + 1, len(flat_board)):
            if flat_board[i] > flat_board[j]:
                inversions += 1
    blank_row = board.index(0) // 4
    return (inversions + blank_row) % 2 == 1

def generate_solvable_board():
    target = list(range(1, 16)) + [0]
    while True:
        board = list(range(1, 16)) + [0]
        random.shuffle(board)
        if board != target and is_solvable(board):
            return board

def is_solved(board):
    return board == list(range(1, 16)) + [0]

def build_keyboard(board, owner_id):
    keyboard = []
    for i in range(0, 16, 4):
        row = []
        for j in range(4):
            idx = i + j
            val = board[idx]
            text = " " if val == 0 else str(val)
            row.append(InlineKeyboardButton(text=text, callback_data=f"puzz_clk:{owner_id}:{idx}"))
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("🔄 Refrescar Tablero", callback_data=f"puzz_ref:{owner_id}")])
    return InlineKeyboardMarkup(keyboard)

# --- MANEJADORES DE COMANDOS ---

async def start_puzzle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    player_mention = f"@{user.username}" if user.username else f"*{user.first_name}*"
    
    is_direct_duel = False
    target_id = None
    target_mention = ""
    target_username = ""
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        if target_user.id != user.id:
            is_direct_duel = True
            target_id = target_user.id
            target_username = target_user.username or target_user.first_name
            target_mention = f"@{target_user.username}" if target_user.username else f"*{target_user.first_name}*"

    keyboard = [[InlineKeyboardButton("⚔️ Aceptar Desafío", callback_data=f"puzz_join:{user.id}")]]
    
    USER_GAMES[user.id] = {
        "host_username": user.username or user.first_name,
        "host_mention": player_mention,
        "is_lobby": True,
        "is_direct_duel": is_direct_duel,
        "target_id": target_id,
        "target_mention": target_mention,
        "target_username": target_username,
        "chat_id": chat_id
    }
    
    if is_direct_duel:
        lobby_text = (
            f"🎯 *DUELO DIRECTO ACTIVADO* 🎯\n\n"
            f"👤 Anfitrión: {player_mention}\n"
            f"⚔️ Desafiado: {target_mention}\n\n"
            f"El juego está congelado a la espera de que {target_mention} acepte el duelo.\n"
            f"_(Si sos el anfitrión, podés presionarlo para cancelar e iniciar Solo)_"
        )
    else:
        lobby_text = (
            f"🧩 *Lobby del Rompecabezas del 15*\n\n"
            f"👤 Anfitrión: {player_mention}\n"
            f"⚔️ Modo: Desafío Abierto\n\n"
            f"Presioná el botón de abajo para unirte al duelo. Si sos el anfitrión y nadie entra, podés jugar Solo."
        )
        
    await update.message.reply_text(text=lobby_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = load_stats()
    chat_id = update.effective_chat.id
    cid_str = str(chat_id)
    
    chat_data = stats.get(cid_str, {"global_top": [], "players": {}})
    global_top = chat_data.get("global_top", [])
    
    if not global_top:
        try:
            await context.bot.send_message(chat_id=chat_id, text="📉 Todavía no hay registros en el ranking de este chat. ¡Inaugurá el podio con /puzzgame!")
        except Exception: pass
        return
    
    global_top.sort(key=lambda x: (x["moves"], x["time"]))
    
    message = "🏆 *TOP 15 JUGADORES (ESTE CHAT)* 🏆\n\n"
    message += "Pos. | Jugador | Movimientos (Tiempo)\n"
    message += "----------------------------------------\n"
    
    for index, entry in enumerate(global_top[:15], start=1):
        username = entry.get("username", f"User_{entry.get('user_id')}")
        moves = entry.get("moves", 0)
        duration = entry.get("time", 0)
        
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"`{index}.`"
        message += f"{medal} *{username}* - {moves} movs ({format_time(duration)})\n"
        
    try:
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
    except Exception: pass

async def show_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = load_stats()
    chat_id = update.effective_chat.id
    cid_str = str(chat_id)
    
    chat_data = stats.get(cid_str, {"global_top": [], "players": {}})
    players = chat_data.get("players", {})
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        is_self = False
    else:
        target_user = update.effective_user
        is_self = True
        
    uid_str = str(target_user.id)
    name = target_user.first_name
    
    if uid_str not in players:
        text = "❌ No tenés estadísticas registradas en este chat." if is_self else f"❌ *{name}* no tiene estadísticas en este chat."
        await update.message.reply_text(text)
        return
        
    user_stats = players[uid_str]
    message = f"📊 *ESTADÍSTICAS DE {name.upper()} (ESTE CHAT)* 📊\n\n"
    message += f"🎮 Partidas finalizadas aquí: {user_stats.get('partidas_jugadas', 0)}\n\n"
    
    message += "⏱️ *Top 5 Mejores Tiempos:*\n"
    for i, t in enumerate(user_stats.get("mejores_tiempos", []), start=1):
        message += f"  {i}. {format_time(t)}\n"
        
    message += "\n🔢 *Top 5 Mejores Movimientos:*\n"
    for i, m in enumerate(user_stats.get("mejores_movimientos", []), start=1):
        message += f"  {i}. {m} movs\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

# --- CONTROLADOR INTERACTIVO CORE ---

async def handle_game_move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.effective_chat.id
    
    if query.data == "puzz_ignore":
        try: await query.answer()
        except Exception: pass
        return

    data = query.data.split(":")
    action = data[0]
    owner_id = int(data[1])
    current_user_id = query.from_user.id
    
    if action == "puzz_join":
        lobby_data = USER_GAMES.get(owner_id, {})
        if not lobby_data or not lobby_data.get("is_lobby", False):
            try: await query.answer("❌ Este lobby ya no está disponible.", show_alert=True)
            except Exception: pass
            return

        if current_user_id == owner_id:
            try: await query.answer()
            except Exception: pass
            
            shared_board = generate_solvable_board()
            start_t = time.time()
            player_mention = lobby_data["host_mention"]
            
            USER_GAMES[owner_id] = {
                "board": shared_board, "moves": 0, "start_time": start_t,
                "username": lobby_data["host_username"], "player_mention": player_mention, 
                "is_challenge": False, "chat_id": chat_id
            }
            
            try:
                await query.message.edit_text(
                    f"🧩 *Juego del 15*\n👤 {player_mention} jugando...\n🔢 Movs: 0  |  ⏰ Tiempo: 0s",
                    reply_markup=build_keyboard(shared_board, owner_id), parse_mode="Markdown"
                )
            except Exception: pass
            return
            
        else:
            if lobby_data.get("is_direct_duel", False):
                if current_user_id != lobby_data["target_id"]:
                    try: 
                        await query.answer(f"❌ ¡Duelo Privado! Solo {lobby_data['target_mention']} puede aceptar.", show_alert=True)
                    except Exception: pass
                    return

            try: await query.answer()
            except Exception: pass
            
            shared_board = generate_solvable_board()
            start_t = time.time()
            
            host_mention = lobby_data["host_mention"]
            host_username = lobby_data["host_username"]
            guest_mention = f"@{query.from_user.username}" if query.from_user.username else f"*{query.from_user.first_name}*"
            guest_username = query.from_user.username or query.from_user.first_name
            
            try:
                await query.message.edit_text(
                    f"⚔️ *¡Desafío del 15 Activado!* ⚔️\n\n🏃‍♂️ {host_mention} VS {guest_mention}\nLos tableros se desplegaron abajo 👇",
                    parse_mode="Markdown"
                )
            except Exception: pass
            
            msg_host = await context.bot.send_message(
                chat_id=chat_id,
                text=f"🧩 *Juego del 15* (Desafío)\n👤 {host_mention} jugando...\n🔢 Movs: 0  |  ⏰ Tiempo: 0s",
                reply_markup=build_keyboard(list(shared_board), owner_id), parse_mode="Markdown"
            )
            msg_guest = await context.bot.send_message(
                chat_id=chat_id,
                text=f"🧩 *Juego del 15* (Desafío)\n👤 {guest_mention} jugando...\n🔢 Movs: 0  |  ⏰ Tiempo: 0s",
                reply_markup=build_keyboard(list(shared_board), current_user_id), parse_mode="Markdown"
            )
            
            USER_GAMES[owner_id] = {
                "board": list(shared_board), "moves": 0, "start_time": start_t,
                "username": host_username, "player_mention": host_mention,
                "is_challenge": True, "opponent_id": current_user_id, "msg_id": msg_host.message_id, "chat_id": chat_id
            }
            USER_GAMES[current_user_id] = {
                "board": list(shared_board), "moves": 0, "start_time": start_t,
                "username": guest_username, "player_mention": guest_mention,
                "is_challenge": True, "opponent_id": owner_id, "msg_id": msg_guest.message_id, "chat_id": chat_id
            }
            return

    if current_user_id != owner_id:
        try: await query.answer()
        except Exception: pass
        return

    if owner_id not in USER_GAMES:
        try: await query.answer("❌ No tenés ninguna partida activa.", show_alert=True)
        except Exception: pass
        return

    try: await query.answer()
    except Exception: return

    game = USER_GAMES[owner_id]
    board = game["board"]
    player_mention = game["player_mention"]
    active_chat_id = game.get("chat_id", chat_id)
    
    if action == "puzz_ref":
        elapsed_time = int(time.time() - game["start_time"])
        try:
            await query.message.edit_text(
                f"🧩 *Juego del 15*\n👤 {player_mention} jugando...\n🔢 Movs: {game['moves']}  |  ⏰ Tiempo: {format_time(elapsed_time)}",
                reply_markup=build_keyboard(board, owner_id), parse_mode="Markdown"
            )
        except Exception: pass
        return

    clicked_idx = int(data[2])
    blank_idx = board.index(0)
    clicked_r, clicked_c = clicked_idx // 4, clicked_idx % 4
    blank_r, blank_c = blank_idx // 4, blank_idx % 4
    
    if abs(clicked_r - blank_r) + abs(clicked_c - blank_c) == 1:
        board[blank_idx], board[clicked_idx] = board[clicked_idx], board[blank_idx]
        game["moves"] += 1
    else:
        return

    elapsed_time = int(time.time() - game["start_time"])
    time_str = format_time(elapsed_time)

    if is_solved(board):
        save_victory_stats(active_chat_id, owner_id, game["username"], game["moves"], elapsed_time)
        
        def build_dead_keyboard(b):
            kb = []
            for i in range(0, 16, 4):
                kb.append([InlineKeyboardButton(text=" " if b[i+j]==0 else str(b[i+j]), callback_data="puzz_ignore") for j in range(4)])
            return InlineKeyboardMarkup(kb)

        if game.get("is_challenge"):
            opp_id = game["opponent_id"]
            opp_game = USER_GAMES.get(opp_id)
            
            try:
                await query.message.edit_text(
                    f"🎉 *¡Ganaste el Desafío!* 👑\n\n👤 {player_mention}\n"
                    f"🏆 Estado: *100% ordenado*\n🔢 Movs totales: {game['moves']}\n⏱️ Tiempo: {time_str}",
                    reply_markup=build_dead_keyboard(board), parse_mode="Markdown"
                )
            except Exception: pass
            
            opp_pct = 0
            if opp_game:
                opp_pct = calculate_completion_percentage(opp_game["board"])
                try:
                    await context.bot.edit_message_text(
                        chat_id=active_chat_id,
                        message_id=opp_game["msg_id"],
                        text=f"💀 *¡Perdiste el Desafío!* 🏁\n\n👤 {opp_game['player_mention']}\n"
                             f"📊 Tu progreso: *{opp_pct}% ordenado*\n🔢 Movs realizados: {opp_game['moves']}",
                        reply_markup=build_dead_keyboard(opp_game["board"]), parse_mode="Markdown"
                    )
                except Exception: pass
            
            summary_text = (
                f"🏁 *¡FIN DEL DESAFÍO DEL 15!* 🏁\n\n"
                f"👑 *GANADOR:* {player_mention}\n"
                f"├ 🔢 Movimientos: *{game['moves']} movs*\n"
                f"├ ⏱️ Tiempo utilizado: *{time_str}*\n"
                f"└ 📊 Progreso: *100% ordenado*\n\n"
                f"💀 *PERDEDOR:* {opp_game['player_mention'] if opp_game else 'Rival'}\n"
                f"├ 🔢 Movimientos hechos: *{opp_game['moves'] if opp_game else 0} movs*\n"
                f"└ 📊 Progreso final: *{opp_pct}% ordenado*"
            )
            
            try:
                await context.bot.send_message(chat_id=active_chat_id, text=summary_text, parse_mode="Markdown")
            except Exception: pass
            
            if opp_id in USER_GAMES:
                del USER_GAMES[opp_id]
        else:
            try:
                await query.message.edit_text(
                    f"🎉 *¡Felicitaciones, ganaste!* 👑\n\n👤 {player_mention} ordenó el tablero.\n🔢 Movs: {game['moves']}\n⏱️ Tiempo: {time_str}",
                    reply_markup=build_dead_keyboard(board), parse_mode="Markdown"
                )
            except Exception: pass
            
        del USER_GAMES[owner_id]
    else:
        try:
            await query.message.edit_text(
                f"🧩 *Juego del 15*\n👤 {player_mention} jugando...\n🔢 Movs: {game['moves']}  |  ⏰ Tiempo: {time_str}",
                reply_markup=build_keyboard(board, owner_id), parse_mode="Markdown"
            )
        except Exception: pass

# --- INICIALIZACIÓN CON WEBHOOKS (MODO WEB CLOUD) ---
async def start_bot():
    """Inicializa la aplicación y activa el Webhook dentro del loop activo."""
    load_stats()
    application = Application.builder().token(TOKEN).build()

    # Registro de manejadores
    application.add_handler(CommandHandler("puzzgame", start_puzzle))
    application.add_handler(CommandHandler("puzztop", show_top))
    application.add_handler(CommandHandler("puzzrank", show_rank))
    application.add_handler(CallbackQueryHandler(handle_game_move, pattern="^(puzz_)"))

    print(f"Configurando Webhook en puerto {PORT}...")
    
    # Inicializamos la app de forma asíncrona explícita
    await application.initialize()
    
    # Activamos el webhook esperando de forma asíncrona la respuesta de la API de Telegram
    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )
    
    # Iniciamos el servidor de la aplicación para que empiece a escuchar el puerto
    await application.start()
    print("Bot del Juego del 15 — Webhook en línea de forma segura.")
    
    # Mantenemos el proceso corriendo de forma infinita esperando los eventos
    while True:
        await asyncio.sleep(3600)

def main():
    """Función de entrada principal que inicializa el bucle de eventos correctamente."""
    try:
        # Forzamos la creación de un nuevo bucle de eventos limpio para el hilo principal
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_bot())
    except (KeyboardInterrupt, SystemExit):
        print("Bot detenido localmente.")

if __name__ == "__main__":
    main()
