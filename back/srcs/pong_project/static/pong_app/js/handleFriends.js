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
						<button class="custom-button" id="add-friend" style="background-color: green; width: 10%;">
							<i class="fas fa-user-plus"></i>
						</button>
						<div class="friends-list" style="width: 100%;">
				`;

				data.friends.forEach(friend => {
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
							</div>`});
				friendsHTML +=	`</div>
					</div>
				</div>`;

				app.innerHTML = friendsHTML;

				document.querySelectorAll('.remove-friend').forEach(button => {
					button.addEventListener('click', function(event) {
						const username = event.target.getAttribute('data-username');
						removeFriend(username);
					});
				});

				document.getElementById('add-friend').addEventListener('click', function() {
					const username = prompt("Enter the username of the friend you want to add:");
					if (username) {
						addFriend(username);
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

function addFriend(username)
{
	const token = localStorage.getItem('access');
	if (token)
	{
		fetch('/home/friends/add/',
		{
			method: 'POST',
			headers:
			{
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({friend_username: username})
		})
		.then(response => response.json())
		.then(data =>
		{
			alert(data.message);
			loadFriendsSection();
		})
		.catch(error => console.error('Error:', error));
	}
}

function removeFriend(username)
{
	const token = localStorage.getItem('access');
	if (token)
	{
		fetch('/home/friends/remove/',
		{
			method: 'POST',
			headers:
			{
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({friend_username: username})
		})
		.then(response => response.json())
		.then(data =>
		{
			alert(data.message);
			loadFriendsSection();
		})
		.catch(error => console.error('Error:', error));
	}
}

window.loadFriendsSection = loadFriendsSection;
