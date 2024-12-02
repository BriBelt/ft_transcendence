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
from django.utils import timezone
from .models import Tournament, Paddle, Board, Ball, Game, CustomUser
from django.utils import timezone
import jwt
from django.conf import settings
from django.utils.timezone import now

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
tournament_wins = {} 
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
        token = self.scope['url_route']['kwargs']['token']

        try:
        # Decodificar el token usando el SECRET_KEY
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            self.user_id = payload.get("id")  # Obtener el user_id del payload
        
            if not self.user_id:
                raise jwt.InvalidTokenError("Invalid user_id in token")

        except (ExpiredSignatureError, InvalidTokenError):
            await self.accept()  # Acepta la conexión antes de enviar un mensaje
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "authentication_failed"
            }))
            await self.close()
            return

        #self.user_id = int(self.scope['url_route']['kwargs']['userid'])
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
        self.is_tournament_game = False
        if self.tournament_name and len(self.tournament_name) > 0:
            self.is_tournament_game = True
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
            if len(tournament_queue[self.tournament_name]) >= 2 and len(tournament_queue_ids[self.tournament_name]) >= 2:
                    
                
                print(f"USERS THAT WIN: {tournament_wins}", flush=True)
                print(f"QUEUE IDS: {tournament_queue_ids[self.tournament_name]}", flush=True)
                if self.tournament_name in tournament_wins and (
                    tournament_queue_ids[self.tournament_name][0] in tournament_wins[self.tournament_name]
                    and tournament_queue_ids[self.tournament_name][1] not in tournament_wins
                ):
                    temp = tournament_queue[self.tournament_name].pop(0)
                    temp_id = tournament_queue_ids[self.tournament_name].pop(0)
                    tournament_queue[self.tournament_name].append(temp)
                    tournament_queue_ids[self.tournament_name].append(temp_id)

                elif self.tournament_name in tournament_wins and (
                    tournament_queue_ids[self.tournament_name][0] not in tournament_wins[self.tournament_name]
                    and tournament_queue_ids[self.tournament_name][1] in tournament_wins[self.tournament_name]
                ):
                    temp = tournament_queue[self.tournament_name].pop(1)
                    temp_id = tournament_queue_ids[self.tournament_name].pop(1)
                    tournament_queue[self.tournament_name].append(temp)
                    tournament_queue_ids[self.tournament_name].append(temp_id)

                if (
                    self.tournament_name not in tournament_wins
                    or (
                        tournament_queue_ids[self.tournament_name][0] not in tournament_wins[self.tournament_name]
                        and tournament_queue_ids[self.tournament_name][1] not in tournament_wins[self.tournament_name]
                    )
                    or (
                        tournament_queue_ids[self.tournament_name][0] in tournament_wins[self.tournament_name]
                        and tournament_queue_ids[self.tournament_name][1] in tournament_wins[self.tournament_name]
                    )
                ):
                    print(f"TOURNAMENT_QUEUES IDS: {tournament_queue_ids}", flush=True)
                    self.player_1 = tournament_queue[self.tournament_name].pop(0)
                    self.player_2 = tournament_queue[self.tournament_name].pop(0)
                    tournament_queue_ids[self.tournament_name].pop(0)
                    tournament_queue_ids[self.tournament_name].pop(0)

                else:
                    return

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
        ids = self.group_name.split('_')
        id1 = int(ids[2]) 
        id2 = int(ids[3])

        # Share usernames to anounce them
        if player_number == 2:
            player1_user = await sync_to_async(CustomUser.objects.get)(id=id1)
            player2_user = await sync_to_async(CustomUser.objects.get)(id=id2)
            print(f"\033[33mABOUT TO SEND ANOUNCEMENT!!\033[0m", flush=True)

            if self.is_tournament_game:
                await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "announce_players",
                    "player1_username": player1_user.username,
                    "player2_username": player2_user.username,
                }
                )
            else:
                await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "announce_Qmatch",
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
            "tournament_name": self.tournament_name,
        }))
    async def announce_Qmatch(self, event):
        await self.send(text_data=json.dumps({
            "type": "announcement",
            "message": f"Quick Match between {event['player1_username']} and {event['player2_username']} is about to begin!",
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

                if not self.tournament_name in tournament_wins:
                    tournament_wins[self.tournament_name] = []
                tournament_wins[self.tournament_name].append(self.game_state.player1.user_id)


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
                
                if not self.tournament_name in tournament_wins:
                    tournament_wins[self.tournament_name] = []
                tournament_wins[self.tournament_name].append(self.game_state.player2.user_id)
                
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

        # New game model updates
        game_data = {
        'player1': player1_user.username,
        'player2': player2_user.username,
        'winner': player1_user.username if winner == 1 else player2_user.username,
        'date': timezone.now()
        }

        # ** to unpack dict into various arguments
        new_game = await sync_to_async(Game.objects.create)(**game_data)

        # Link game to users
        await sync_to_async(player1_user.games.add)(new_game)
        await sync_to_async(player2_user.games.add)(new_game)

    async def update_tournament_stats(self, winner_id):

        print(f"\033[96mUPDATE_TOURNAMENT_STATS CALLED, winner_id : {winner_id}\033[0m", flush=True)
        # Actualiza las estadísticas del ganador
        player_user = await sync_to_async(CustomUser.objects.get)(id=winner_id)
        current_tournament = await sync_to_async(Tournament.objects.get)(name=self.tournament_name)
        current_tournament.finished = True
    
        player_stats = player_user.tournament_stats
        player_stats['total'] = player_stats.get('total', 0) + 1
        player_stats['wins'] = player_stats.get('wins', 0) + 1
        player_user.tournament_stats = player_stats
    
        await sync_to_async(player_user.save)()
    
        # Itera sobre los perdedores del torneo para actualizar sus estadísticas
        if self.tournament_name in tournament_lost:
            loser_ids = tournament_lost[self.tournament_name]
            for loser_id in loser_ids:
                if loser_id == winner_id:  # No actualizar estadísticas del ganador dos veces
                    continue
                loser_user = await sync_to_async(CustomUser.objects.get)(id=loser_id)
                loser_stats = loser_user.tournament_stats
                loser_stats['total'] = loser_stats.get('total', 0) + 1
                loser_stats['losses'] = loser_stats.get('losses', 0) + 1
                loser_user.tournament_stats = loser_stats
                await sync_to_async(loser_user.save)()
    
        await self.send(text_data=json.dumps({'message': 'Tournament is over'}))
        await self.player_2.send(text_data=json.dumps({'message': 'Tournament is over'}))
        await sync_to_async(current_tournament.save)()



class PlayerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = int(self.scope['url_route']['kwargs']['userid'])

        self.user = await CustomUser.objects.aget(id=self.user_id)
        self.user.is_online = True
        self.user.last_seen = now()
        await self.accept()
        self.user.is_online = True
        await sync_to_async(self.user.save)()

    async def disconnect(self, close_code):
        """
        Espera un periodo de gracia antes de marcar al usuario como completamente desconectado.
        Si se reconecta durante este tiempo, no se actualiza a False.
        """
        await asyncio.sleep(10)
        if (now() - self.user.last_seen).total_seconds() > 10:  # Tiempo de gracia
            self.user.is_online = False
            await sync_to_async(self.user.save)()

        #await super().disconnect(close_code)

    async def receive(self, text_data):
        message = json.loads(text_data)
        if message.get("type") == "ping":
            self.user.last_seen = now()
            await sync_to_async(self.user.save)()