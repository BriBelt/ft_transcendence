import base64
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO

def check_magic_number(img_data, ext):
	# Get the first few bytes of the file
	magic_bytes = img_data[:4].hex().upper()
	magic_numbers = {
	'jpeg': 'FFD8',  # JPEG magic number
	'jpg': 'FFD8',   # JPG maps to JPEG
	'png': '89504E47',  # PNG magic number
	'gif': '47494638',  # GIF magic number
	}
	if ext in magic_numbers:
		expected_magic = magic_numbers[ext].upper()
		return magic_bytes.startswith(expected_magic)
	return False


def handle_avatar_upload(user, avatar_data, min_width=100, min_height=100, max_width=2000, max_height=2000, max_size=1*1024*1024):
	# Check extensions
	format, imgstr = avatar_data.split(';base64,')
	ext = format.split('/')[-1].lower()
	if ext not in ['jpeg', 'jpg', 'png', 'gif']:
		return "Unsupported file extension."
	# Cjeck image size
	img_data = base64.b64decode(imgstr)
	if len(img_data) == 0:
		return "The uploaded file is empty."
	if len(img_data) > max_size:
		return "The uploaded file exceeds the maximum allowed size of 1MB."

	# Check magic numbers to check file extension
	if not check_magic_number(img_data, ext):
		return "File signature does not match the provided file extension."


	# Check image dimensions
	image = Image.open(BytesIO(img_data))
	width, height = image.size
	if width < min_width or height < min_height:
		return f"The image is too small (minimum size: {min_width}x{min_height}px)."
	if width > max_width or height > max_height:
		return f"The image is too large (maximum size: {max_width}x{max_height}px)."

	# Save file 
	avatar_file = ContentFile(img_data, name=f'{user.id}_avatar.{ext}')
	print(avatar_file.name, flush=True)
	user.avatar = avatar_file
	return "" 
