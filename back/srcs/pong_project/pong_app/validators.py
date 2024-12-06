import re
import os
import random 
import hashlib 
from django.core.exceptions import ValidationError
from django.conf import settings


def validateUsername(username):
	pattern = re.compile(r'^(?!ft_)[a-zA-Z0-9._%+-]{1,8}$')

	if not pattern.match(username):
		raise ValidationError('Invalid username: must not start with "ft_", must be 1-8 characters long, and contain only alphanumeric characters and ._%+-')

def validateEmail(email):
	pattern = re.compile(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$')

	if not pattern.match(email):
		raise ValidationError('Invalid email format')


def validatePassword(password):
	pattern = re.compile(r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,128}')

	if not pattern.match(password):
		raise ValidationError('Password must be at least 8 characters long, contain at least one digit, one lowercase letter, and one uppercase letter')

def generate_random_digits(n=6):
	return "".join(map(str, random.sample(range(0, 10), n)))

def encodeOTP(otp):
	return hashlib.sha256((settings.JWT_SECRET_KEY + otp).encode()).hexdigest()

def checkOTP(otp, stored):
	return encodeOTP(otp) == stored
