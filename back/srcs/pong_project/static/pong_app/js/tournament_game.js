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
    
    // Close existing WebSocket connection if open
    if (socket) {
        socket.close();
        isSocketOpen = false;
    }
    let board = new Board(900, 500);
    let player1 = new Player(1, board);
    let player2 = new Player(2, board);
    let ball = new Ball(board);
    console.log('initializeGame called');
    loadGameCanvas();
    let score1 = 0;
    let score2 = 0;
    player1.velocityY = 0;
    player2.velocityY = 0;
    userid = localStorage.getItem('userid');
    console.log(`User ID from localStorage: ${userid}`);
    //const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    
    // TODO: generate id only when a new game is created, if not, select the id
    socket = new WebSocket('wss://' + window.location.host + '/ws/pong-socket/' + tournamentName + '/'  + userid + '/');
    //const socket = new WebSocket('ws://' + window.location.host + '/ws/pong-socket/' + id + '/');
    isSocketOpen = false;
    socket.onopen = function(event) {
        console.log("Tournament webSocket is open now.");
//        console.log(id);
        isSocketOpen = true;
    };
    
    socket.onclose = function(event) {
        console.log("Tournament webSocket is closed now.");
        isSocketOpen = false;
        if (isFinalMatch == true){
            initializeTournamentGame();
        }
    };
    
    socket.onerror = function(error) {
        console.error("WebSocket Error: ", error);
    };

    let player1Id;
    let player2Id;
    socket.onmessage = function(event) {

        const data = JSON.parse(event.data);

        console.log(data);

        if (data.message){
            if (data.message.includes("Tournament is over")){
                localStorage.removeItem('tournament_name');
            }
            if (data.message.includes("Winner")){
                winnerDetails = data.message.match(/Winner (\d+)/);
                const winnerId = winnerDetails ? parseInt(winnerDetails[1], 10) : null;
                console.log(`Winner ${winnerId}`)
                console.log(`Player ${userid}`)
                //alert(`Winner ${winnerId}`)//Q
                if (score1 === 7) displayWinnerBanner("Player 1");
                if (score2 === 7) displayWinnerBanner("Player 2");
                if (parseInt(userid, 10) == parseInt(winnerId, 10)){
                    isFinalMatch = true;
                    //isSocketOpen = false;
                    console.log("Preparando partida final...");
                    //socket.close();
                }
            }
            if (data.type === "announcement") {
                gameStarted = true;
                const announcement = data.message;
                console.log(announcement);
        
                // Muestra el mensaje en la interfaz
                displayAnnouncement(data.player1_username, data.player2_username, data.tournament_name);
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
        if (isFinalMatch) {
            if (isSocketOpen){
                socket.send(JSON.stringify({
                    'type': "end_tournament",
                    'winner_id': winnerId
                }));
            }
            else if (isGameSocketOpen){
                gamesocket.send(JSON.stringify({
                    'type': "end_tournament",
                    'winner_id': winnerId
                }));
            }
            }
        gameStarted = false;
    }

    function displayAnnouncement(player1, player2, t_name) {
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
            
    function update() {
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
            if (score1 == 7){
                displayWinnerBanner("Player 1");
                if (userid === player1Id)
                    console.log("eliminar esta linea es solo debug")
                    // Logic to show "Next Game" button
                else
                    console.log("eliminar esta linea es solo debug")    
                    // Logic to send back to tthe main menu 
            }
            else{
                displayWinnerBanner("Player 2");
                if (userid === player2Id)
                    console.log("eliminar esta linea es solo debug")
                    // Logic to show "Next Game" button
                else
                    console.log("eliminar esta linea es solo debug")    
                    // Logic to send back to tthe main menu
            }
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
