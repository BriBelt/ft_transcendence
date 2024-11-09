document.addEventListener('DOMContentLoaded', function() {
    const app = document.getElementById('app');
    const loginLink = document.getElementById('login-link');
    const signupLink = document.getElementById('signup-link');
    const login42Link = document.getElementById('login42-link');
	const logoutLink = document.getElementById('logout-link');
	const navbarLinks = document.querySelectorAll('.explore-navbar-nav .nav-link');// the selector will only select those elements that are descendants of an element that has the class explore-navbar-nav
	// Event listenner in charge of navigating as a SPA
    navbarLinks.forEach(link =>
	{
        link.addEventListener('click', function(event)
		{
            event.preventDefault();// Avoid recharging page
            const targetPath = event.target.getAttribute('data-path');  // Obtain path
            navigateTo(targetPath);
        });
    });

//	This event listener is in charge of receiving any event regarding the 
//	browser buttons (forward/backward/refresh)
	window.addEventListener('popstate', function(event)
	{
		loadPage(window.location.pathname + window.location.search);
	});

	if (loginLink)
	{
		loginLink.addEventListener('click', function(event)
		{
			event.preventDefault();
			navigateTo('/login/');
		});
	}

	if (signupLink)
	{
		signupLink.addEventListener('click', function(event)
		{
			event.preventDefault();
			navigateTo('/signup/');
		});
	}

	if (login42Link)
	{
		login42Link.addEventListener('click', async function(event)
		{
			alert('clicked 42 auth');
			event.preventDefault();
			await handleAuth();
		});
	}
	if (logoutLink)
	{
		logoutLink.addEventListener('click', function(event)
		{
		    event.preventDefault();
		    logoutUser();
		});
	}
	updateLogoutButtonVisibility();
	loadPage(window.location.pathname + window.location.search);
});
