import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import WebsocketConsumer
import contextlib
import random
import asyncio
import logging
import time
import threading
from asgiref.sync import sync_to_async
from .models import Paddle, Board, Ball, Game, CustomUser

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # or logging.ERROR for fewer logs

def outOfBounds(yPosition, player, board):
    return yPosition < 0 or yPosition + player > board

def ballOutOfBounds(yPosition, ball, board):
    return yPosition < 0 or yPosition + ball > board

waiting_queue = []
active_players = set()
game_states = {}
tournament_records = {}
tournament_ids = {}

# En un archivo nuevo, por ejemplo, game_state.py
class GameState:
    def __init__(self, user_id1, user_id2):
        self.board = Board(width=900, height=500)
        self.ball = Ball(board=self.board)
        self.player1 = Paddle(number=1, board=self.board, user_id=user_id1)
        self.player2 = Paddle(number=2, board=self.board, user_id=user_id2)
        self.game_loop_started = False
        self.running = True

    def reset(self):
        self.ball = Ball(board=self.board)
        self.player1.score = 0
        self.player2.score = 0
        self.running = True


class PongConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.user_id = int(self.scope['url_route']['kwargs']['userid'])
        self.user_id2 = int(self.scope['url_route']['kwargs']['userid2'])
        self.group_name = None
        self.player_1 = None
        self.player_2 = None
        self.player_number = None
        self.game_state = None
        self.ended = False
        self.is_tournament_game = False
        min_id = 0
        max_id = 0
        check = 0

        if self.user_id in active_players:
            await self.close()  # Close the WebSocket connection
            logger.info(f"Player {self.user_id} is already connected. Closing duplicate connection.")
            return
        if self.user_id2 == 0:
            active_players.add(self.user_id)
            waiting_queue.append(self)
            print(f'!!!!!! queue length = {len(waiting_queue)}', flush=True)
            self.user = await CustomUser.objects.aget(id=self.user_id)
            #self.user = CustomUser.objects.get(id=self.user_id)

            await self.accept()
            # if there are sufficient players start if not wait
            if len(waiting_queue) >= 2:
                    
                self.player_1 = waiting_queue.pop(0)
                self.player_2 = waiting_queue.pop(0)
                self.player_1.player_1 = self.player_1
                self.player_1.player_2 = self.player_2
                min_id = self.player_1.user_id
                max_id = self.player_2.user_id
                check = 1
        else:
            self.is_tournament_game = True
            min_id = self.user_id if self.user_id < self.user_id2 else self.user_id2
            max_id = self.user_id if self.user_id > self.user_id2 else self.user_id2
            if f"{min_id}+{max_id}" not in tournament_ids:
                tournament_ids[f"{min_id}+{max_id}"] = []
            print(f"TOURNMENT IDS: {tournament_ids}", flush=True)
            tournament_ids[f"{min_id}+{max_id}"].append(self)
            await self.accept()
            if len(tournament_ids[f"{min_id}+{max_id}"]) >= 2:
                print("INSIDE LEN >= 2!!!!!!!!!!!!!!!!!!!", flush=True)
                self.player_1 = tournament_ids[f"{min_id}+{max_id}"].pop(0)
                self.player_2 = tournament_ids[f"{min_id}+{max_id}"].pop(0)
                self.player_1.player_1 = self.player_1
                self.player_1.player_2 = self.player_2
                check = 1
        if check == 1:
            # Create unique identifier for game
            self.group_name = f'pong_game_{min_id}_{max_id}'
            self.player_1.game_state = GameState(user_id1=min_id, user_id2=max_id)
            self.player_2.game_state = self.player_1.game_state
            game_states[self.group_name] = self.player_1.game_state
            # Asign same room for players
            await self.player_1.start_game(self.group_name, 1)
            await self.player_2.start_game(self.group_name, 2)

#            await self.send(text_data=json.dumps({'message': 'Ws connextion established'}))

    async def start_game(self, group_name, player_number):
        print(self.channel_name, flush=True)
        self.group_name = group_name
        self.player_number = player_number
        #self.game_state = GameState()

        #game_states[group_name] = self.game_state

        # Add this player to room
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        print(f"!!!!!!Jugador {self.player_number} se unió a la sala: {self.group_name}!!!!!!", flush=True)

        if player_number == 1:# and not hasattr(self.game_state, 'game_loop_started'):
            print("INIZIALICING GAME OBJECTS", flush=True)
            self.game_state.board = Board(width=900, height=500)
            self.game_state.ball = Ball(board=self.game_state.board)
            self.game_state.player1 = Paddle(number=1, board=self.game_state.board, user_id=self.user_id)
            self.game_state.player2 = Paddle(number=2, board=self.game_state.board, user_id=self.player_2.user_id)
            
            self.game_state.game_loop_started = True
            asyncio.create_task(self.game_loop())
        self.running = True



    def ballSaved(self):
        if (self.game_state.ball.x + self.game_state.ball.velocityX <= self.game_state.player1.x + self.game_state.player1.width) and (self.game_state.ball.x >= self.game_state.player1.x) and \
                (self.game_state.player1.y <= self.game_state.ball.y <= self.game_state.player1.y + self.game_state.player1.height):
            paddle_center = self.game_state.player1.y + self.game_state.player1.height / 2
            hit_pos = (self.game_state.ball.y - paddle_center) / (self.game_state.player1.height / 2)
            self.game_state.ball.velocityY += hit_pos * 3  # Modify the vertical velocity
            
            self.game_state.ball.x = self.game_state.player1.x + self.game_state.player1.width + 1
            return True

        elif (self.game_state.ball.x + self.game_state.ball.velocityX >= self.game_state.player2.x - self.game_state.ball.width) and (self.game_state.ball.x <= self.game_state.player2.x) and \
                (self.game_state.player2.y <= self.game_state.ball.y <= self.game_state.player2.y + self.game_state.player2.height):
            paddle_center = self.game_state.player2.y + self.game_state.player2.height / 2
            hit_pos = (self.game_state.ball.y - paddle_center) / (self.game_state.player2.height / 2)
            self.game_state.ball.velocityY += hit_pos * 3
            
            self.game_state.ball.x = self.game_state.player2.x - self.game_state.ball.width - 1
            return True

        return False


    def move_players(self):
        if not outOfBounds(self.game_state.player1.y + self.game_state.player1.velocityY, self.game_state.player1.height, self.game_state.board.height):
            self.game_state.player1.y += self.game_state.player1.velocityY
        if not outOfBounds(self.game_state.player2.y + self.game_state.player2.velocityY, self.game_state.player1.height, self.game_state.board.height):
            self.game_state.player2.y += self.game_state.player2.velocityY
    
    def score(self):
        if self.game_state.ball.x >= self.game_state.board.width:
            self.game_state.player1.score += 1
            return True
        elif self.game_state.ball.x <= 0 - self.game_state.ball.width:
            self.game_state.player2.score += 1
            return True
        return False

    async def move_ball(self):
#        print("MOVE BALL CALLED", flush=True)
        #print("Before: ", self.game_state.ball.x, flush=True)
        #async with self.lock:  # Acquire the lock before modifying shared resources CHECK IF NEEDED
        if ballOutOfBounds(self.game_state.ball.y, self.game_state.ball.height, self.game_state.board.height):
            self.game_state.ball.velocityY = -self.game_state.ball.velocityY

        # Ensure that the ball has a minimum speed to avoid getting stuck
        if abs(self.game_state.ball.velocityX) < 5:
            self.game_state.ball.velocityX = 5 if self.game_state.ball.velocityX > 0 else -5

        if self.ballSaved():
            self.game_state.ball.velocityX = -self.game_state.ball.velocityX

        # Move the ball as usual
        self.game_state.ball.x += self.game_state.ball.velocityX
        self.game_state.ball.y += self.game_state.ball.velocityY

        
        #

        # Check if the ball is out of bounds to score
        if self.score():
            if self.game_state.player1.score == 7 or self.game_state.player2.score == 7:
                winner = 1 if self.game_state.player1.score == 7 else 2
                await self.update_game_stats(winner)
                position_updated = {
                    'Player1': self.game_state.player1.y,
                    'Player2': self.game_state.player2.y,
                    'ballX': self.game_state.ball.x,
                    'ballY': self.game_state.ball.y,
                    'Score1': self.game_state.player1.score,
                    'Score2': self.game_state.player2.score
                }
                self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'send_position',
                    'position': position_updated
                }
                )

                #Ends Game
                self.running = False
                self.ended = True
                #self.disconnect("game over") # TODO: when you restart the game it gets a bit weird so it has to be improved
            # Reset the ball after scoring
            self.game_state.ball = Ball(board=self.game_state.board)
        
    
    
    async def game_loop(self):
        print("GAME LOOP CALLED", flush=True)
        self.running = True
        while self.running:
            await self.move_ball()
            self.move_players()
            position_updated = {
                    'Player1': self.game_state.player1.y,
                    'Player2': self.game_state.player2.y,
                    'ballX': self.game_state.ball.x,
                    'ballY': self.game_state.ball.y,
                    'Score1': self.game_state.player1.score,
                    'Score2': self.game_state.player2.score
                }
            #print(f"Position: {position_updated}.\nPlayer {self.player_1.user_id}, Player number {self.player_number}", flush=True)
            #print(f'Player: {self.user_id}, ballx: {self.game_state.ball.x}', flush=True)
            #print(self.game_state.player1.y, flush=True)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'send_position',
                    'position': position_updated
                }
            )

            await asyncio.sleep(0.033)  # 0.016 -> Approx 60 FPS
            if self.ended:
                if self.is_tournament_game:
                    winner_id = self.game_state.player1.user_id if self.game_state.player1.score == 7 else self.game_state.player2.user_id
                    await self.notify_tournament_consumer(winner_id)
                await asyncio.sleep(1)
                await self.close()
                await self.player_2.close()
             
    
    async def disconnect(self, close_code):
        logger.info(f"Disconnected: {close_code}")
        self.running = False
        active_players.discard(self.user_id)
        #self.game_thread.join()  # Wait for the thread to finish before exiting
        if self.group_name:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        
        # Close the WebSocket connection
        await super().disconnect(close_code)

        # Remove game state if both players disconnect
        #if self.group_name in game_states and not any(player.running for player in [self.player_1, self.player_2]):
        #    del game_states[self.group_name]

    async def send_position(self, event):
        #print("SENDING POSITION", flush=True)
    #try:
        position = event['position']
        #print(f"POSITION {position}", flush=True)
        #print(f"scope type: {self.scope}", flush=True)
        if self.scope["type"] == "websocket" and self.channel_layer is not None:
            await self.send(text_data=json.dumps(position))
        else:
            print("Attempted to send message, but WebSocket is closed.", flush=True)
    #except Exception as e:
        #logger.error(f"Error sending position: {e}")

    async def receive(self, text_data):
        print("!!!!!RECIBIDO!!!", flush=True)
        try:
            text_data_json = json.loads(text_data)
            key = text_data_json['position']["key"]
            action = text_data_json['position']["action"]

            # Determinar qué jugador envió la actualización
            print(f"\033[91mPlayer number : {self.player_number}\033[0m", flush=True)
            print(f"\033[91mKey : {key}\033[0m", flush=True)
            print(f"\033[91mAction : {action}\033[0m", flush=True)
            player = self.game_state.player1 if self.player_number == 1 else self.game_state.player2
        
            if action == "move":
                if key == "ArrowUp":
                    player.velocityY = -10
                elif key == "ArrowDown":
                    player.velocityY = 10
            else:
                player.velocityY = 0

            position_updated = {
                    'Player1': self.game_state.player1.y,
                    'Player2': self.game_state.player2.y,
                    'ballX': self.game_state.ball.x,
                    'ballY': self.game_state.ball.y,
                    'Score1': self.game_state.player1.score,
                    'Score2': self.game_state.player2.score
                }
            await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'send_position',
                'position': position_updated
            }
        )
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON: %s", e)
        except Exception as e:
            logger.error("Unexpected error: %s", e)

    #need sync_to_async() decorator to convert the synchronous database operation into an asynchronous operation that can be executed within a WebSockets context.
    async def update_game_stats(self, winner):

        print(f"\033[96mUPDATE_GAME_STATS CALLED, winner : {winner}\033[0m", flush=True)
        player1_user = await sync_to_async(CustomUser.objects.get)(id=self.game_state.player1.user_id)
        player2_user = await sync_to_async(CustomUser.objects.get)(id=self.game_state.player2.user_id)

        player1_stats = player1_user.game_stats
        player1_stats['total'] = player1_stats.get('total', 0) + 1
        if winner == 1:
            player1_stats['wins'] = player1_stats.get('wins', 0) + 1
        else:
            player1_stats['losses'] = player1_stats.get('losses', 0) + 1
        player1_user.game_stats = player1_stats
        await sync_to_async(player1_user.save)()

        player2_stats = player2_user.game_stats
        player2_stats['total'] = player2_stats.get('total', 0) + 1
        if winner == 2:
            player2_stats['wins'] = player2_stats.get('wins', 0) + 1
        else:
            player2_stats['losses'] = player2_stats.get('losses', 0) + 1
        player2_user.game_stats = player2_stats
        await sync_to_async(player2_user.save)()

    async def notify_tournament_consumer(self, winner_id):
        """Envia mensaje al TournamentConsumer cuando termina una partida."""

        # Buscar el nombre del torneo en tournament_records
        tournament_name = None
        for name, players in tournament_records.items():
            if any(player.user_id == self.user_id or player.user_id == self.user_id2 for player in players):
                tournament_name = name
                print(f"\033[96mTOURNAMENT NAME FOUND({tournament_name}),about to send to TC\033[0m", flush=True)
                break
        
        if not tournament_name:
            print("No se encontró el torneo correspondiente en tournament_records")
            return

        # Definir el grupo de torneo usando el nombre del torneo encontrado
        tournament_group = f"tournament_{tournament_name}"
        
        # Obtener los IDs de los jugadores
        min_id = min(self.game_state.player1.user_id, self.game_state.player2.user_id)
        max_id = max(self.game_state.player1.user_id, self.game_state.player2.user_id)

        # Enviar el mensaje de que la partida ha finalizado
        await self.channel_layer.group_send(
            tournament_group,
            {
                'type': 'match_finished',
                'match_info': {
                    'winner_id': winner_id,
                    'loser_id': self.game_state.player2.user_id if winner_id == self.game_state.player1.user_id else self.game_state.player1.user_id,
                    'match_players': [min_id, max_id]
                }
            }
        )


class TournamentConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.tournament_name = self.scope['url_route']['kwargs']['tournament']
        self.user_id = int(self.scope['url_route']['kwargs']['userid'])
        self.group_name = None
        print(f"\033[96muUSER: {self.user_id} , TOURNAMENT_GAME: {self.tournament_name} CONNECTED\033[0m", flush=True)

        # Inicializar el torneo si no existe en el registro
        if self.tournament_name not in tournament_records:
            tournament_records[self.tournament_name] = []

        # Verificar si el usuario ya está en el torneo
        if self.user_id in [player.user_id for player in tournament_records[self.tournament_name]]:
            await self.close()
            return

        # Añadir el consumidor actual al registro del torneo
        tournament_records[self.tournament_name].append(self)

        # Aceptar la conexión WebSocket
        await self.accept()

        # Si hay 4 jugadores, iniciar las dos partidas(el 4 es el que inicia el torneo)
        if len(tournament_records[self.tournament_name]) == 4:
            # Inicializa el grupo de torneo para recibir mensajes de los juegos
            self.tournament_group_name = f"tournament_{self.tournament_name}"
            await self.channel_layer.group_add(self.tournament_group_name, self.channel_name)
            await self.start_tournament()

        elif len(tournament_records[self.tournament_name]) > 4:
            print(f"Tournament {self.tournament_name} is already full.")
            await self.close()
            return

    async def start_tournament(self):
        players = tournament_records[self.tournament_name]
        print("Starting matches for tournament:", self.tournament_name, flush=True)

        # Emparejamiento de los 4 jugadores
        self.match_1 = (players[0], players[1])
        self.match_2 = (players[2], players[3])

        # Iniciar la primera ronda
        await self.start_match(self.match_1, False)
        await self.start_match(self.match_2, False)

    async def start_match(self, match, is_final):
        """Iniciar una partida entre dos jugadores."""
        player1, player2 = match
        game_group = f"match_{player1.user_id}_{player2.user_id}"

        # Añadir ambos jugadores al grupo del canal
        await self.channel_layer.group_add(game_group, player1.channel_name)
        await self.channel_layer.group_add(game_group, player2.channel_name)

        if is_final:
            await self.channel_layer.group_send(
                game_group,
                {
                    'type': 'game_start',
                    'message': f"Final match between {player1} and {player2} is starting!"
                }
            )
        else:
            await self.channel_layer.group_send(
                game_group,
                {
                    'type': 'game_start',
                    'message': f"Match between {player1.user_id} and {player2.user_id} is starting!"
                }
            )

    async def game_start(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'message': message}))

    async def match_finished(self, event):
        match_info = event['match_info']
        winner_id = match_info['winner_id']
        loser_id = match_info['loser_id']
        match_players = match_info['match_players']

        print(f"Partida entre {match_players} ha terminado. Ganador: {winner_id}", flush=True)

        # Guarda el ganador y llama a los métodos correspondientes según la lógica del torneo
        if match_players == [self.match_1[0].user_id, self.match_1[1].user_id]:
            self.winner_match_1 = winner_id
        elif match_players == [self.match_2[0].user_id, self.match_2[1].user_id]:
            self.winner_match_2 = winner_id
        # Si ambos ganadores de la primera ronda están listos, comienza la partida final
        if hasattr(self, 'winner_match_1') and hasattr(self, 'winner_match_2'):
            await self.start_match((self.winner_match_1, self.winner_match_2, True))

    async def end_match(self, match, winner):
        """Finalizar una partida, actualiza los ganadores."""
        player1, player2 = match
        game_group = f"match_{player1.user_id}_{player2.user_id}"

        # Quitar los jugadores del grupo del canal
        await self.channel_layer.group_discard(game_group, player1.channel_name)
        await self.channel_layer.group_discard(game_group, player2.channel_name)

        # Registrar el ganador y preparar para la final si ambas partidas han terminado
        if match == self.match_1:
            self.winner_match_1 = winner
        elif match == self.match_2:
            self.winner_match_2 = winner

        # Iniciar la partida final si los dos ganadores están listos
        if hasattr(self, 'winner_match_1') and hasattr(self, 'winner_match_2'):
            await self.start_match((self.winner_match_1, self.winner_match_2))

    async def end_tournament(self, winner_id):
        """Finaliza el torneo actual, actualizando estadísticas y cerrando conexiones."""
        print(f"Tournament {self.tournament_name} finished. Winner: {winner_id}")

        # Actualizar las estadísticas del torneo para el ganador
        await self.update_tournament_stats(winner_id)

        # Cerrar todas las conexiones de los jugadores
        for player in tournament_records[self.tournament_name]:
            await player.close()

        # Eliminar el torneo del registro
        del tournament_records[self.tournament_name]

    async def update_tournament_stats(self, winner):

        print(f"\033[96mUPDATE_TOURNAMENT_STATS CALLED, winner : {winner}\033[0m", flush=True)
        player_user = await sync_to_async(CustomUser.objects.get)(id=self.user_id)
        player_stats = player_user.tournament_stats
        player_stats['total'] = player_stats.get('total', 0) + 1

        if winner:
            player_stats['wins'] = player_stats.get('wins', 0) + 1

        player_user._stats = player_stats
        await sync_to_async(player_user.save)()

    async def disconnect(self, close_code):
        """Maneja la desconexión de un usuario."""
        if self.tournament_name in tournament_records:
            tournament_records[self.tournament_name] = [
                player for player in tournament_records[self.tournament_name] if player.user_id != self.user_id
            ]

        await super().disconnect(close_code)

#    def ballSaved(self):
#        if (self.game_state.ball.x + self.game_state.ball.velocityX <= self.game_state.player1.x + self.game_state.player1.width) and (self.game_state.ball.x >= self.game_state.player1.x) and \
#                (self.game_state.player1.y <= self.game_state.ball.y <= self.game_state.player1.y + self.game_state.player1.height):
#            paddle_center = self.game_state.player1.y + self.game_state.player1.height / 2
#            hit_pos = (self.game_state.ball.y - paddle_center) / (self.game_state.player1.height / 2)
#            self.game_state.ball.velocityY += hit_pos * 3  # Modify the vertical velocity
#            
#            self.game_state.ball.x = self.game_state.player1.x + self.game_state.player1.width + 1
#            return True
#
#        elif (self.game_state.ball.x + self.game_state.ball.velocityX >= self.game_state.player2.x - self.game_state.ball.width) and (self.game_state.ball.x <= self.game_state.player2.x) and \
#                (self.game_state.player2.y <= self.game_state.ball.y <= self.game_state.player2.y + self.game_state.player2.height):
#            paddle_center = self.game_state.player2.y + self.game_state.player2.height / 2
#            hit_pos = (self.game_state.ball.y - paddle_center) / (self.game_state.player2.height / 2)
#            self.game_state.ball.velocityY += hit_pos * 3
#            
#            self.game_state.ball.x = self.game_state.player2.x - self.game_state.ball.width - 1
#            return True
#
#        return False
#
#
#    def move_players(self):
#        if not outOfBounds(self.game_state.player1.y + self.game_state.player1.velocityY, self.game_state.player1.height, self.game_state.board.height):
#            self.game_state.player1.y += self.game_state.player1.velocityY
#        if not outOfBounds(self.game_state.player2.y + self.game_state.player2.velocityY, self.game_state.player1.height, self.game_state.board.height):
#            self.game_state.player2.y += self.game_state.player2.velocityY
#    
#    def score(self):
#        if self.game_state.ball.x >= self.game_state.board.width:
#            self.game_state.player1.score += 1
#            return True
#        elif self.game_state.ball.x <= 0 - self.game_state.ball.width:
#            self.game_state.player2.score += 1
#            return True
#        return False
#
#    async def move_ball(self):
##        print("MOVE BALL CALLED", flush=True)
#        #print("Before: ", self.game_state.ball.x, flush=True)
#        #async with self.lock:  # Acquire the lock before modifying shared resources CHECK IF NEEDED
#        if ballOutOfBounds(self.game_state.ball.y, self.game_state.ball.height, self.game_state.board.height):
#            self.game_state.ball.velocityY = -self.game_state.ball.velocityY
#
#        # Ensure that the ball has a minimum speed to avoid getting stuck
#        if abs(self.game_state.ball.velocityX) < 5:
#            self.game_state.ball.velocityX = 5 if self.game_state.ball.velocityX > 0 else -5
#
#        if self.ballSaved():
#            self.game_state.ball.velocityX = -self.game_state.ball.velocityX
#
#        # Move the ball as usual
#        self.game_state.ball.x += self.game_state.ball.velocityX
#        self.game_state.ball.y += self.game_state.ball.velocityY
#
#        
#        #
#
#        # Check if the ball is out of bounds to score
#        if self.score():
#            if self.game_state.player1.score == 7 or self.game_state.player2.score == 7:
#                winner = 1 if self.game_state.player1.score == 7 else 2
#                await self.update_game_stats(winner)
#                position_updated = {
#                    'Player1': self.game_state.player1.y,
#                    'Player2': self.game_state.player2.y,
#                    'ballX': self.game_state.ball.x,
#                    'ballY': self.game_state.ball.y,
#                    'Score1': self.game_state.player1.score,
#                    'Score2': self.game_state.player2.score
#                }
#                self.channel_layer.group_send(
#                self.group_name,
#                {
#                    'type': 'send_position',
#                    'position': position_updated
#                }
#                )
#
#                #Ends Game
#                self.running = False
#                self.ended = True
#                #self.disconnect("game over") # TODOs: when you restart the game it gets a bit weird so it has to be improved
#            # Reset the ball after scoring
#            self.game_state.ball = Ball(board=self.game_state.board)
#        
#    
## TENEMOS QUE ADAPATAR EL GAME_LOOP A LA LOGICA DEL CONSUMER DE LOS TORNEOS!! AHORA LO GESTIONA EL 4 CONSUMER. VA A HABER 2 GAMELOOPS AL MISMO TIEMPO,
## LOS GESTIONA TODOS EL 4 O UNO EL  Y OTRO EL 2? !!! HAY VARIABLES DE LAS FUNCIONES AÑADIDAS DESPUES DE SELF.DISCONNECT QUE NO TIENE ESTE CONSUMER!!ADAPTAR!!
## FALTA INICIALIZAR LOS GAME_STATES(BASADOS EN EL GROUP_NAME) Y TENERLOS EN CUENTA PARA ELIMINARLOS CUANDO NO HAGAN FALTA. AL HABER 3 GAME_STATES,
## SE PODRIA CREAR UN DICCIONARIO EN SELF QUE TENGA MATCH1_GAMESTATE, MATCH2_GAMESTATE Y FINAL_GAMESTATE
#    async def game_loop(self):
#        print("GAME LOOP CALLED", flush=True)
#        self.running = True
#        while self.running:
#            await self.move_ball()
#            self.move_players()
#            position_updated = {
#                    'Player1': self.game_state.player1.y,
#                    'Player2': self.game_state.player2.y,
#                    'ballX': self.game_state.ball.x,
#                    'ballY': self.game_state.ball.y,
#                    'Score1': self.game_state.player1.score,
#                    'Score2': self.game_state.player2.score
#                }
#
#            await self.channel_layer.group_send(
#                self.group_name,
#                {
#                    'type': 'send_position',
#                    'position': position_updated
#                }
#            )
#
#            await asyncio.sleep(0.033)  # 0.016 -> Approx 60 FPS
#            if self.ended:
#                await asyncio.sleep(1)
#                await self.close()
#                await self.player_2.close()
#
#
#    async def send_position(self, event):
#        try:
#            position = event['position']
#            if self.scope["type"] == "websocket" and self.channel_layer is not None:
#                await self.send(text_data=json.dumps(position))
#            else:
#                print("Attempted to send message, but WebSocket is closed.")
#        except Exception as e:
#            logger.error(f"Error sending position: {e}")

# ESTA FUNCION NO TIENE SENTIDO POR QUESE GESTIONAN VARIAS PARTIDAS, NO HAY SELF.PLAYER_NUMBER, HAY QUE DETERMINAR QUIEN MANDO EL MENSAJE DE OTRA MANERA
    async def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'end_tournament':
            winner_id = data['winner_id']
            await self.end_tournament(winner_id)
        #print("!!!!!RECIBIDO!!!", flush=True)
#        try:
#            text_data_json = json.loads(text_data)
#            key = text_data_json['position']["key"]
#            action = text_data_json['position']["action"]
#
#            # Determinar qué jugador envió la actualización
#            print(f"\033[91mPlayer number : {self.player_number}\033[0m", flush=True)
#            print(f"\033[91mKey : {key}\033[0m", flush=True)
#            print(f"\033[91mAction : {action}\033[0m", flush=True)
#            player = self.game_state.player1 if self.player_number == 1 else self.game_state.player2
#        
#            if action == "move":
#                if key == "ArrowUp":
#                    player.velocityY = -10
#                elif key == "ArrowDown":
#                    player.velocityY = 10
#            else:
#                player.velocityY = 0
#
#            position_updated = {
#                    'Player1': self.game_state.player1.y,
#                    'Player2': self.game_state.player2.y,
#                    'ballX': self.game_state.ball.x,
#                    'ballY': self.game_state.ball.y,
#                    'Score1': self.game_state.player1.score,
#                    'Score2': self.game_state.player2.score
#                }
#            await self.channel_layer.group_send(
#            self.group_name,
#            {
#                'type': 'send_position',
#                'position': position_updated
#            }
#        )
#        except json.JSONDecodeError as e:
#            logger.error("Failed to parse JSON: %s", e)
#        except Exception as e:
#            logger.error("Unexpected error: %s", e)