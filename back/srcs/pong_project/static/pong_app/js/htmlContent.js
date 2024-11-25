
//Font Awesome is a very popular icon library that allows you to include thousands of scalable icons on a web page simply by applying CSS classes.
function homeHTML(data)
{
	return(`
	<div class="jumbotron text-center" style="background-color: #745c94;">
		<h1 class="display-4">Welcome to WebPong ${data.username}!</h1>
		<p class="lead">The best way to connect with your friends, personalize your profile and enjoy Pong games.</p>
		<hr class="my-4">
		<p>
			With WebPong, you can:
			<ul class="list-unstyled">
				<li><i class="fas fa-user-friends"></i> Add and manage friends</li>
				<li><i class="fas fa-user-cog"></i> Customize your profile to your liking</li>
				<li><i class="fas fa-gamepad"></i> Challenge your friends in online Pong games</li>
				<li><i class="fas fa-trophy"></i> Create Pong Tournaments to test your skills</li>
			</ul>
		</p>
	</div>

		`);
}

function profileHTML(data, avatarUrl)
{
//?. allows access to a property (total, wins or losses) of game_stats only if game_stats is defined and not null.
	const gamesPlayed = data.game_stats?.total || 0;
	const gamesWon = data.game_stats?.wins || 0;
	const gamesLost = data.game_stats?.losses || 0;
//	The username is not being picked up. Both bottom buttons are not being centered
	return(`
		<div id="profile-settings" class="container mt-4" style="font-family: 'Courier New', Courier, Monospace;">
			<div class="card mx-auto" style="max-width: 500px; background-color: #745c94; border-radius: 20px;">
				<div class="card-body text-center">
					<img src="${avatarUrl}" alt="Profile Picture" class="img-thumbnail mb-3" style="background-color: #362c45; border-radius: 20px;">
					<h3 id="username" style="padding: 10px 10px;">${data.username}</h3>
					<div class="container" style="box-sizing: border-box; width: 100%; padding: 0; margin: 0;">
						<div class="container" style="width: 40%; background-color: #C3B0DB; color: #362c45; border-radius: 20px; margin-top: 20px;">
							<ul class="list-group list-group-flush mb-3">
								<b>Games</b>
								<li class="list-group item">
									Played: 
									<span id="games-played">${gamesPlayed}</span>
								</li>
								<li class="list-group item">
									Won: 
									<span id="games-won">${gamesWon}</span>
								</li>
								<li class="list-group item">
									Lost: 
									<span id="games-lost">${gamesLost}</span>
								</li>
							</ul>
						</div>
					</div>
					<div class="button-group">
						<button id="edit-profile" class="custom-button">
							<i class="fas fa-user-edit"></i>
						</button>
					</div>
				</div>
			</div>
		</div>
		`);
}

function profileSettingsHTML(data, avatarUrl)
{
	return(`
		<div id="profile-settings" class="container mt-4" style="font-family: 'Courier New', Courier, Monospace;">
			<div class="card mx-auto" style="max-width: 500px; background-color: #745c94;">
				<div class="card-body text-center">
					<img src="${avatarUrl}" alt="Profile Picture" class="img-thumbnail" style="background-color: #362c45; width: 70%; height: 50%;">
					<form id="profile-settings" style="padding: 30px 20px;">
						<div class="form-group row" id="usernameDiv" style="justify-content: center;">
							<label for="username" class="col-form-label">Username</label>
							<div class="col-sm-10">
								<input type="text" class="form-control" id="username" value=${data.username}>
								<span id="username-error" class="error-message"></span>
							</div>
						</div>
						<div class="form-group row" id="passwordDiv" style="justify-content: center;">
							<label for="password" class="col-form-label">Password</label>
							<div class="col-sm-10">
								<input type="password" class="form-control" id="password" placeholder="********">
								<span id="password-error" class="error-message"></span>
							</div>
						</div>
						<div class="form-group row" id="twofaDiv" style="justify-content: center;"> 
							<div class="col-sm-10" >
								<label for="twofa" class="col-form-label row" style="justify-content: center;">Activate 2FA</label>
								<input type="checkbox" id="twofa">
							</div>
						</div>
						<div class="form-group row" style="justify-content: center;">
							<label for="avatar" class="col-form-label">Change Avatar</label>
							<div class="col-sm-10">
								<input type="file" class="form-control-file" id="avatar">
							</div>
							<span id="file-error" class="error-message"></span>
							
						<!-- We need to reduce the amount of margin or space that is between the choose file button
						and the save changes button. -->
						</div>
						<span id="file-error" class="error-message"></span>
					</div>
					</form>
					<div class="button-group" style="padding: 0; margin-top: 0;">
						<button id="save-changes" class="custom-button" style="margin-top: 0;">Save Changes</button>
					</div>
				</div>
			</div>
		</div>
		`);
}

function loadGenericHTML(type)
{
	if (type === 'login')
	{
		return (`

		<div class="form-container">
			<h2 class="form-title">Log in</h2>
			<form id="login-form">
				<div class="form-group">
					<label for="username">Username</label>
					<input type="username" class="form-control" id="username" placeholder="Enter username">
						<span id="username-error" class="error-message"></span>
				</div>
				<div class="form-group">
					<label for="password">Password</label>
					<input type="password" class="form-control" id="password" placeholder="Enter password">
						<span id="password-error" class="error-message"></span>
				</div>
				<div class="form-group" id="codeDiv" style="display: none;">
					<label for="code">Auth code</label>
					<input type="code" class="form-control" id="code" placeholder="Enter auth code">
						<span id="code-error" class="error-message"></span>
				</div>
				<button class="custom-button" id="submit">Submit</button>
			</form>
		</div>
		`);
	}
	else if (type === 'signup')
	{
		return(`
			<div class="form-container">
				<h2 class="form-title">Sign Up</h2>
				<form id="signup-form">
					<div class="form-group">
						<label for="username">Username</label>
						<input type="username" class="form-control" id="username" placeholder="Enter username">
						<span id="username-error" class="error-message"></span>
					</div>
					<div class="form-group">
						<label for="email">Email</label>
						<input type="email" class="form-control" id="email" placeholder="Enter email">
						<span id="email-error" class="error-message"></span>
					</div>
					<div class="form-group">
						<label for="password">Password</label>
						<input type="password" class="form-control" id="password" placeholder="Enter password">
						<span id="password-error" class="error-message"></span>
					</div>
					<div class="form-group">
						<label for="confirm password">Password</label>
						<input type="password" class="form-control" id="confirm-password" placeholder="Confirm password">
						<span id="conf-password-error" class="error-message"></span>
					</div>
					<button class="custom-button" id="submit">Submit</button>
				</form>
			</div>
		`);
	}
}

function loadTournamentSectionHTML()
{
	return (`<div class="options-container">
				<div class="option">
					<h2>Create a Tournament</h2>
					<p>Create your own tournament and invite your friends to compete!</p>
					<button class="custom-button" id="create-btn">Create</button>
				</div>
				<div class="option">
					<h2>Join a Tournament</h2>
					<p>Join an existing tournament and compete against other players!</p>
					<button class="custom-button" id="join-btn">Join</button>
				</div>
			</div>`);
}

function loadNotFoundHTML()
{
	return(`
		<h2>Seems like there's nothing to see here...</h2>
		`);
}

function loadNotAuthorizedHTML()
{
	return(`
		<h2>Not Authorized to view this page. Please authenticate.</h2>
		`);
}

function loadInitialHTML()
{
	return(`
		<button class="custom-button" id="signup-link">Sign up</button>
		<button class="custom-button" id="login-link">Log in</button>
		<button class="custom-button" id="login42-link">42 Log in</button>
		`);
}

window.homeHTML = homeHTML;
window.profileHTML = profileHTML;
window.profileSettingsHTML = profileSettingsHTML;
window.loadGenericHTML = loadGenericHTML;
window.loadNotFoundHTML = loadNotFoundHTML;
window.loadNotAuthorizedHTML = loadNotAuthorizedHTML;
window.loadInitialHTML = loadInitialHTML;
