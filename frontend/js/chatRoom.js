$(document).ready(function () {
    const token = localStorage.getItem('token'); // Retrieve token from local storage
    const room = localStorage.getItem('room');
    console.log(token)
    console.log(room)
    const socket = new WebSocket('ws://localhost:8000/ws/call-center/room?token=' + token + '&room=' + room);

    socket.onopen = function () {
        console.log('WebSocket connection established.');
    };

    socket.onclose = function () {
        window.history.back()
    }
    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        //console.log(data)
        if (data.message) {
            displayChatMessage(data.message);
        } else if (data.messages) {
            localStorage.setItem('code', data.close_code);
            const chatMessagesElement = $('#chat-messages');
            chatMessagesElement.empty();
            data.messages.forEach((message) => displayChatMessage(message.sender + ": " + message.content));
        }
    };


    // Handle message form submission
    $('#message-form').submit(function (event) {
        event.preventDefault();
        const message_input = $('#message-input');
        socket.send(JSON.stringify({
            'type': 'chat_message',
            'content': message_input.val(),
        }));
        message_input.val('');
    });

    $('#close_button').click(function () {
        console.log("close button clicked")
        let code = localStorage.getItem('code')
        socket.close(parseInt(code));
    });

    // Display chat messages
    function displayChatMessage(message) {
        const chatMessagesElement = $('#chat-messages');
        chatMessagesElement.append('<p>' + message + '</p>');
        chatMessagesElement.scrollTop(chatMessagesElement.prop('scrollHeight'));
    }
});