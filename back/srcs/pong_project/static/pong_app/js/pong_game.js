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
let board = new Board(900, 500);
let player1 = new Player(1, board);
let player2 = new Player(2, board);
let ball = new Ball(board);



function initializeGame(){
    player1.velocityY = 0;
    player2.velocityY = 0;
    const socket = new WebSocket('ws://' + window.location.host + '/ws/pong-socket/');
    socket.onopen = function(event) {
        console.log("WebSocket is open now.");
    };
    
    socket.onclose = function(event) {
        console.log("WebSocket is closed now.");
    };
    
    socket.onerror = function(error) {
        console.error("WebSocket Error: ", error);
    };

    socket.onmessage = function(event) {
        // Parse the JSON data received from the server
        const data = JSON.parse(event.data);

        // Update player1's position with the received data
        player1.y = data['Player1'];

        // Update player2's position with the received data
        player2.y = data['Player2'];

        ball.x = data['ballX'];
        ball.y = data['ballY'];

        console.log(player2.y);
        console.log(ball.x);
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

    document.addEventListener("keyup", moveDjango);
    document.addEventListener("keydown", stopDjango);
        
    function moveDjango(e){
        sendPlayerData(e.code, "move");
    }

    function stopDjango(e){
        sendPlayerData(e.code, "stop")
    }

    function sendPlayerData(keycode, action){
        socket.send(JSON.stringify(
        {
            'key': keycode,
            'action': action
        }))
    }
            
    function update() {
        //requestAnimationFrame(update);
        context.clearRect(0, 0, board.width, board.height);

        // draw players
        context.fillStyle = "skyblue";
        context.fillRect(player1.x, player1.y, player1.width, player1.height);
        context.fillRect(player2.x, player2.y, player2.width, player2.height);

        //ball
        context.fillStyle = "White"
        context.fillRect(ball.x, ball.y, ball.width, ball.height);

        // Send ball and player data every frame
        sendPlayerData("update");
    }
    update();
}

window.initializeGame = initializeGame;