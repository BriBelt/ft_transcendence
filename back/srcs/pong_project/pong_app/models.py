from django.db import models
from django.contrib.auth.models import AbstractUser 
import random
from django.utils.timezone import now

# Create your models here.

class CustomUser(AbstractUser):
	# Preferred language
	# lang = models.CharField(max_length=2)
	# This is to store the user's profile pic
	avatar = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
	# This attribute is to check if the user has registrated via 42intra
	intra = models.BooleanField(default=False)
	tfa = models.BooleanField(default=False)
	# If the tfa is set to true, then the otp should not be blank
	otp = models.CharField(max_length=6, null=True, blank=True)
	otp_expDate = models.DateTimeField(null=True, blank=True)

	is_online = models.BooleanField(default=False)

	# Game stats for every game played, including the tournament games(total/wins/losses)
	game_stats = models.JSONField(default=dict)
	# Tournament stats ONLY for tournament, not the rounds in the tournament(total/wins/losses)
	tournament_stats = models.JSONField(default=dict)
	# self so that can be related witj user model,
	friends = models.ManyToManyField('self', blank=True)
	games = models.ManyToManyField('Game', blank=True, related_name='players')
	user_in_online_game = models.BooleanField(default=False)
	user_in_tournament = models.BooleanField(default=False)
	#id = models.IntegerField()

	def __str__(self):
		return f"{self.username}"

class Tournament(models.Model):
	name = models.CharField(max_length=15)
	# Key = User chosen tag, value = user instance
	participants = models.JSONField(default=dict)
	finished = models.BooleanField(default=False)
	winner = models.CharField(max_length=12, blank=True, null=True)

	def __str__(self):
		return f"Winner of {self.name}: {self.winner}!"

class	Game(models.Model):
	player1 = models.CharField(max_length=8, blank=True, null=True)
	player2 = models.CharField(max_length=8, blank=True, null=True)
	winner = models.CharField(max_length=8, blank=True, null=True)
	date = models.DateTimeField(default=now)

	def __str__(self):
		return f"Winner: {self.winner}!"


class Board:
	def __init__(self, width=900, height=500) -> None:
		self.width = width
		self.height = height

class Ball:
	def __init__(self, board) -> None:
		self.width = board.width / 50
		self.height = self.width
		self.x = (board.width / 2) - (self.height / 2)
		self.y = (board.height / 2) - (self.height / 2)
		#self.velocityX = 1
		#self.velocityY = 2
		list1 = [1, -1]
		self.velocityX = 10 * random.choice(list1) # 5
		self.velocityY = 20 * random.choice(list1) # 6

class Paddle:
	def __init__(self, number, board, user_id) -> None:
		self.width = board.width / 50
		self.height = self.width * 5
		#list1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30]
		#self.velocityY = random.choice(list1)
		self.velocityY = 0
		self.score = 0
		self.user_id = user_id
		if number == 1:
			self.x = 10
			self.y = (board.height / 2) - (self.height / 2)
		else:
			self.x = board.width - (self.width * 2)
			self.y = (board.height / 2) - (self.height / 2)
