// This function will send a petition to the back, the back will give this function
// the settings (.env) variables needed. After getting the variables, it will
// construct the authUrl.
async function getAuthUrl()
{
	try
	{
		const response = await fetch('api/auth-settings/',
		{
			method: 'GET',
			headers:
			{
				'Content-Type': 'application/json'
			}
		});
		const data = await response.json();
		if (data.status === 'success')
		{
			const authUrl =  `${data.auth_endpoint}?client_id=${data.client_id}&redirect_uri=${data.redirect_uri}&response_type=${data.scope}`
			return (authUrl);
		}
		else
		{
			console.error('Error fetching API settings: ', data.message);
			alert('Could not retrieve API settings');
			return (null);
		}
	}
	catch(error)
	{
		console.error('Error fetching API settings: ', error);
		return (null);
	}

}

// This function calls getAuthUrl(), and will redirect to the corresponing URL
// which will start the process of loging into the 42 intra
async function handleAuth()
{
	const authUrl = await getAuthUrl();

	if (authUrl)
	{
		console.log('Before redirecting to url');
		window.location.href = authUrl;
	}
	else
	{
		alert('No AuthURL was found');
	}
}

// After being redirected to the callback html, this function will be triggered by the DOM 
// if a code is found inside the URL. First, it will send the code received to the back,
// so the backend uses that code with the 42API and can retrieve information. 
// If the code is valid, the backend will return a success response along with the info
// that retrieved from the API. Finally, the handle42Info is called.
async function verifyCode(code)
{
	try
	{
		const response = await fetch('api/auth/verify/',
		{
			method: 'POST',
			headers:
			{
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ code })
		});
		const data = await response.json();
		if (data.status === 'success')
			handle42Info(data.userInfo);
		else
		{
			console.log('Error: ', data.message);
			alert('Code verification failed');
		}
	}
	catch(error)
	{
		alert("ex verifyCode2: " + error);
		console.error("Error: ", error);
	}
}

// This will be the last petition sent to the backend for this OAuth process.
// In this petition, it will send back the user information to the backend,
// the backend will handle the information and return a response along with
// a URL to redirect the program back to the app.
async function handle42Info(userInfo)
{
	try
	{
		const response = await fetch('api/auth/create-user/',
		{
			method: 'POST',
			headers:
			{
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ userInfo })
		});
		const data = await response.text();

		try
		{
			const jsonData = JSON.parse(data);
			if (jsonData.status === 'success')
				window.location.href = jsonData.redirect_url;
			else
			{
				console.log('Error: ', jsonData.message);
				alert('OAuth login/signup failed');
			}
		}
		catch(e)
		{
			console.error('Error: ', e);
			console.error('Response: ', data);
			alert('Failed to create the user');
		}
	}
	catch(error)
	{
		alert("ex handle42Info2: " + error);
		console.error("Error: ", error);
	}
}

// This function will be always in the background, waiting for the callback.html
// file, and the corresponding url to either the code or the refresh or access
// tokens given by the backend. Depending to what token or code is in the URL,
// it will set the tokens inside the localStorage or will start the process of OAuth.
document.addEventListener('DOMContentLoaded', () =>
{
	const urlParams = new URLSearchParams(window.location.search);
	const code = urlParams.get('code');
	const access = urlParams.get('access');

	if (access)
	{
		localStorage.setItem('access', access);
		window.history.replaceState({}, document.title, "/home/");
		navigateTo('/home/');
	}
	if (code)
	{
		verifyCode(code);
	}
});

window.getAuthUrl = getAuthUrl;
window.handleAuth = handleAuth;
window.handle42Info = handle42Info;
window.verifyCode = verifyCode;
