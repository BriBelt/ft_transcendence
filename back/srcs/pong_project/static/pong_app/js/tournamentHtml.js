function createTournamentHTML()
{
	return (`

	<i class="fas fa-trophy fa-2x" style="color: black;"></i>
	<div class="form-container">
		<h2 class="form-title">Create a tournament</h2>
		<form id="login-form">
			<div class="form-group">
				<label for="tournamentName">Name</label>
				<input type="username" class="form-control" id="name" placeholder="Enter a name">
					<span id="tournament-error" class="error-message"></span>
			</div>
			<button class="custom-button" id="create-btn">Create</button>
		</form>
	</div>
	`);
}

function loadCreateTournament()
{
	const app = document.getElementById('app');
	app.innerHTML = createTournamentHTML();
	const name = document.getElementById('name');
	const create = document.getElementById('create-btn');

	console.log("inside loadCreateTournament");

	if (create)
	{
		console.log("create exists");
		create.addEventListener('click', async function(event)
		{
			event.preventDefault();
			if (name)
			{
				const tournamentName = name.value;
				console.log("Tournament name: " + tournamentName);
				await createTournament(tournamentName);
			}
			
		});
	}
}

async function loadTournamentsSection()
{
	const token = localStorage.getItem('access');

	if (token)
	{
		try
		{
			const response = await fetch('/home/game/tournament/join',
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
				let tournamentsHTML = `
				<div class="options-container">
					<div class="option">
						<h3><b>Tournaments</b></h3>
						<div class="friends-list" style="width: 100%;">
				`;

				data.tournaments.forEach(tournament => {
					tournamentsHTML += `
							<div class="friend-card">
								<span class="friend-username">${tournament.name}</span>
								<span class="friend-status">${tournament.players}/4</span>
								<div class="friend-actions">
									<button data-tournament="${tournament.name}" class="custom-button join-tournament" style="background-color: green; align-items: left;">
										<i class="fas fa-plus"></i>
									</button>
								</div>
							</div>`});
				tournamentsHTML +=	`</div>
					</div>
				</div>`;

				app.innerHTML = tournamentsHTML;

				document.querySelectorAll('.join-tournament').forEach(button => {
					button.addEventListener('click', async function(event)
					{
						const tournamentName = event.currentTarget.getAttribute('data-tournament');
						console.log("Someone clicked the button");
						console.log(tournamentName);
						await joinTournament(tournamentName);
					});
				});
			}
			else
			{
				await checkRefresh(data, '/home/game/tournament/join', token);
			}
		}
		catch(error)
		{
			console.log('INSIDE CATCH OF TOURNAMENTS!');
			notAuthorized(error);
		}
	}
	else
	{
		notAuthorized();
	}
}

window.createTournamentHTML = createTournamentHTML;
window.loadTournamentsSection = loadTournamentsSection;
window.loadCreateTournament = loadCreateTournament;
