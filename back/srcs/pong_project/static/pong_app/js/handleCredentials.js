function connectUser(userid) {
    if (!userid) {
        console.error("Invalid userid");
        return;
    }

    const onlinesocket = new WebSocket('wss://' + window.location.host + '/ws/online/' + userid + '/');

    onlinesocket.onopen = () => {
        console.log("WebSocket connection established");
    };

    onlinesocket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };

    function sendPing() {
        if (onlinesocket.readyState === WebSocket.OPEN) {
            onlinesocket.send(JSON.stringify({ type: "ping" }));
            console.log("Ping sent");
        } else {
            console.warn("WebSocket is not open, skipping ping");
        }
    }

    // Llamada inicial y luego se repite cada 5 segundos
    sendPing();
    setInterval(sendPing, 5000);
}

function logInHandler()
{
    const loginForm = document.getElementById('login-form');

    if (loginForm)
    {
    	try
	{
		loginForm.addEventListener('submit', async function(event)
		{
		    event.preventDefault();

		    const formData =
		    {
			username: document.getElementById('username').value,
			password: document.getElementById('password').value
		    };

		    if (validateInput(formData, 'login'))
		    {
			const response = await fetch('/login/',
			{
			    method: 'POST',
			    headers:
			    {
				'Content-Type': 'application/json'
			    },
			    body: JSON.stringify(formData)
			});
			const data = await response.json();

			if (data.status === 'success')
			{
				connectUser(data.userid)
				localStorage.setItem('userid', data.userid);
				const code = document.getElementById('code').value;
				if (code)
				{
					handle2FA(code);
				}
				else if (data.message === 'Logged in successfully!')
				{
					localStorage.setItem('access', data.access);
					localStorage.setItem('playing', 'false');
					navigateTo('/home/');
				}
				else if (data.message === 'Verification code needed')
				{
					const codeDiv = document.getElementById('codeDiv');
					codeDiv.style.display = '';
					await askForCode(formData);
				}
			}
			else
			{
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
		}
	    });
	}
        catch(error)
	{
//             console.error('Error:', error);
        }
    }
}

async function askForCode(userData)
{
	try
	{
		const response = await fetch('/login/2fa-code/', 
		{
                    method: 'POST',
                    headers:
		    {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(userData)
		});
		const data = await response.json();

		if (data.status === 'success')
			return (true);
		else
			return (false);
	}
	catch(error)
	{
		return (false);
	}
}

async function handle2FA(code)
{
	const formData =
	{
		username: document.getElementById('username').value,
		otp: code
	};
	if (code)
	{
		const response = await fetch('/login/verify-2fa/',
		{
		    method: 'POST',
		    headers:
		    {
			'Content-Type': 'application/json'
		    },
		    body: JSON.stringify(formData)
		});

		const data = await response.json();
		if (data.status === 'success')
		{
			localStorage.setItem('access', data.access);
			navigateTo('/home/');
		}
		else
		{
			showMessage('code-error', 'Incorrect verification code, try again.');
			askForCode(formData);
		}
	}
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
