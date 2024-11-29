function checkRefreshToken(token)
{
	return new Promise((resolve, reject) =>
	{
		fetch('/verify-refresh/', {
			method: 'POST',
			headers: {
//				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json'
			},
			credentials: 'include',
			body: JSON.stringify(
			{
				'token': `${token}`,
				'tokenType': 'Refresh'
			})
		})
		.then(response => response.json())
		.then(data =>
		{
			if (data.status === 'success') {
				localStorage.setItem('access', data.newToken); // Save the new access token
				resolve("valid"/*data.new_access_token*/); // Return the new token
			} else if (data.status === 'expired'){
				reject("expired"); // Failed to refresh token
			}
		})
		.catch(error =>
		{
			reject("catch");
		});
	});
}

async function checkRefresh(data, route, token)
{
	if (data.message === 'Access unauthorized')
	{
		const result = await checkRefreshToken(token);
		if (result === "valid")
		{
			navigateTo(route);
		}
	}
}
function notAuthorized(error)
{
	if (error === "expired")
	{
		app.innerHTML = loadNotAuthorizedHTML();
		setTimeout(() => 
		{
			localStorage.removeItem('access');
			navigateTo('/');
		}, 5000);
	}
	else
	{
		alert('You are not authorized to view this page. Please log in.');
		app.innerHTML = loadNotAuthorizedHTML();
		setTimeout(() => 
		{
			localStorage.removeItem('access');
			navigateTo('/');
		}, 5000);
	}
}

window.checkRefreshToken = checkRefreshToken;
window.checkRefresh = checkRefresh
window.notAuthorized = notAuthorized;
