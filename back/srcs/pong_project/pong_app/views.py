import json
import smtplib, ssl
from django.shortcuts import render, redirect
from django.db import IntegrityError
from django.core.exceptions import ValidationError
import requests
import os

from http import HTTPStatus
from django.http import HttpResponse, JsonResponse

from django.contrib.auth import authenticate, login, logout

from .models import CustomUser, Tournament
from django.conf import settings
from django.contrib.auth.models import User 
from .validators import validateUsername, validateEmail, validatePassword, generate_random_digits
from email.mime.text import MIMEText
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from datetime import timedelta
from django.utils import timezone
from .jwtUtils import create_jwt_token, get_user_from_jwt, create_jwt_refresh_token, decode_jwt_token, check_expiry
from django.views.decorators.csrf import csrf_exempt
from .avatar import handle_avatar_upload


@csrf_exempt
def main_view(request):

	if not request.user.is_authenticated:
		if request.method == 'GET':
			return render(request, 'pong_app/index.html')
	return render(request, "pong_app/index.html")

# This function will be used for almost all views, it will be used as a decorator, which
# needs to execute right before the each view. Its purpose is to get both the refresh and
# access token, verify first the access, if it is valid, the view will be executed correctly.
# Else, if it's expired, it will check the received refresh token. There's two different outcomes:
# the refresh token is valid or not. If the refresh token is valid, a new access token will be provided
# in the response, else, means the session of the user is no longer valid, therefore logs out the user.
@csrf_exempt
def jwt_required(viewFunction):

	def wrapper(request, *args, **kwargs):
		# Take both tokens, refresh inside the cookies, access inside the header
		# or depending on the type of request, it could be inside the body.
		auth_header = request.headers.get('Authorization')
		refresh_token = request.COOKIES.get('refresh_token')
		token = None
		tokenType = None
		if auth_header and auth_header.startswith('Bearer '):
			token = auth_header.split(' ')[1]
			print('There is a token in header!', flush=True)
		else:
			print('No token in header, checking if it is in body!', flush=True)
			try:
				if request.body:
					body_data = json.loads(request.body)
					tokenType = body_data.get('tokenType')
					token = body_data.get('token')
			except json.JSONDecodeError:
				print('Invalid JSON!', flush=True)
				return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
		if token:
			print('Token founded!', flush=True)
			user = None
			# If the token is expired, we look for the refresh token and check it.
			if check_expiry(token) is True:
				print('Token expired', flush=True)
				print('Inside wrapper, checking access', flush=True)
				if refresh_token is not None and tokenType == 'Refresh':
				# The refresh token is expired, we return our response.
					print('Refresh token sent!', flush=True)
					if check_expiry(refresh_token) is True:
						print('Refresh has expired!', flush=True)
						decode_jwt_token(refresh_token, refreshType="yes")
						return JsonResponse({'status': 'expired', 'message': 'Refresh expired'}, status=402)
					# The refresh token is valid, we execute the view
					else:
						print('Refresh is still active!', flush=True)
						user = get_user_from_jwt(token)
						request.user = user
						if user is None:
							print('couldnt get user from token!!!', flush=True)
						return viewFunction(request, *args, **kwargs)
				# The access token is expired, we send a especific response so the front knows that it needs to
				# ask for a new access token to the back-end's view "verifyRefresh".
				else:
					print('Access token expired!', flush=True)
					return JsonResponse({'status': 'error', 'message': 'Access unauthorized'}, status=401)
					
			# Everything is correct, we set the request.user and execute the view.
			else:
				print('there is a token and it didn`t expire!', flush=True)
				user = get_user_from_jwt(token)
				if user is None:
					print('couldnt get user from token!!!', flush=True)
				request.user = user
				return viewFunction(request, *args, **kwargs)
		return render(request, "pong_app/index.html")
	return wrapper

# This view will be called after the front-end receives the response that the access token is expired. It will receive the refresh token
# inside the cookies of the request. After the decorator checks that the refresh token is valid, this view will create a new access token
# and return it in the response.
@csrf_exempt
@jwt_required
def	verifyRefresh(request):
	if request.method == 'POST':
		print('Inside verify Refresh', flush=True)
		newToken = create_jwt_token(request.user)
		print('-------------------------------------', flush=True)
		print(newToken, flush=True)
		print('-------------------------------------', flush=True)
		return JsonResponse({'status': 'success', 'newToken': newToken, 'message': 'New access token was generated'}, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@jwt_required
def	getUserInfo(request):
	if request.method == 'GET':
		user = request.user
		username = user.username
		status = "ONLINE" if user.is_online else "OFFLINE"
		print(f"Username: {username}, Status: {status}", flush=True)
		return JsonResponse({'status': 'success', 'username': username, 'is_online': user.is_online, 'avatar': user.avatar.url if user.avatar else None, 'intra': user.intra, 'tfa': user.tfa}, status=200)

	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def signupView(request):

	if request.method == 'GET':
		return render(request, "pong_app/index.html")

	elif request.method == 'POST':
		data = json.loads(request.body)
		username = data.get('username', '')
		email = data.get('email', '')
		password = data.get('password', '')
		confPass = data.get('confPass', '')
		# Validating the new user's credentials
		try:
			validateUsername(username)
			validateEmail(email)
			validatePassword(password)
		except ValidationError as e:
			return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
		if not password == confPass:
			return JsonResponse({'status': 'error', 'message': 'Invalid password confirmation'}, status=400)
		if CustomUser.objects.filter(username=username).exists():
			return JsonResponse({'status': 'error', 'message': 'Username already in use'}, status=400)
		if CustomUser.objects.filter(email=email).exists():
			return JsonResponse({'status': 'error', 'message': 'Email already in use'}, status=400)
		# Create the user after passing all the requirements	
		user = CustomUser.objects.create_user(username, email=email)
		user.is_active = False 
		user.set_password(password + settings.PEPPER)
		user.save()

		# Generating link for confirmation email
		token_generator = PasswordResetTokenGenerator()
		domain = settings.HOST
		uid = urlsafe_base64_encode(force_bytes(user.id))
		token = token_generator.make_token(user)
		activation_link = f'https://{domain}:8000/activate/{uid}/{token}/'
		#activation_link = f'https://localhost:8000/activate/{uid}/{token}/'
		message = MIMEText(f'Please click the following link to activate your account\n {activation_link}')
		message['Subject'] = 'Account confirmation'
		message['From'] = settings.EMAIL_HOST_USER 
		message['To'] = email 

		# Starting the server smtp connection and sending the email
		smtp_connection = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
		smtp_connection.starttls()
		smtp_connection.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
		smtp_connection.send_message(message)
		smtp_connection.quit()

		return JsonResponse({'status': 'success', 'message': 'User created succesfully!'}, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def ActivateAccountView(request, uidb64, token):

	if request.method == 'GET':
		try:
			# Decode the user ID from the URL
			uid = force_str(urlsafe_base64_decode(uidb64))
			user = CustomUser.objects.get(pk=uid)
		except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
			user = None
			# Create an instance of the token generator
		token_generator = PasswordResetTokenGenerator()
				# Check if the token is valid
		if user is not None and token_generator.check_token(user, token):
			user.is_active = True
			user.save()
					# Redirect to the login page or another page after successful activation
			return redirect(f'https://{settings.HOST}:8000')
		else:
					# Render a template with an error message if the token is invalid
			return redirect(f'https://{settings.HOST}:8000')
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def loginView(request):

	if request.method == 'POST':
		data = json.loads(request.body)
		username = data.get('username')
		password = data.get('password')

		try:
			user = CustomUser.objects.get(username=username)
		except CustomUser.DoesNotExist:
			return JsonResponse({'status': 'error', 'message': 'Invalid username'}, status=401)

		# Check the attribute is_active, if it's false, means the user has not verified
		# their email
		if user.is_active is False:
			return JsonResponse({'status': 'error', 'message': 'Email not verified'}, status=401)

		# The password is correct
		if user.check_password(password + settings.PEPPER):
			# If the user has 2FA active, we send the needed code
			if user.tfa is True:
				return JsonResponse({'status': 'success', 'message': 'Verification code needed'}, status=200)
			token = create_jwt_token(user)
			refresh_token = create_jwt_refresh_token(user)
			user.is_online = True
			user.save()
			response = JsonResponse({
					'status': 'success',
					'message': 'Logged in successfully!',
					'access': token,
					'userid': user.id}, status=200)
			response.set_cookie(
				key = 'refresh_token',
				value = refresh_token,
				httponly = True,
				max_age = (settings.JWT_REFRESH_EXPIRATION_DELTA) * 24 * 60 * 60,
				samesite = 'Strict')
			return response
		else:
			return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=401)
	elif request.method == 'GET':
		return render(request, "pong_app/index.html")
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
@jwt_required
def	logoutView(request):
	print("INSIDE LOGOUT VIEW!!!", flush=True)
	if request.method == 'POST':
		user = request.user
		if user:
			user.is_online = False
			user.save()
			print("USER JUST LOGGEDOUT!!!", flush=True)
			return JsonResponse({'status': 'success'}, status=200)
		return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def verify2FA(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		username = data.get('username')
		otp = data.get('otp')
		print(username, flush=True)
		print(otp, flush=True)
		try:
			user = CustomUser.objects.get(username=username)

			if user is not None:
				print("USER OTP: " + user.otp, flush=True)
				if (user.otp == otp and user.otp_expDate is not None and user.otp_expDate > timezone.now()):
					print("Inside the if for verify2FA", flush=True)
					token = create_jwt_token(user)
					user.is_online = True
					user.save()
					return JsonResponse({
							'status': 'success',
							'message': 'Logged in successfully!',
							'access': token},
							status=200
						)
				else:
					print("Inside the else", flush=True)
					return JsonResponse({'status': 'error', 'message': 'Expired code'}, status=400)
			else:
				print("Inside the else for invalid user", flush=True)
				return JsonResponse({'status': 'error', 'message': 'Invalid code'}, status=400)
		except(CustomUser.DoesNotExist):
			print("USER DOES NOT EXIST?!", flush=True)
			return JsonResponse({'status': 'error', 'message': 'User does not exist'}, status=400)
	print("Is not a POST request", flush=True)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def give2FA(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		username = data.get('username')

		try:
			print("USER -------- " + username, flush=True)
			user = CustomUser.objects.get(username=username)
			user.otp = generate_random_digits()
			user.otp_expDate = timezone.now() + timedelta(hours=1)
			user.save()
			email = user.email
			userOtp = user.otp

			message = MIMEText(f'Your verification code is: {userOtp}')
			message['Subject'] = 'Verification code'
			message['From'] = settings.EMAIL_HOST_USER 
			message['To'] = email

			smtp_connection = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
			smtp_connection.starttls()
			smtp_connection.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
			smtp_connection.send_message(message)
			smtp_connection.quit()

			return JsonResponse({'status': 'success', 'message': 'Verification code sent'}, status=200)
		except(CustomUser.DoesNotExist):
			print("USER DOES NOT EXIST?!", flush=True)
			return JsonResponse({'status': 'error', 'message': 'User does not exist'}, status=400)
	print("NON VALID REQUEST METHOD", flush=True)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@jwt_required
def Home(request):
	if request.method == 'GET':
		# Also check if user is online to avoid rendering HomeHTML when refresh token is ok but user in not online
		if request.user.is_online:
			content = {'status': 'success', 'message': 'Welcome to the home page!', 'username': request.user.username}
			return JsonResponse(content, status=200)
		return JsonResponse({'status': 'error', 'message': 'Not online dispite valid token'}, status=400)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@jwt_required
def Profile(request):
	if request.method == 'GET':
		user = request.user
		game_stats = user.game_stats if user.game_stats else {'total': 0, 'wins': 0, 'losses': 0}
		content = {'status': 'success', 'username': user.username, 'email': user.email, 'tfa': user.tfa, 'avatar': user.avatar.url if user.avatar else None,'game_stats': game_stats}
#'game_stats': request.user.game_stats,
#'tournament_stats': request.user.tournament_stats
		return JsonResponse(content, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

# View needed to edit the User's information. Auto-fills the current user's info, when new data
# is entered, checks if it is valid (passes check for characters and if it's repeated or not).


@csrf_exempt
@jwt_required
def EditProfile(request):
	if request.method == 'PUT':
		try:
			# Decodificar el cuerpo JSON
			data = json.loads(request.body)

			user = request.user
			username = data.get('username', user.username)
			password = data.get('password')
			twofa = data.get('twofa', user.tfa)
			avatar_data = data.get('avatar')

			try:
				if username != user.username:
					validateUsername(username)
					if CustomUser.objects.filter(username=user.username).exclude(id=user.id).exists():
						return JsonResponse({'status': 'error', 'message': 'Username in use'}, status=400)
					user.username = username
				if password:
					validatePassword(password)
					user.set_password(password + settings.PEPPER)
			except ValidationError as e:
				return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

			user.tfa = True if twofa == 'on' else False
			
			if avatar_data:
				msgAvatar = handle_avatar_upload(user, avatar_data)
				if msgAvatar != "":
					return JsonResponse({'status': 'error', 'message': msgAvatar}, status=400)
			user.save()
			return JsonResponse({'status': 'success', 'message': 'Profile updated successfully!'}, status=200)
		except json.JSONDecodeError as e:
			return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
		except IntegrityError as e:
			return JsonResponse({'status': 'error', 'message': 'Username in use'}, status=400)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def  authSettings(request):

	if request.method == 'GET':
		data = {
			'status': 'success',
			'client_id': settings.CLIENT_ID,
			'redirect_uri': settings.REDIRECT_URI,
			'auth_endpoint': settings.AUTH_ENDPOINT,
			'scope': settings.SCOPE,
		}
		return JsonResponse(data, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def authVerify(request):
	
	if request.method == 'POST':
		data = json.loads(request.body)
		code = data.get('code')
		print(code, flush=True)
		if not code:
			return JsonResponse({'status': 'error', 'message': 'No code provided'}, status=400)
		tokenResponse = requests.post(settings.TOKEN_URL, data=
		{
			'grant_type': 'authorization_code',
			'client_id': settings.CLIENT_ID,
			'client_secret': settings.CLIENT_SECRET,
			'redirect_uri': settings.REDIRECT_URI,
			'code': code
		})
		tokenData = tokenResponse.json()
		accessToken = tokenData.get('access_token')
		if not accessToken:
			return JsonResponse({'status': 'error', 'message': 'No access token was found'}, status=400)
		userResponse = requests.get(settings.USER_INFO_URL, headers=
		{
			'Authorization': f'Bearer {accessToken}'
		})
		if userResponse.status_code != 200:
			return JsonResponse({'status': 'error', 'message': 'Could not retrieve the user data'}, status=400)
		userInfo = userResponse.json()
		return JsonResponse({'status': 'success', 'userInfo': userInfo}, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def authCreateUser(request):
	
	if request.method == 'POST':
		data = json.loads(request.body)
		userInfo = data.get('userInfo')
		if not userInfo:
			return JsonResponse({'status': 'error', 'message': 'No user information'}, status=401)
		username = "ft_" + userInfo['login']
		email = userInfo['email']
		user, created = CustomUser.objects.get_or_create(username=username, email=email)
		if created is True:
			user.set_unusable_password()
			user.intra = True
			user.is_active = True
			user.is_online = True
			user.save()
		# Could use the CustomUser.objects.get_or_create() and later check if the user exists 
		token = create_jwt_token(user)

		redirect_url = f"https://{settings.HOST}:8000?access={token}"
		return JsonResponse({'status': 'success', 'redirect_url': redirect_url}, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


# FRIENDS
@csrf_exempt
@jwt_required
def FriendsList(request):

	if request.method == 'GET':
		user = request.user
		friends = user.friends.all()
		friends_data = [{'username': friend.username, 'online': friend.is_online} for friend in friends]
		return JsonResponse({'status': 'success', 'friends': friends_data}, status=200, safe=False)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
@jwt_required
def UsersStats(request):

	if request.method == 'GET':
		user = request.user
		users = CustomUser.objects.all()
		users_data = [{'username': other.username, 'online': other.is_online} for other in users]
		return JsonResponse({'status': 'success', 'users': users_data}, status=200, safe=False)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
@jwt_required
def OtherUserProfile(request):

	if request.method == 'POST':
		user = request.user
		data = json.loads(request.body)
		other_username = data.get('other_username')
		try:
			print("------------------------------------------", flush=True)
			print("INSIDE OTHERUSERPROFILE", flush=True)
			print(other_username, flush=True)
			print("------------------------------------------", flush=True)
			otherUser = CustomUser.objects.get(username=other_username)
			games = otherUser.games.all()
			games_data = [{'player1': game.player1, 'player2': game.player2, 'date': game.date.strftime('%Y-%m-%d %H:%M:%S'), 'winner': game.winner} for game in games]
			userInfo = {
				'avatar': str(otherUser.avatar.url) if otherUser.avatar else None,
				'username': other_username,
			}
			return JsonResponse({'status': 'success', 'userInfo': userInfo, 'games_data': games_data}, status=200)
		except CustomUser.DoesNotExist:
			print("User not found:", other_username, flush=True)
			return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
		except Exception as e:
			print("INSIDE OTHERUSERPROFILE EXCEPTION", flush=True)
			return JsonResponse({'status': 'error', 'message': '{str(e)}'}, status=404)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
@jwt_required
def AddFriend(request):

	if request.method == 'POST':
		user = request.user
		data = json.loads(request.body)
		friend_username = data.get('friend_username')
		try:
			if friend_username == user.username:
				return JsonResponse({'status': 'error', 'message': 'That\'s sad, but you cannot add yourself as a friend.'}, status=400)
			friend = CustomUser.objects.get(username=friend_username)
			if friend in user.friends.all():
				return JsonResponse({'status': 'error', 'message': 'This user a is already your friend.'}, status=409)
			user.friends.add(friend)
			return JsonResponse({'status': 'success', 'message': f'{friend_username} added as a friend'}, status=400)
		except Exception as e:
			return JsonResponse({'status': 'error', 'message': 'We don\'t have access to imaginary friends.'}, status=404)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
@jwt_required
def RemoveFriend(request):

	if request.method == 'POST':
		user = request.user
		data = json.loads(request.body)
		friend_username = data.get('friend_username')
		try:
			friend = CustomUser.objects.get(username=friend_username)
			user.friends.remove(friend)
			return JsonResponse({'status': 'success', 'message': f'{friend_username} removed from friends'}, status=200)
		except Exception as e:
			return JsonResponse({'status': 'error', 'message': '{str(e)}'}, status=404)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


# TOURNAMENTS

@csrf_exempt
@jwt_required
def create_tournament_view(request):
	if request.method == 'POST':
		try:
			data = json.loads(request.body)
			user_id = data.get('user_id')
			tour_name = data.get('tour_name')
			if not tour_name or not (2 <= len(tour_name) <= 15):
				return JsonResponse({'status': 'error', 'message': 'Invalid Tournament name.'}, status=400)
			
			if Tournament.objects.filter(name=tour_name).exists():
				return JsonResponse({'status': 'error', 'message': 'A tournament with this name already exists.'}, status=400)

            # Obtain user to add username to tournament participants
			try:
				user = CustomUser.objects.get(id=user_id)
			except CustomUser.DoesNotExist:
				return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)

			# Check if user is on another tournament
			active_tournament = Tournament.objects.filter(participants=user.username, finished=False)
			print(f"Active tournaments: {active_tournament}", flush=True)
			if user.user_in_online_game == True:
				return JsonResponse({'status': 'error', 'message': "User can not join another game!"}, status=405)

			if user.user_in_tournament == True:
				tournaments = Tournament.objects.all()
				for tournament in tournaments:
					if tournament.finished == False and tournament.name != tour_name:
						return JsonResponse({'status': 'error', 'message': "User can not join another tournament!"}, status=405)

            # Create tournament and add user to it
			participants = {user.username: user_id}
			print(f"User in tournament: {user.user_in_tournament} {user.user_in_online_game}", flush=True)
			user.user_in_tournament = True
			user.save()
			tournament = Tournament.objects.create(name=tour_name, participants=participants)
			return JsonResponse({'status': 'success', 'message': 'Tournament created successfully!'}, status=200)

		except json.JSONDecodeError:
			return JsonResponse({'status': 'error', 'message': 'Invalid JSON format.'}, status=400)
		except Exception as e:
			return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
@jwt_required
def join_tournament_view(request):

	if request.method == 'GET':
		tournaments_data = []
		tournaments = Tournament.objects.all()
		for tournament in tournaments:
			if tournament.finished == False:
				tournaments_data.append({'name': tournament.name, 'players': len(tournament.participants)})
		return JsonResponse({'status': 'success', 'tournaments': tournaments_data}, status=200, safe=False)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
@jwt_required
def join_tournament_checker(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		tour_name = data.get('tournament')
		user_id = data.get('user_id')
		
		try:
			tournament = Tournament.objects.get(name=tour_name)
		except Tournament.DoesNotExist:
			return JsonResponse({'status': 'error', 'message': 'No tournament with this name exists.'}, status=404)

		# Obtain user to add username to tournament participants
		try:
			user = CustomUser.objects.get(id=user_id)
		except CustomUser.DoesNotExist:
			return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)

		if user.user_in_online_game == True:
			return JsonResponse({'status': 'error', 'message': "User already playing an online game!"}, status=405)

		if user.user_in_tournament == True:
			tournaments = Tournament.objects.all()
			for tournament in tournaments:
				if tournament.finished == False and tournament.name != tour_name:
					return JsonResponse({'status': 'error', 'message': "User can not join another tournament!"}, status=405)

		if user.username in tournament.participants:
			tournament.participants.pop(user.username)
			tournament.save()
		print(f'PARTS: {tournament.participants}', flush=True)

		if len(tournament.participants) == 4:
			return JsonResponse({'status': 'error', 'message': "Tournament is full!"}, status=403, safe=False)

		#try:
		active_tournament = Tournament.objects.filter(participants=user.username, finished=False)
		if active_tournament:
			return JsonResponse({'status': 'error', 'message': "User can not join another tournament!"}, status=405)
		tournament.participants[user.username] = user_id
		user.user_in_tournament = True
		user.save()
		tournament.save()
		return JsonResponse({'status': 'success', 'message': 'User joined the tournament!'}, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
@jwt_required
def gameOptions(request):
	if request.method == 'GET':
		return JsonResponse({'status': 'success', 'message': 'Page loaded correctly.'}, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
@jwt_required
def gameLocal(request):
	if request.method == 'GET':
		return JsonResponse({'status': 'success', 'message': 'Page loaded correctly.', 'playing': 'true'}, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
@jwt_required
def gameOnline(request):
	if request.method == 'GET':
		user = request.user
		print(f"user: {user} y sobre si está o no en un torneo: {user.user_in_tournament}")
		if user.user_in_tournament == True:
			return JsonResponse({'status': 'error', 'message': "User has joined a tournament, can not play an online game!"}, status=405)
		user.user_in_online_game = True
		user.save()
		return JsonResponse({'status': 'success', 'message': 'Page loaded correctly.'}, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
@jwt_required
def gameTournamentOptions(request):
	if request.method == 'GET':
		return JsonResponse({'status': 'success', 'message': 'Page loaded correctly.'}, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
		
@csrf_exempt
@jwt_required
def notFound(request):
	if request.method == 'GET':
		return JsonResponse({'status': 'success', 'message': 'Page loaded correctly.'}, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
@jwt_required
def gameTournament(request):
	if request.method == 'GET':
		return JsonResponse({'status': 'success', 'message': 'Page loaded correctly.'}, status=200)
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
