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
