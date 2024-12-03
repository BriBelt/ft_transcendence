function loadPage(url, data)
{
	if (url && (url.includes('callback.html') || url.includes('access=')))
		return;
	else if (url == '/' || url == '')
		loadInitialPage();
	else if (url == '/home/')
		loadHome();
	else if (url == '/home/users/')
		loadUsers();
	else if (url == '/home/users/user/')
		loadOtherUserProfile();
	else if (url  == '/login/')
		loadLoginForm();
	else if (url  == '/signup/')
		loadSignupForm();
	else if (url  == '/signup/email/activate/')
		loadLoginForm();
	else if (url  == '/home/profile/')
		loadProfile(data);
	else if (url  == '/home/profile/edit/')
		loadProfileSettings();
	else if (url === '/home/game/')
		loadPlayGame();
	else if (url === '/home/game/local/')
		initializeLocalGame();
	else if (url === '/home/game/online/')
		initializeGame();
	else if (url === '/home/game/tournament/')
		loadTournamentSection();
	else if (url === '/home/game/tournament/join/')
		loadTournamentsSection();
	else if (url === '/home/game/tournament/create/')
		loadCreateTournament();
	else if (url === '/home/game/tournament/t_game/')
		initializeTournament();
	else if (url === '/home/friends/')
		loadFriendsSection();
	else 
		loadNotFound();
}

function navigateTo(url, data)
{
	window.history.pushState({}, '', url);
	loadPage(url, data);
	updateLogoutButtonVisibility();
}

window.loadPage = loadPage;
window.navigateTo = navigateTo;
