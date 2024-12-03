async function initializeTournament()
{
	const app = document.getElementById('app');
	const token = localStorage.getItem('access');
	if (token)
	{
		try
		{
			const response = await fetch('/home/game/tournament/t_game',
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
				initializeTournamentGame();
			}
			else
				await checkRefreshToken(token);
		}
		catch(error)
		{
			alert('Uh-oh! There was an unexpected error.');
			notAuthorized(error);
		}
	}
	else
	{
		notAuthorized(error);
	}
}


function initializeTournamentGame(){
    const tournamentName = localStorage.getItem('tournament_name');

    const accessToken = localStorage.getItem('access');
	if (!accessToken)
	{
        alert('No access token found. Please log in.');
        return;
    }

    if (!tournamentName)
        return;
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
    let gamesocket = null;
    let isGameSocketOpen = false;
    let isSocketOpen = false;
    let isFinalMatch = false;
    let gameStarted = false;
    let announcementShown = localStorage.getItem('announcementShown') === 'true';
    let no_refreshed_aShown = false;

    let waitingForOpponent;
    if (localStorage.getItem('waitingForOpponent') !== null) {
        waitingForOpponent = localStorage.getItem('waitingForOpponent') === 'true';
    } else {
        waitingForOpponent = true;
        localStorage.setItem('waitingForOpponent', 'true');
    }
    
    // Close existing WebSocket connection if open
    if (socket) {
        socket.close();
        isSocketOpen = false;
    }
    let board = new Board(900, 500);
    let player1 = new Player(1, board);
    let player2 = new Player(2, board);
    let ball = new Ball(board);
    loadGameCanvas();
    let score1 = 0;
    let score2 = 0;
    player1.velocityY = 0;
    player2.velocityY = 0;
    userid = localStorage.getItem('userid');
    
    socket = new WebSocket('wss://' + window.location.host + '/ws/pong-socket/' + tournamentName + '/'  + accessToken + '/');
    isSocketOpen = false;
    socket.onopen = function(event) {
        isSocketOpen = true;
    };
    
    socket.onclose = function(event) {
        isSocketOpen = false;
        if (isFinalMatch == true){
            initializeTournamentGame();
        }
    };
    
    socket.onerror = function(error) {
	alert('Uh-oh! There was an unexpected error.');
    };

    let player1Id;
    let player2Id;
    socket.onmessage = function(event) {

        const data = JSON.parse(event.data);

        if (data.message){
            if (data.type === 'error' && data.message === 'authentication_failed') {
                alert('Authentication failed. Please log in again.');
                socket.close();
                return;
            }
            if (data.message.includes("Tournament is over")){
                localStorage.removeItem('tournament_name');
            }
            if (data.message.includes("Winner")){
                winnerDetails = data.message.match(/Winner (\d+)/);
                const winnerId = winnerDetails ? parseInt(winnerDetails[1], 10) : null;
                if (score1 === 7) displayWinnerBanner("Player 1");
                if (score2 === 7) displayWinnerBanner("Player 2");
                if (parseInt(userid, 10) == parseInt(winnerId, 10)){
                    isFinalMatch = true;
                }
            }
            if (data.type === "announcement") {
                gameStarted = true;
                const announcement = data.message;
                // Muestra el mensaje en la interfaz
                displayAnnouncement(data.player1_username, data.player2_username, data.tournament_name);
                localStorage.setItem('announcementShown', 'true');
			    no_refreshed_aShown = true;
                waitingForOpponent = false;
                localStorage.setItem('waitingForOpponent', 'false');
            }
        }
        else{
            // Actualiza posiciones y puntajes
            player1.y = data['Player1'];
            player2.y = data['Player2'];
            ball.x = data['ballX'];
            ball.y = data['ballY'];
            score1 = data['Score1'];
            score2 = data['Score2'];
            update();
        }
    };


    // Funciones de movimiento
    document.removeEventListener("keyup", stopDjango);
    document.removeEventListener("keydown", moveDjango);


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

    if (waitingForOpponent)
		displayWaitingMessage();
        
    function moveDjango(e){
        sendPlayerData(e.code, "move");
    }

    function stopDjango(e){
        sendPlayerData(e.code, "stop")
    }

    function sendPlayerData(keycode, action){
        if (!gameStarted)
            return;
        if (socket && isSocketOpen){
            socket.send(JSON.stringify({
                'position': {
                    'key': keycode,// ArrowUp or ArrowDown
                    'action': action//"move" or "stop"
                }
            }));
        }
        else if (gamesocket && isGameSocketOpen){
            gamesocket.send(JSON.stringify({
                'position': {
                    'key': keycode,// ArrowUp or ArrowDown
                    'action': action//"move" or "stop"
                }
            }));
        }
    }

    function displayWinnerBanner(winner) {
        context.fillStyle = "white";
        context.font = "50px Arial";
        const text = `${winner} Wins!`;
        // Measure the text width to center it
        const textWidth = context.measureText(text).width;
        // Clear the canvas for the banner
        context.clearRect(0, 0, canvas.width, canvas.height);
        // Draw the banner in the center of the canvas
        context.fillText(text, (canvas.width / 2) - (textWidth / 2), canvas.height / 2);

        const winnerId = (score1 === 7) ? player1Id : player2Id;
        // is its a final, notify TournamentConsumer to save data
        //if (isFinalMatch) {
        //    if (isSocketOpen){
        //        socket.send(JSON.stringify({
        //            'type': "end_tournament",
        //            'winner_id': winnerId
        //        }));
        //    }
        //    else if (isGameSocketOpen){
        //        gamesocket.send(JSON.stringify({
        //            'type': "end_tournament",
        //            'winner_id': winnerId
        //        }));
        //    }
        //    }
        gameStarted = false;
        localStorage.setItem('announcementShown', 'false');
		no_refreshed_aShown = false;
    }

    function displayAnnouncement(player1, player2, t_name) {
        if (announcementShown || no_refreshed_aShown) return;
        const originalUpdate = update; // Guarda una referencia al método original de actualización

        // Desactiva temporalmente el método de actualización
        update = function() {};

        context.fillStyle = "white";
        context.font = "40px Arial";
        const text = `${t_name}'s tournament match: ${player1} vs ${player2}`;
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

    function displayWaitingMessage() {
		if (!waitingForOpponent) return;
		context.clearRect(0, 0, board.width, board.height);
		context.fillStyle = "white";
		context.font = "30px Arial";
		const text = "Waiting for an opponent...";
		const textWidth = context.measureText(text).width;
		context.fillText(text, (board.width / 2) - (textWidth / 2), board.height / 2);
	}
            
    function update() {
        if (!gameStarted) return;
        //requestAnimationFrame(update);
        context.clearRect(0, 0, board.width, board.height);
        context.fillStyle = "Black";
        context.fillRect(0, 0, board.width, board.height);

        // draw players
        context.fillStyle = "skyblue";
        context.fillRect(player1.x, player1.y, player1.width, player1.height);
        context.fillRect(player2.x, player2.y, player2.width, player2.height);

        //ball
        context.fillStyle = "White"
        context.fillRect(ball.x, ball.y, ball.width, ball.height);
        if (score1 == 7 || score2 == 7)
        {
            if (score1 == 7)
                displayWinnerBanner("Player 1");
            else
                displayWinnerBanner("Player 2");
        }
        else{
            context.fillText(score1.toString(), (board.width / 4), board.height/2);
            context.fillText(score2.toString(), (board.width / 4) * 3, board.height/2);
            context.font = '50px Arial';
        }
    }
    update();
}

window.initializeTournamentGame = initializeTournamentGame;
window.initializeTournament = initializeTournament;
