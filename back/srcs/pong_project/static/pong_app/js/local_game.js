// boardL
class BoardL {
    constructor(width = 900, height = 500) {
        this.width = width;
        this.height = height;
    }
}

// players
class PlayerL {
    constructor(number, boardL) {
        this.width = boardL.width / 50;
        this.height = this.width * 5;
        this.velocityY = 0;
        this.score = 0;
        if (number === 1) {
            this.x = 10;
            this.y = (boardL.height / 2) - (this.height / 2);
        } else {
            this.x = boardL.width - (this.width * 2);
            this.y = (boardL.height / 2) - (this.height / 2);
        }
    }

    move() {
        this.y += this.velocityY;
    }

    // Prevent player from going out of bounds
    constrain(boardL) {
        if (this.y < 0) {
            this.y = 0;
        } else if (this.y + this.height > boardL.height) {
            this.y = boardL.height - this.height;
        }
    }
}

// ballL
class BallL {
    constructor(boardL) {
        this.width = boardL.width / 50;
        this.height = this.width;
        this.x = (boardL.width / 2) - (this.height / 2);
        this.y = (boardL.height / 2) - (this.height / 2);
        this.velocityX = 5;
        this.velocityY = 3;
    }

    move() {
        this.x += this.velocityX;
        this.y += this.velocityY;
    }

    // Ball bounce logic
    bounce(boardL, player1L, player2L) {
        // Bounce off top and bottom
        if (this.y <= 0 || this.y + this.height >= boardL.height) {
            this.velocityY = -this.velocityY;
        }

        // Check if the ballL hits player 1
        if (this.x <= player1L.x + player1L.width && this.y + this.height >= player1L.y && this.y <= player1L.y + player1L.height) {
			const paddleCenter = player1L.y + player1L.height / 2; // Centro de la pala
			const hitPos = (this.y - paddleCenter) / (player1L.height / 2); // Posición de impacto normalizada

			this.velocityY += hitPos * 3; // Modificar la velocidad vertical según el impacto

			// Ajustar la posición para evitar que la pelota se atasque en la pala
			this.x = player1L.x + player1L.width + 1;
            this.velocityX = -this.velocityX;
        }

        // Check if the ballL hits player 2
        if (this.x + this.width >= player2L.x && this.y + this.height >= player2L.y && this.y <= player2L.y + player2L.height) {
            const paddleCenter = player2L.y + player2L.height / 2; // Centro de la pala
			const hitPos = (this.y - paddleCenter) / (player2L.height / 2); // Posición de impacto normalizada

			this.velocityY += hitPos * 3; // Modificar la velocidad vertical según el impacto

			// Ajustar la posición para evitar que la pelota se atasque en la pala
			this.x = player2L.x - this.width - 1;
			this.velocityX = -Math.abs(this.velocityX);
        }

        //// Reset ballL position if it goes off screen (left or right)
        //if (this.x <= 0 || this.x >= boardL.width) {
        //    this.x = (boardL.width / 2) - (this.width / 2);
        //    this.y = (boardL.height / 2) - (this.height / 2);
        //    this.velocityX = -this.velocityX; // Reverse direction on reset
        //}

        // Check if scored
        this.score(player1L, player2L, boardL);
    }
    // Check for scoring
    score(player1L, player2L, boardL) {
        if (this.x <= 0) {
            // Gol del jugador 2
            player2L.score += 1;
            this.resetPosition(boardL);
            } else if (this.x >= boardL.width) {
                // Gol del jugador 1
            player1L.score += 1;
            this.resetPosition(boardL);
        }
    }

    // Reset ballL position to center
    resetPosition(boardL) {
        this.x = (boardL.width / 2) - (this.width / 2);
        this.y = (boardL.height / 2) - (this.height / 2);
        this.velocityX = -this.velocityX; // Cambiar la dirección tras un gol
    }
}

let contextL;
let boardL = new BoardL(900, 500);
let player1L = new PlayerL(1, boardL);
let player2L = new PlayerL(2, boardL);
let ballL = new BallL(boardL);
let running = false;
let game_ended = false;

function saveLocalGameState()
{
	const gameState =
	{
		player1Score: player1L.score,
		player2Score: player2L.score,
		player1Position: player1L.y,
		player2Position: player2L.y,
		ballPosition:
		{
			x: ballL.x, y: ballL.y
		},
		ballVelocity:
		{
			x: ballL.velocityX, y: ballL.velocityY
		},
		playing: localStorage.getItem('playing')
	};
	localStorage.setItem('state', JSON.stringify(gameState));
}

function loadLocalGameState()
{
	const savedState = JSON.parse(localStorage.getItem('state'));
	if (savedState)
	{
		player1L.score = savedState.player1Score;
		player2L.score = savedState.player2Score;
		player1L.y = savedState.player1Position;
		player2L.y = savedState.player2Position;
		ballL.x = savedState.ballPosition.x;
		ballL.y = savedState.ballPosition.y;
		ballL.velocityX = savedState.ballVelocity.x;
		ballL.velocityY = savedState.ballVelocity.y;
		localStorage.setItem('playing', savedState.playing);
	}
}

function clearLocalGameState()
{
	localStorage.removeItem('state');
	localStorage.setItem('playing', 'false');
}

async function startLocalGame()
{
	if (running){
		running = false;
		await new Promise((resolve) => setTimeout(resolve, 50)); // Espera un frame antes de reiniciar
	}

	running = true;

	if (game_ended)
	{
		//Restore objects if it's a new game
		player1L = new PlayerL(1, boardL);
    	player2L = new PlayerL(2, boardL);
    	ballL = new BallL(boardL);
		game_ended = false;
	}

	const playing = localStorage.getItem('playing');
	if (playing === 'true')
	{
		loadLocalGameState();
	}
	else
		localStorage.setItem('playing', 'true');
	loadGameCanvas();
	let canvas = document.getElementById("board");
	contextL = canvas.getContext("2d");
	canvas.width = boardL.width;
	canvas.height = boardL.height;

	// Control players using keyboardL
	document.addEventListener("keydown", movePlayer);
	document.addEventListener("keyup", stopPlayer);

	// Start the game loop
	gameLoop();


	// Move players based on keyboardL input
	function movePlayer(e)
	{
		switch (e.code)
		{
			// Player 1 controls (W and S)
			case "KeyW":
				player1L.velocityY = -5;
				break;
			case "KeyS":
				player1L.velocityY = 5;
				break;
			// Player 2 controls (Arrow Up and Arrow Down)
			case "ArrowUp":
				player2L.velocityY = -5;
				break;
			case "ArrowDown":
				player2L.velocityY = 5;
				break;
		}
	}

	// Stop players when keys are released
	function stopPlayer(e)
	{
		switch (e.code) 
		{
		    case "KeyW":
		    case "KeyS":
			player1L.velocityY = 0;
			break;

		    case "ArrowUp":
		    case "ArrowDown":
			player2L.velocityY = 0;
			break;
		}
	}

	function displayWinnerBanner(winner)
	{
		contextL.fillStyle = "white";
		contextL.font = "50px Arial";
		const text = `${winner} Wins!`;
		// Measure the text width to center it
		const textWidth = contextL.measureText(text).width;
		// Clear the canvas for the banner
		contextL.clearRect(0, 0, canvas.width, canvas.height);
		// Draw the banner in the center of the canvas
		contextL.fillText(text, (canvas.width / 2) - (textWidth / 2), canvas.height / 2);
	 }

	 function checkEndGame(player1L, player2L)
	 {
		if (player1L.score === 7)
		{
		    displayWinnerBanner("Player 1");
		    clearLocalGameState();
		    running = false;
			game_ended = true;
			//playing = 'false';
		}
		else if (player2L.score === 7)
		{
			displayWinnerBanner("Player 2");
			clearLocalGameState();
			running = false;
			game_ended = true;
			//playing = 'false';
		}
	 }

	    // Game loop to update positions and render the game
	 function gameLoop()
	 {
		if (!running) return;

		const playing = localStorage.getItem('playing');
	 	if (playing !== 'True')
		{
			contextL.clearRect(0, 0, boardL.width, boardL.height);
			contextL.fillStyle = "Black";
			contextL.fillRect(0, 0, boardL.width, boardL.height);
			localStorage.setItem('playing', 'true');
		}
		else
			loadLocalGameState();

		// Move and constrain players
		player1L.move();
		player1L.constrain(boardL);
		player2L.move();
		player2L.constrain(boardL);

		// Move and bounce the ballL
		ballL.move();
		ballL.bounce(boardL, player1L, player2L);

		// Draw players
		contextL.fillStyle = "skyblue";
		contextL.fillRect(player1L.x, player1L.y, player1L.width, player1L.height);
		contextL.fillRect(player2L.x, player2L.y, player2L.width, player2L.height);

		// Draw ballL
		contextL.fillStyle = "White";
		contextL.fillRect(ballL.x, ballL.y, ballL.width, ballL.height);

		// Display scores
		contextL.font = "30px Arial";
		contextL.fillStyle = "white";
		contextL.fillText("Player 1: " + player1L.score, 50, 50);
		contextL.fillText("Player 2: " + player2L.score, boardL.width - 200, 50);

		checkEndGame(player1L, player2L);
		saveLocalGameState();

		// Continuously call gameLoop
		if (running)
			requestAnimationFrame(gameLoop);
	 }
}

async function initializeLocalGame()
{
	const app = document.getElementById('app');
	const token = localStorage.getItem('access');
	const playing = localStorage.getItem('playing');

	if (token)
	{
		try
		{
			const response = await fetch('/home/game/local/',
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
				startLocalGame();
			else
				await checkRefreshToken(token);
		}
		catch(error)
		{
			notAuthorized(error);
		}
	}
	else
	{
		notAuthorized(error);
	}
}

window.initializeLocalGame = initializeLocalGame;
