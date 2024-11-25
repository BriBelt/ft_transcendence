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
from .models import Tournament, Paddle, Board, Ball, Game, CustomUser

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # or logging.ERROR for fewer logs

def outOfBounds(yPosition, player, board):
    return yPosition < 0 or yPosition + player > board

def ballOutOfBounds(yPosition, ball, board):
    return yPosition < 0 or yPosition + ball > board

waiting_queue = []
tournament_queue = {}
tournament_queue_ids = {}
tournament_lost = {} 
waiting_ids = []
active_players = []
game_states = {}
running_games = {}
tournament_records = {}
connected_users = {}

# En un archivo nuevo, por ejemplo, game_state.py
class GameState:
    def __init__(self, user_id1, user_id2, player_1, player_2):
        self.board = Board(width=900, height=500)
        self.ball = Ball(board=self.board)
        self.player1 = Paddle(number=1, board=self.board, user_id=user_id1)
        self.player2 = Paddle(number=2, board=self.board, user_id=user_id2)
        self.consumer_1 = player_1
        self.consumer_1_id = user_id1
        self.consumer_2 = player_2
        self.consumer_2_id = user_id2
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
        try:
            self.tournament_name = self.scope['url_route']['kwargs']['tournament']
        except:
            self.tournament_name = None
        user_connected = connected_users.get(self.user_id)
        self.group_name = None
        self.player_1 = None
        self.player_2 = None
        self.player_number = None
        self.game_state = None
        self.ended = False
        self.is_tournament_game = True if self.tournament_name and len(self.tournament_name) > 0 else False
        min_id = 0
        max_id = 0
        check = 0

        if int(self.user_id) in waiting_ids:
            print("User already logged in", flush=True)
            await self.close()
            return
        if self.is_tournament_game and self.tournament_name in tournament_queue_ids and self.user_id in tournament_queue_ids[self.tournament_name]:
            print("User already logged in", flush=True)
            await self.close()
            return
        if self.is_tournament_game and self.tournament_name in tournament_lost and self.user_id in tournament_lost[self.tournament_name]:
            print("User already disqualified from the tournament", flush=True)
            await self.close()
            return
        print(f"Users that lost: {tournament_lost}", flush=True)
        if len(game_states) > 0:
            for key in game_states.keys():
                print(f"KEY: {key}", flush=True)
                ids = key.split('_')
                if int(self.user_id) == int(ids[2]) or int(self.user_id) == int(ids[3]):
                    self.group_name = key
                    print(f"Game found: {self.group_name}", flush=True)
        print(f"SUPER DEBUG: {self.user_id}, {active_players}, {user_connected} and {self.group_name}", flush=True)
        if (int(self.user_id) in active_players and user_connected) or self.group_name:
            print(f"Reconnecting player {self.user_id} to existing game: {self.group_name}", flush=True)
            # Reconnect to the existing group
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            game_state = game_states.get(self.group_name)
            print(f'Game State {game_state}', flush=True)
            if game_state:
                position_updated = {
                        'Player1': game_state.player1.y,
                        'Player2': game_state.player2.y,
                        'ballX': game_state.ball.x,
                        'ballY': game_state.ball.y,
                        'Score1': game_state.player1.score,
                        'Score2': game_state.player2.score
                    }
            else:
                active_players.append(int(self.user_id))
                waiting_queue.append(self)
                waiting_ids.append(int(self.user_id))
                print(f'!!!!!! queue length = {len(waiting_queue)}', flush=True)
                self.user = await CustomUser.objects.aget(id=self.user_id)
                #self.user = CustomUser.objects.get(id=self.user_id)

                await self.accept()

                connected_users[self.user_id] = self.group_name

                return

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'send_position',
                    'position': position_updated
                }
            )
            # if game_state.consumer_1 == None and game_state.consumer_2 == None:
            #   return
            if game_state.consumer_1_id == self.user_id:
                self.player_1 = self
                self.player_2 = game_state.consumer_2
                game_state.consumer_1 = self
                self.player_number = 1
                self.player_1.game_state = game_state
                self.player_2.game_state = self.player_1.game_state
            elif game_state.consumer_2_id == self.user_id:
                self.player_1 = game_state.consumer_1
                self.player_2 = self
                game_state.consumer_2 = self
                self.player_number = 2
                self.player_1.game_state = game_state
                self.player_2.game_state = self.player_1.game_state
            #if not game_state.game_loop_started:
            await self.player_1.start_game(self.group_name, 1)
            await self.player_2.start_game(self.group_name, 2)
            #check = 1
            return
        elif self.is_tournament_game == False:
            active_players.append(int(self.user_id))
            waiting_queue.append(self)
            waiting_ids.append(int(self.user_id))
            print(f'!!!!!! queue length = {len(waiting_queue)}', flush=True)
            self.user = await CustomUser.objects.aget(id=self.user_id)
            #self.user = CustomUser.objects.get(id=self.user_id)

            await self.accept()
            # if there are sufficient players start if not wait
            if len(waiting_queue) == 2:
                    
                self.player_1 = waiting_queue.pop(0)
                self.player_2 = waiting_queue.pop(0)
                waiting_ids.pop(0)
                waiting_ids.pop(0)
                self.player_1.player_1 = self.player_1
                self.player_1.player_2 = self.player_2
                min_id = self.player_1.user_id
                max_id = self.player_2.user_id
                check = 1
        else:
            active_players.append(int(self.user_id))
            if not self.tournament_name in tournament_queue:
                tournament_queue[self.tournament_name] = []
            tournament_queue[self.tournament_name].append(self)
            if not self.tournament_name in tournament_queue_ids:
                tournament_queue_ids[self.tournament_name] = []
            tournament_queue_ids[self.tournament_name].append(int(self.user_id))
            print(f'!!!!!! queue length = {len(tournament_queue[self.tournament_name])}', flush=True)
            self.user = await CustomUser.objects.aget(id=self.user_id)
            #self.user = CustomUser.objects.get(id=self.user_id)

            await self.accept()
            # if there are sufficient players start if not wait
            if len(tournament_queue[self.tournament_name]) == 2:
                    
                self.player_1 = tournament_queue[self.tournament_name].pop(0)
                self.player_2 = tournament_queue[self.tournament_name].pop(0)
                tournament_queue_ids[self.tournament_name].pop(0)
                tournament_queue_ids[self.tournament_name].pop(0)
                self.player_1.player_1 = self.player_1
                self.player_1.player_2 = self.player_2
                min_id = self.player_1.user_id
                max_id = self.player_2.user_id
                check = 1
        connected_users[self.user_id] = self.group_name
        if check == 1:
            # Create unique identifier for game
            self.group_name = f'pong_game_{min_id}_{max_id}'
            #running_games[self.group_name].append(self.player_1)
            #running_games[self.group_name].append(self.player_2)
            self.player_1.game_state = GameState(user_id1=min_id, user_id2=max_id, player_1=self.player_1, player_2=self.player_2)
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

        # Share usernames to anounce them
        if player_number == 2 and self.is_tournament_game:
            player1_user = await sync_to_async(CustomUser.objects.get)(id=self.player_1.user_id)
            player2_user = await sync_to_async(CustomUser.objects.get)(id=self.player_2.user_id)
            print(f"\033[33mABOUT TO SEND ANOUNCEMENT!!\033[0m", flush=True)

            await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "announce_players",
                "player1_username": player1_user.username,
                "player2_username": player2_user.username,
            }
            )

        if player_number == 1 and not self.game_state.game_loop_started:# and not hasattr(self.game_state, 'game_loop_started'):
            if not self.game_state.board:
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
            if self.game_state.player1.score >= 7 or self.game_state.player2.score >= 7:
                winner = 1 if self.game_state.player1.score >= 7 else 2
                await self.update_game_stats(winner)
                if self.is_tournament_game and self.tournament_name in tournament_lost and len(tournament_lost[self.tournament_name]) == 3:
                    if winner == 1:
                        winner_id = self.player_1.user_id
                    else:
                        winner_id = self.player_2.user_id
                    await self.update_tournament_stats(winner_id)
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
        await asyncio.sleep(2)
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
                """
                if self.is_tournament_game and self.tournament_name in tournament_lost and len(tournament_lost[self.tournament_name]) == 3:
                    winner_id = self.game_state.player1.user_id if self.game_state.player1.score >= 7 else self.game_state.player2.user_id
                    await self.update_tournament_stats(winner_id)
                """
                await asyncio.sleep(1)
                await self.close()
                await self.player_2.close()
             
    
    async def disconnect(self, close_code):
        print(f"Disconnected: {close_code}", flush=True)
        if self.is_tournament_game:
            try:
                tournament_queue_ids[self.tournament_name].remove(self.user_id)
            except:
                print(f"User_id {self.user_id} not in list {tournament_queue_ids[self.tournament_name]}", flush=True)
            try:
                tournament_queue[self.tournament_name].remove(self)
            except:
                print(f"Consumer {self.user_id} not in list {tournament_queue[self.tournament_name]}", flush=True)
        else:
            try:
                waiting_ids.remove(self.user_id)
            except:
                print(f"User_id {self.user_id} not in list {waiting_ids}", flush=True)
            try:
                waiting_queue.remove(self)
            except:
                print(f"Consumer {self.user_id} not in list {waiting_queue}", flush=True)
        """
        if self.game_state and self.user_id == self.game_state.consumer_1_id:
            self.game_state.consumer_1 = None
        elif self.game_state and self.user_id == self.game_state.consumer_2_id:
            self.game_state.consumer_2 = None
        """
        # active_players.discard(self.user_id)
        #self.game_thread.join()  # Wait for the thread to finish before exiting
        if self.group_name:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            if self.game_state.player1.score > 6 or self.game_state.player2.score > 6:
                print("GameState deleted", flush=True)
                active_players.remove(self.user_id)
                connected_users.pop(self.user_id, None)
                if self.group_name in game_states:
                    game_states.pop(self.group_name, None)
        
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

    async def announce_players(self, event):
        await self.send(text_data=json.dumps({
            "type": "announcement",
            "message": f"Tournament Match between {event['player1_username']} and {event['player2_username']} is about to begin!",
            "player1_username": event["player1_username"],
            "player2_username": event["player2_username"],
        }))


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
            if self.is_tournament_game:
                if not self.tournament_name in tournament_lost:
                    tournament_lost[self.tournament_name] = []
                tournament_lost[self.tournament_name].append(self.game_state.player2.user_id)
                await self.player_2.send(text_data=json.dumps({'message': 'Tournament is over'}))
                await self.send(text_data=json.dumps({'message': f'Winner {self.game_state.player1.user_id}'}))
                await self.player_2.send(text_data=json.dumps({'message': f'Winner {self.game_state.player1.user_id}'}))
                player2_user.user_in_online_game = False
            else:
                player1_user.user_in_online_game = False
                player2_user.user_in_online_game = False
        else:
            player1_stats['losses'] = player1_stats.get('losses', 0) + 1
            if self.is_tournament_game:
                if not self.tournament_name in tournament_lost:
                    tournament_lost[self.tournament_name] = []
                tournament_lost[self.tournament_name].append(self.game_state.player1.user_id)
                await self.send(text_data=json.dumps({'message': 'Tournament is over'}))
                await self.send(text_data=json.dumps({'message': f'Winner {self.game_state.player2.user_id}'}))
                await self.player_2.send(text_data=json.dumps({'message': f'Winner {self.game_state.player2.user_id}'}))
                player1_user.user_in_online_game = False
            else:
                player1_user.user_in_online_game = False
                player2_user.user_in_online_game = False
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

    async def update_tournament_stats(self, winner_id):

        print(f"\033[96mUPDATE_TOURNAMENT_STATS CALLED, winner_id : {winner_id}\033[0m", flush=True)
        player_user = await sync_to_async(CustomUser.objects.get)(id=winner_id)
        current_tournament = await sync_to_async(Tournament.objects.get)(name=self.tournament_name)
        current_tournament.finished = True
        player_stats = player_user.tournament_stats
        player_stats['total'] = player_stats.get('total', 0) + 1

        if winner_id:
            player_stats['wins'] = player_stats.get('wins', 0) + 1

        player_user._stats = player_stats
        await self.send(text_data=json.dumps({'message': 'Tournament is over'}))
        await self.player_2.send(text_data=json.dumps({'message': 'Tournament is over'}))
        await sync_to_async(current_tournament.save)()
        await sync_to_async(player_user.save)()



class TournamentConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.tournament_name = self.scope['url_route']['kwargs']['tournament']
        self.user_id = int(self.scope['url_route']['kwargs']['userid'])
        self.group_name = None
        self.final_started = False
        print(f"\033[96muUSER: {self.user_id} , TOURNAMENT_GAME: {self.tournament_name} CONNECTED\033[0m", flush=True)

        if len(tournament_ids) > 0:
            for key in tournament_ids.keys():
                print(f"KEY: {key}", flush=True)
                ids = key.split('_')
                if int(self.user_id) == int(ids[0]) or int(self.user_id) == int(ids[1]):
                    self.group_name = key
        # Inicializar el torneo si no existe en el registro
        if self.tournament_name not in tournament_records:
            tournament_records[self.tournament_name] = []

        # Verificar si el usuario ya está en el torneo
        if self.user_id not in [player.user_id for player in tournament_records[self.tournament_name]]:
            
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
        print(f"\033[92mEMPEZANDO PARTIDA\033[0m", flush=True)
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
                    'message': f"Final match between {player1.user_id} and {player2.user_id} is starting!"
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

        print(f"\033[96mPartida entre {match_players} ha terminado. Ganador: {winner_id}\033[0m", flush=True)
        # Busca la instancia del ganador
        players = tournament_records[self.tournament_name]
        print(f"Players in tournament_records[{self.tournament_name}]: {[player.user_id for player in players]}")

        winner_instance = next((player for player in players if player.user_id == winner_id), None)

        # Verifica si se encontró el ganador
        if winner_instance is None:
            print(f"\033[91mNo se encontró una instancia para el ganador con user_id {winner_id}\033[0m", flush=True)
        else:
            print(f"\033[92mGanador encontrado: {winner_instance.user_id}\033[0m", flush=True)

        # Guarda el ganador y llama a los métodos correspondientes según la lógica del torneo
        # Comparar match_players con los IDs de manera más robusta para evitar errores de orden
        match_1_ids = sorted([self.match_1[0].user_id, self.match_1[1].user_id])
        match_2_ids = sorted([self.match_2[0].user_id, self.match_2[1].user_id])
        sorted_match_players = sorted(match_players)

        if sorted_match_players == match_1_ids:
            self.winner_match_1 = winner_instance
        elif sorted_match_players == match_2_ids:
            self.winner_match_2 = winner_instance
        # Si ambos ganadores de la primera ronda están listos, comienza la partida final
        if hasattr(self, 'winner_match_1') and hasattr(self, 'winner_match_2') and not self.final_started:
            print("\033[96mA punto de empezar la final\033[0m", flush=True)
            self.final_started = True
            await self.start_match((self.winner_match_1, self.winner_match_2), True)

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
        print(f"Tournament {self.tournament_name} finished. Winner: {winner_id}, self.user_id = {self.user_id}.", flush=True)

        if winner_id == self.user_id:
            # Actualizar las estadísticas del torneo para el ganador
            print(f"\033[96mABOUT TO CALL UPDATE_TOURNAMENT_STATS BROOO\033[0m", flush=True)
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


    async def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'end_tournament':
            winner_id = int(data['winner_id'])
            await self.end_tournament(winner_id)