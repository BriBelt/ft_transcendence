
function initializeTournamentGame(tournamentName){
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
    let socket;
    let isSocketOpen = false;
    let isGameSocketOpen = false;
    let gamesocket;
    let isFinalMatch = false;
    
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
    //const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    
    // TODO: generate id only when a new game is created, if not, select the id
    socket = new WebSocket('wss://' + window.location.host + '/ws/pong-socket/' + tournamentName + '/'  + userid + '/');
    //const socket = new WebSocket('ws://' + window.location.host + '/ws/pong-socket/' + id + '/');
    isSocketOpen = false;
    socket.onopen = function(event) {
        console.log("WebSocket is open now.");
//        console.log(id);
        isSocketOpen = true;
    };
    
    socket.onclose = function(event) {
        console.log("WebSocket is closed now.");
    };
    
    socket.onerror = function(error) {
        console.error("WebSocket Error: ", error);
    };

    let player1Id;
    let player2Id;
    socket.onmessage = function(event) {
//        const data = event.data;
//        console.log("received: ", data);
//        const regex = /Match between (\d+) and (\d+) is starting!/;
//        const match = data.match(regex);
//
//        // Check if the match was successful
//        if (match) {
//            player1Id = match[1];
//            player2Id = match[2];// Abre el `gamesocket` basado en los IDs de los jugadores
//            const opponentId = (player1Id === userid) ? player2Id : player1Id;
//            const gamesocketUrl = `wss://${window.location.host}/ws/pong-socket/${userid}/${opponentId}/`;
//
//            console.log("Creando gamesocket con URL:", gamesocketUrl);
//            createGameSocket(gamesocketUrl);

        const data = JSON.parse(event.data);
            
        if (data.message) {
            let matchDetails;
            if (data.message.includes("Final match between")) {
                isFinalMatch = true;  // Marcar como partida final
                matchDetails = data.message.match(/Final match between (\d+) and (\d+) is starting!/);
            } else if (data.message.includes("Match between")) {
                isFinalMatch = false;  // No es la final
                matchDetails = data.message.match(/Match between (\d+) and (\d+) is starting!/);
            }
        
            if (matchDetails) {
                player1Id = matchDetails[1];
                player2Id = matchDetails[2];
            
                // Identificar al oponente para crear el `gamesocket`
                const opponentId = (player1Id === userid) ? player2Id : player1Id;
                const gamesocketUrl = `wss://${window.location.host}/ws/pong-socket/${userid}/${opponentId}/`;
                console.log("Creando gamesocket con URL:", gamesocketUrl);
                createGameSocket(gamesocketUrl);
        };

        }
    };

    function createGameSocket(url) {
        gamesocket = new WebSocket(url);

        gamesocket.onopen = function () {
            console.log("GameWebSocket abierto");
            isGameSocketOpen = true;
        };

        gamesocket.onclose = function () {
            console.log("GameWebSocket cerrado");
            isGameSocketOpen = false;
        };

        gamesocket.onerror = function (error) {
            console.error("Error en GameWebSocket:", error);
        };

        gamesocket.onmessage = function (event) {
            //console.log("Mensaje recibido en gamesocket:", event.data);
            const data = JSON.parse(event.data);

            // Actualiza posiciones y puntajes
            player1.y = data['Player1'];
            player2.y = data['Player2'];
            ball.x = data['ballX'];
            ball.y = data['ballY'];
            score1 = data['Score1'];
            score2 = data['Score2'];
            update();
        };
    }

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
        if (gamesocket && isGameSocketOpen){
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
            socket.send(JSON.stringify({
                'type': "end_tournament",
                'winner_id': winnerId
            }));
        }
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