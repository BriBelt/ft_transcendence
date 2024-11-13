function logInHandler()
{
    const loginForm = document.getElementById('login-form');

    if (loginForm)
    {
        loginForm.addEventListener('submit', function(event)
	{
            event.preventDefault();

            const formData =
	    {
                username: document.getElementById('username').value,
                password: document.getElementById('password').value
            };

	    if (validateInput(formData, 'login'))
	    {
                fetch('/login/',
		{
                    method: 'POST',
                    headers:
		    {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                })
			    .then(response => response.json())
                .then(data =>
		{
                    if (data.status === 'success')
		    {
			localStorage.setItem('userid', data.userid);
			if (data.message === 'Verification code sent')
			{
				code = prompt('Enter the verification code: ');
				if (handle2FA(code))
				{

					alert('Valid code');
					return;
				}
				else 
				{
					alert('Non-valid code');
					return;
				}

			}
			else
			{
				localStorage.setItem('access', data.access);
				localStorage.setItem('playing', 'false');
				alert('Log in successful!');
				navigateTo('/home/');
			}
                    }
		    else
		    {
		    	console.log('Inside else');
		    	if (data.message === 'Invalid credentials')
			{
				showMessage('password-error', 'Invalid password. Try again');
			}
		    	else if (data.message === 'Invalid username')
			{
				showMessage('username-error', 'Invalid username');
			}
			else
			{
				alert('Your account is not verified, please check your email.')
				showMessage('email-error', 'Account is not verified, please check your email');
			}
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            }
        });
    }
    else
    {
        console.error('login-form not found');
    }
}

function handle2FA(code)
{
	const formData =
	{
		username: document.getElementById('username').value,
		otp: code
	};
	fetch('/login/verify-2fa/',
	{
	    method: 'POST',
	    headers:
	    {
		'Content-Type': 'application/json'
	    },
	    body: JSON.stringify(formData)
	})
	.then(response => response.json())
	.then(data =>
	{
	    if (data.status === 'success')
	    {
		localStorage.setItem('access', data.access);
		alert('Log in successful!');
		navigateTo('/home/');
		return (true);
	    }
	    else
	    {
		showMessage('code-error', 'Incorrect verification code, please try again.');
		return (false);
	    }
	})
}

function validateInput(formData, form)
{
	let valid = true;

	if (!validateUsername(formData.username))
	{
		valid = false;
		showMessage('username-error', 'Invalid username');
	}
	else
	{
		hideMessage('username-error');
	}
	if (form != 'edit' && !validateEmail(formData.email, form))
	{
		valid = false;
		showMessage('email-error', 'Invalid email');
	}
	else
	{
		hideMessage('email-error');
	}
	if (form === 'edit' && formData.password)
	{
		if (!validatePass(formData.password))
		{
			valid = false;
			showMessage('password-error', 'Invalid password');
		}
		else
			hideMessage('password-error');
	}
	else if (form !== 'edit')
	{
		if (!validatePass(formData.password))
		{
			valid = false;
			showMessage('password-error', 'Invalid password');
		}
		else
		{
			hideMessage('password-error');
		}
	}
	if (form === 'signup' && formData.password !== formData.confPass)
	{
		valid = false;
		showMessage('conf-password-error', 'Invalid password confirmation');
	}
	else
	{
		hideMessage('conf-password-error');
	}
	return (valid);
}

function validateUsername(username)
{
	const pattern =/^(?!ft_)[a-zA-Z0-9._%+-]{1,8}$/;

	return (pattern.test(username));
}

function validateEmail(email, form)
{
	if (form === 'login')
		return (true);

	const pattern = /^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$/;

	return (pattern.test(email));
}

function validatePass(password)
{
	const pattern = /(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,128}/;

	return (pattern.test(password));
}

function showMessage(id, message)
{
	const elementMsg = document.getElementById(id);
	
	if (elementMsg)
	{
		elementMsg.textContent = message;
		elementMsg.style.display = 'block';
	}
}

function hideMessage(id)
{
	const message = document.getElementById(id);

	if (message)
	{
		message.style.display = 'none';
	}
}

window.logInHandler = logInHandler;
window.showMessage = showMessage;
window.hideMessage = hideMessage;
window.validateUsername = validateUsername;
window.validateEmail = validateEmail;
window.validatePass = validatePass;
