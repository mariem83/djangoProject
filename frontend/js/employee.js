$(document).ready(function () {
    const rooms_map = new Map();
    const token = localStorage.getItem('token'); // Retrieve token from local storage
    // WebSocket connection
    const socket = new WebSocket('ws://localhost:8000/ws/call-center/queue?token=' + token);

    socket.onopen = function () {
        console.log('WebSocket connection established.');
    };

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        const messageType = data.type;

        if (messageType === 'call_queue_status') {
            console.log(data)
            displayCallQueue(data.call_queue);
        }
    };


    socket.onclose = function (){
        console.log('WebSocket connection closed')
        //window.history.back()
    }

    $('#call-queue-list').on('click', '.list-group-item', function (event) {
        // Handle the click event here
        console.log('Clicked room:', $(this).text());
        localStorage.setItem('room', rooms_map.get($(this).text()));
        window.location.href = 'chatRoom.html';
    });

    // Display the call queue
    function displayCallQueue(callQueue) {
        const callQueueList = $('#call-queue-list');
        callQueueList.empty();
        rooms_map.clear()
        if (callQueue.length === 0) {
            callQueueList.append('<li>No calls in the queue</li>');
        } else {
            callQueue.forEach(function (call) {
                rooms_map.set(call.customer_username,call.customer_pk)
                callQueueList.append('<li class="list-group-item">' + call.customer_username + '</li>');
            });
        }
    }
});