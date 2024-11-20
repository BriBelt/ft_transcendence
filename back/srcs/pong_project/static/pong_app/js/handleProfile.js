async function loadProfile()
{
	const token = localStorage.getItem('access');

	if (token)
	{
		try
		{
			const response = await fetch('/home/profile/',
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

				app.innerHTML = profileHTML(data, avatarUrl);

				const edit = document.getElementById('edit-profile');
				if (edit)
				{
					edit.addEventListener('click', function(event)
					{
						event.preventDefault();	
						navigateTo('/home/profile/edit/');
					});
				}
				const back = document.getElementById('back-to-home');
				if (back)
				{
					back.addEventListener('click', function(event)
					{
						event.preventDefault();	
						navigateTo('/home/');
					});
				}
			}
			else
			{
				await checkRefresh(data, '/home/profile/', token);
//				console.log(data.status);
//				console.log(data.message);
//				console.log('Inside the else for the data message')
//				if (data.message === 'Access unauthorized')
//				{
//					const result = await checkRefreshToken(token);
//					console.log('Inside the access unauthorized')
//					if (result)
//					{
//						console.log('Inside result');
//						console.log(result);
//						navigateTo('/home/profile/');
//					}
//				}
//				else
//				{
//					console.log('Inside the else for unauthorized')
//					alert('You are not authorized to view this page. Please log in.');
//					navigateTo('/login/');
//				}
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
