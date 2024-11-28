async function loadProfileSettings()
{
	const token = localStorage.getItem('access');
	if (token)
	{
		try
		{
			const response = await fetch('/get_user_info/',
			{
				method: 'GET',
				headers:
				{
					'Authorization': `Bearer ${token}`,
					'Content-Type': 'application/json'
				}
        	})
			const data = await response.json();
			if (data.status === 'success')
			{
				const avatarUrl = data.avatar ? data.avatar : '/static/pong_app/media/user-pic.jpg';
				app.innerHTML = profileSettingsHTML(data, avatarUrl);
				const twofa = document.getElementById('twofa');
				twofa.checked = data.tfa;

				const username_field = document.getElementById('usernameDiv');
				const password_field = document.getElementById('passwordDiv');
				const twofa_field = document.getElementById('twofaDiv');
				if (data.intra)
				{
					username_field.classList.add('d-none');	
					password_field.classList.add('d-none');	
					twofa_field.classList.add('d-none');	
				}
				const save = document.getElementById('save-changes');
				if (save)
				{
					save.addEventListener('click', function(event)
				{
					event.preventDefault();
					updateUserInfo();
				});
				}
	 		}
			else
			{
				await checkRefresh(data,'/home/profile/edit/', token);
			}
		}
		catch(error)
		{
			notAuthorized(error);
		}
	}
	else
	{
		notAuthorized();
	}
}

function updateUserInfo()
{
    const token = localStorage.getItem('access');

	if (token)
	{
		const username = document.getElementById('username').value;
		const password = document.getElementById('password').value;
		const twofa = document.getElementById('twofa').checked ? 'on' : 'off';
		const userPic = document.getElementById('avatar').files[0];


		const userDict =
		{
		    username: username,
		    twofa: twofa,
		};
		if (password)
			userDict.password = password;

		if (userPic)
		{
		    const reader = new FileReader();
		    reader.readAsDataURL(userPic);

		    reader.onloadend = function ()
		    {
			userDict.avatar = reader.result;// Convertido a base64

			if (validateInput(userDict, 'edit'))
				sendUserData(userDict, token);
		    };
        	}
		else
		{
			if (validateInput(userDict, 'edit'))
		    		sendUserData(userDict, token);
		}
	}
	else
	{
		notAuthorized();
    	}
}

async function sendUserData(userDict, token)
{
	try
	{
		const response = await fetch('/home/profile/edit/',
		{
		    method: 'PUT',
		    headers:
			{
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json',
			},
		    body: JSON.stringify(userDict)
		})
		const data = await response.json();
		if (data.status === 'success')
		{
		    alert('Info updated correctly!');
		    navigateTo('/home/profile/', userDict);
		}
		else
		{
		    if (data.message)
		    {
			if (data.message.includes('file'))
			{
			    showMessage('file-error', data.message);
			}
			console.error(data.message);
					await checkRefresh(data, '/home/profile/edit/', token);
		    }
		}
	}
	catch(error)
	{
		notAuthorized(error);
	}
}

window.loadProfileSettings = loadProfileSettings;
