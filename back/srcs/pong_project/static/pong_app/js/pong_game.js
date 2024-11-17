//board

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
let board, player1, player2, ball;

function initializeGame(){
    
    // Close existing WebSocket connection if open
    if (socket) {
        socket.close();
        isSocketOpen = false;
    }
    if (!board) board = new Board(900, 500);
    if (!player1) player1 = new Player(1, board);
    if (!player2) player2 = new Player(2, board);
    if (!ball) ball = new Ball(board);
    console.log('initializeGame called');
    loadGameCanvas();
    let score1 = 0;
    let score2 = 0;
    player1.velocityY = 0;
    player2.velocityY = 0;
    userid = localStorage.getItem('userid');
    //const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    
    // TODO: generate id only when a new game is created, if not, select the id
    socket = new WebSocket('wss://' + window.location.host + '/ws/pong-socket/'  + userid + '/' + 0 + '/');
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

    socket.onmessage = function(event) {
        console.log("RECIEVING MESSAGE FROM WS!!")
        console.log(event.data)
        // Parse the JSON data received from the server
        const data = JSON.parse(event.data);

        // Update player1's position with the received data
        player1.y = data['Player1'];

        // Update player2's position with the received data
        player2.y = data['Player2'];

        ball.x = data['ballX'];
        ball.y = data['ballY'];

        score1 = data['Score1']
        score2 = data['Score2']
        update();
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
        
    function moveDjango(e){
        sendPlayerData(e.code, "move");
    }

    function stopDjango(e){
        sendPlayerData(e.code, "stop")
    }

    function sendPlayerData(keycode, action){
        console.log('!!SENDING DATA!!!');
        if (isSocketOpen) {
            socket.send(JSON.stringify({
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

        // Send ball and player data every frame
        //sendPlayerData("update");
    }
    update();
}

window.initializeGame = initializeGame;