function signUpHandler()
{
    const signUpForm = document.getElementById('signup-form');

    if (signUpForm)
    {
        // Define the behavior for when receiving an event
        signUpForm.addEventListener('submit', function(event)
	{
            // Prevent the default behavior
            event.preventDefault();

            // Get the value for the email and password tags and set them into a variable
            const formData =
	    {
                username: document.getElementById('username').value,
                email: document.getElementById('email').value,
                password: document.getElementById('password').value,
		confPass: document.getElementById('confirm-password').value
            };

	    if (validateInput(formData, 'signup'))
	    {
                fetch('/signup/',
		{
                    method: 'POST',
                    headers:
		    {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data =>
		{
                    if (data.status == 'success')
		    {
		    	alert('Please check your email before logging in.');
			navigateTo('/login/');
                    }
		    else
                        alert('Signup failed: ' + data.message);
                })
                .catch(error =>
		{
                    console.error('Error:', error);
                });
	    }
        });
    }
    else
    {
        console.error('signup-form not found');
    }
}

function	handleInitialPage()
{
	const app = document.getElementById('app');
	const loginLink = document.getElementById('login-link');
	const signupLink = document.getElementById('signup-link');
	const login42Link = document.getElementById('login42-link');

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
}

window.signUpHandler = signUpHandler;
window.handleInitialPage = handleInitialPage;
