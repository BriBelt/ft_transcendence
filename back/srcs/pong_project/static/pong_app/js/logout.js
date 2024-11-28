async function updateLogoutButtonVisibility()
{
    if (window.location.pathname.startsWith('/callback.html'))
    	return;
    const logoutItem = document.getElementById('display-item');
    const token = localStorage.getItem('access');

    if (token)
    {
        try
        {
            // Fetch user info to check if the user is online
            const response = await fetch('/get_user_info/',
    	    {
                method: 'GET',
                headers:
    	    {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            })
            const data = await response.json();
            if (data.status === 'success' && data.is_online)
    	    {
                    // If the user is online, show the Logout button
                    logoutItem.classList.remove('d-none');
            }
    	    else
    	    {
                // Hide the Logout button if the user is not online
                logoutItem.classList.add('d-none');
                // If access expired try to get new one if posible
                if (data.message === 'Access unauthorized')
                {
                    const result = await checkRefreshToken(token);
                    if (result === "valid")
                    {
                        logoutItem.classList.remove('d-none');
                    }
                }
            }
            
        }
        catch(error)
    	{
            console.error('Error:', error);
            // Hide the Logout button in case of error
            logoutItem.classList.add('d-none');
            // If refresh just expired expel user
            notAuthorized(error);
        }
    }
    else
    {
        // Hide the Logout button if no token is found
        logoutItem.classList.add('d-none');
    }
}

async function logoutUser()
{
    const token = localStorage.getItem('access');
    if (token)
    {
        try
        {
            const response = await fetch('/logout/',
    	    {
                method: 'POST',
                headers:
    	        {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
    	        credentials: 'include',
            })
            const data = await response.json();
            if (data.status === 'success')
    	    {
                    localStorage.removeItem('access');
                    navigateTo('/');
            }
    	    else
    	    {
                if (data.message === 'Access unauthorized')
                {
                    const result = await checkRefreshToken(token);
                    if (result === "valid")
                    {
                        logoutUser();
                    }
                }
    	    	else
    		    {
                    if (localStorage.getItem('access'))
                    {
                        localStorage.removeItem('access');
                        navigateTo('/');
                    }
    		    }
    	    }
        }
        catch(error)
	    {
            console.error('Error during logout:', error);
            notAuthorized(error);
        }
    }
    else
    	notAuthorized();

}

window.updateLogoutButtonVisibility = updateLogoutButtonVisibility
window.logoutUser = logoutUser
