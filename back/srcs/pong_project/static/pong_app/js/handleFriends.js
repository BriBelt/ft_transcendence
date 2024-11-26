async function loadFriendsSection()
{
	const token = localStorage.getItem('access');

	if (token)
	{
		try
		{
			const response = await fetch('/home/friends/',
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
				let friendsHTML = `
				<div class="options-container">
					<div class="option">
						<h3><b>Friends</b></h3>
						<div style="display: flex; align-items: center; gap: 0.5rem;"> 
							<input type="username" class="form-control" id="username" placeholder="Enter username"> 
							<button class="custom-button" id="add-friend" style="background-color: green; width: 10%;">
								<i class="fas fa-user-plus"></i>
							</button>
						</div>
						<span id="adduser-error" class="error-message"></span>
						<div class="friends-list" style="width: 100%;">
				`;

				data.friends.forEach(friend =>
				{
					friendsHTML += `
							<div class="friend-card">
								<span class="friend-username">${friend.username}</span>
								<span class="friend-status ${friend.online ? 'online' : 'offline'}">
									${friend.online ? 'Online' : 'Offline'}
								</span>
								<div class="friend-actions">
									<button data-username="${friend.username}" class="custom-button remove-friend" style="background-color: red; align-items: left;">
										<i class="fas fa-user-minus"></i>
									</button>
								</div>
							</div>`
				});
				friendsHTML +=	`</div>
					</div>
				</div>`;

				app.innerHTML = friendsHTML;

				document.querySelectorAll('.remove-friend').forEach(button =>
				{
					button.addEventListener('click', async function(event)
					{
						const username = event.target.getAttribute('data-username');
						await removeFriend(username);
					});
				});

				document.getElementById('add-friend').addEventListener('click', async function()
				{
					const username = document.getElementById('username').value;
					if (username)
					{
						await addFriend(username);
					}
				});
			}
			else
			{
				await checkRefresh(data, '/home/friends/', token);
			}
		}
		catch(error)
		{
			console.log('INSIDE CATCH OF FRIENDS!');
			notAuthorized(error);
		}
	}
	else
	{
		notAuthorized();
	}
}

async function addFriend(username)
{
	const token = localStorage.getItem('access');
	if (token)
	{
		try
		{
			const response = await fetch('/home/friends/add/',
			{
				method: 'POST',
				headers:
				{
					'Authorization': `Bearer ${token}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({friend_username: username})
			});
			const data = await response.json();
			if (data.status === 'success')
				await loadFriendsSection();
			else
			{
				if (data.message === 'Access unauthorized')
				{
				    const result = await checkRefreshToken(token);
				    if (result === "valid")
				    {
					console.log('Access expired but Refresh not, calling again function');
					logoutItem.classList.remove('d-none');
				    }
				}
				else
					showMessage('adduser-error', data.message);	
			}
		}
		catch(error)
		{
			console.error('Error: ' + error);
		}
	}
	else
	{
		notAuthorized();
	}
}

async function removeFriend(username)
{
	const token = localStorage.getItem('access');
	if (token)
	{
		try
		{
			const response = await fetch('/home/friends/remove/',
			{
				method: 'POST',
				headers:
				{
					'Authorization': `Bearer ${token}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({friend_username: username})
			});
			const data = await response.json();	

			if (data.status === 'success')
			{
				alert(data.message);
				loadFriendsSection();
			}
			else
				showMessage('adduser-error', data.message);	
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

window.loadFriendsSection = loadFriendsSection;
