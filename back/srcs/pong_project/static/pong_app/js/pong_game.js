class Board{
    constructor(width=900, height=500){
        this.width = width;
        this.height = height;
    }
}
        
//players
class Player{
    constructor(number, board){
        this.width = board.width / 50;
        this.height = this.width * 5;
        this.velocityY = 0;
		this.score = 0;
        if (number == 1){
            this.x = 10;
            this.y = (board.height / 2) - (this.height / 2);
        }
        else{
            this.x = board.width - (this.width * 2);
            this.y = (board.height / 2) - (this.height / 2);
        }
    }
}
                        
//ball
class Ball{
    constructor(board){
        this.width = board.width / 50;
        this.height = this.width;
        this.x = (board.width / 2) - (this.height / 2);
        this.y = (board.height / 2) - (this.height / 2);
        this.velocityX = 1;
        this.velocityY = 2;
    }
}

let context;
let isSocketOpen = false;
let qMatchStarted = false;

let board = new Board(900, 500);
let player1 = new Player(1, board);
let player2 = new Player(2, board);
let ball = new Ball(board);

function saveOnlineGameState()
{
	const gameState =
	{
		player1Score: player1.score,
		player2Score: player2.score,
		player1Position: player1.y,
		player2Position: player2.y,
		ballPosition:
		{
			x: ball.x, y: ball.y
		},
		ballVelocity:
		{
			x: ball.velocityX, y: ball.velocityY
		},
		playing: localStorage.getItem('playing')
	};
	localStorage.setItem('state', JSON.stringify(gameState));
}

function loadOnlineGameState()
{
	const savedState = JSON.parse(localStorage.getItem('state'));
	if (savedState)
	{
		player1.score = savedState.player1Score;
		player2.score = savedState.player2Score;
		player1.y = savedState.player1Position;
		player2.y = savedState.player2Position;
		ball.x = savedState.ballPosition.x;
		ball.y = savedState.ballPosition.y;
		ball.velocityX = savedState.ballVelocity.x;
		ball.velocityY = savedState.ballVelocity.y;
		localStorage.setItem('playing', savedState.playing);
	}
}

function clearOnlineGameState()
{
	localStorage.removeItem('state');
	localStorage.setItem('playing', 'false');
}

async function startOnlineGame()
{
	// Close existing WebSocket connection if open
	const playing = localStorage.getItem('playing');

	if (socket)
	{
		socket.close();
		isSocketOpen = false;
	}
	if (playing === 'true')
	{
		loadOnlineGameState();
	}
	else
	{
		player1.score = 0;
		player2.score = 0;
		player1.velocityY = 0;
		player2.velocityY = 0;
	}
	loadGameCanvas();
	userid = localStorage.getItem('userid');

	// TODO: generate id only when a new game is created, if not, select the id
	socket = new WebSocket('wss://' + window.location.host + '/ws/pong-socket/'  + userid + '/');	//const socket = new WebSocket('ws://' + window.location.host + '/ws/pong-socket/' + id + '/');
	isSocketOpen = false;

	socket.onopen = function(event)
	{
		isSocketOpen = true;
	};
	socket.onerror = function(error)
	{
		alert('Uh-oh! There was an unexpected error.');
		console.error('Error: ' + error);
	};

	socket.onmessage = function(event)
	{
		const data = JSON.parse(event.data);

		if (data.type === "announcement")
		{
			qMatchStarted = true;
            const announcement = data.message;
    
            // Muestra el mensaje en la interfaz
            displayAnnouncement(data.player1_username, data.player2_username);
		}
		else
		{
			// Parse the JSON data received from the server
			const data = JSON.parse(event.data);

			// Update player1's position with the received data
			player1.y = data['Player1'];

			// Update player2's position with the received data
			player2.y = data['Player2'];

			ball.x = data['ballX'];
			ball.y = data['ballY'];

			player1.score = data['Score1']
			player2.score = data['Score2']
			update();
		}
	}

	let canvas = document.getElementById("board");
	context = canvas.getContext("2d");

	// draw players
	context.fillStyle = "skyblue";
	canvas.width = board.width;
	canvas.height = board.height;
	context.fillRect(player1.x, player1.y, player1.width, player1.height);
	context.fillRect(player2.x, player2.y, player2.width, player2.height);

	document.removeEventListener("keyup", stopDjango);  // Remove previous event listeners
	document.removeEventListener("keydown", moveDjango);

	document.addEventListener("keyup", stopDjango);
	document.addEventListener("keydown", moveDjango);
	
	function moveDjango(e)
	{
		sendPlayerData(e.code, "move");
	}

	function stopDjango(e)
	{
		sendPlayerData(e.code, "stop")
	}

	function sendPlayerData(keycode, action)
	{
		if (!qMatchStarted)
			return;
		if (isSocketOpen)
		{
			socket.send(JSON.stringify(
			{
				'position':
				{
					'key': keycode,// ArrowUp or ArrowDown
					'action': action//"move" or "stop"
				}
			}));
		}
	}

	function displayWinnerBanner(winner)
	{
		context.fillStyle = "white";
		context.font = "50px Arial";
		const text = `${winner} Wins!`;
		// Measure the text width to center it
		const textWidth = context.measureText(text).width;
		// Clear the canvas for the banner
		context.clearRect(0, 0, canvas.width, canvas.height);
		// Draw the banner in the center of the canvas
		context.fillText(text, (canvas.width / 2) - (textWidth / 2), canvas.height / 2);
		qMatchStarted = false;
	}

	function displayAnnouncement(player1, player2) {
        const originalUpdate = update; // Guarda una referencia al método original de actualización

        // Desactiva temporalmente el método de actualización
        update = function() {};

        context.fillStyle = "white";
        context.font = "40px Arial";
        const text = `Quick match: ${player1} vs ${player2}`;
        const textWidth = context.measureText(text).width;
    
        // Limpiar el canvas para el anuncio
        context.clearRect(0, 0, canvas.width, canvas.height);
    
        // Mostrar el anuncio en el centro del canvas
        context.fillText(text, (canvas.width / 2) - (textWidth / 2), canvas.height / 2);
    
        // Remover el anuncio después
        setTimeout(() => {
            update = originalUpdate; // Restaura el método de actualización original
            update();
        }, 1900);
    }
	    
	function update()
	{
		if (!qMatchStarted)
			return;
		saveOnlineGameState();
		//requestAnimationFrame(update);
		context.clearRect(0, 0, board.width, board.height);
		context.fillStyle = "Black";
		context.fillRect(0, 0, board.width, board.height);

		// draw players
		loadOnlineGameState();
		context.fillStyle = "skyblue";
		context.fillRect(player1.x, player1.y, player1.width, player1.height);
		context.fillRect(player2.x, player2.y, player2.width, player2.height);

		//ball
		context.fillStyle = "White"
		context.fillRect(ball.x, ball.y, ball.width, ball.height);
		if (player1.score == 7 || player2.score == 7)
		{
			if (player1.score == 7)
				displayWinnerBanner("Player 1");
			else
				displayWinnerBanner("Player 2");
			clearOnlineGameState();
		}
		else
		{
			context.fillText(player1.score.toString(), (board.width / 4), board.height/2);
			context.fillText(player2.score.toString(), (board.width / 4) * 3, board.height/2);
			context.font = '50px Arial';
		}

		// Send ball and player data every frame
		//sendPlayerData("update");
	}
	update();
}


async function initializeGame()
{
	const app = document.getElementById('app');
	const token = localStorage.getItem('access');
	if (token)
	{
		try
		{
			const response = await fetch('/home/game/online/',
			{
				method: 'GET',
				headers:
				{
					'Authorization': `Bearer ${token}`,
					'Content-Type': 'application/json'
				}
			});
			const data = await response.json();
			if (data.status === 'success')
			{
				startOnlineGame();
			}
			else
			{
				if (data.message.includes('User has joined a tournament'))
					alert('You have already joined a tournament, you must play one game at a time.');
				else
					await checkRefreshToken(token);
			}
		}
		catch(error)
		{
			alert('Uh-oh! There was an unexpected error.');
			console.error('Error: ' + error);
			notAuthorized(error);
		}
	}
	else
	{
		notAuthorized(error);
	}
}

window.startOnlineGame = startOnlineGame;
window.initializeGame = initializeGame;
