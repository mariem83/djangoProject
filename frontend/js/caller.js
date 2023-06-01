$(document).ready(function () {
    var token = localStorage.getItem('token'); // Retrieve token from local storage
    var decodedToken = parseJwt(token); // Decode the JWT token
    // WebSocket connection
    var socket = new WebSocket('ws://localhost:8000/ws/call-center/room/', ['Bearer', token]);

    socket.onopen = function () {
        console.log('WebSocket connection established.');
    };

    socket.onmessage = function (event) {
        var data = JSON.parse(event.data);
        var messageType = data.type;

        if (messageType === 'employee_list') {
            displayEmployeeList(data.employee_list);
        }
    };

    // Handle start call form submission
    $('#start-call-form').submit(function (event) {
        event.preventDefault();
        var employeeId = $('#employee-id').val();
        var callerName = $('#caller-name').val();
        socket.send(JSON.stringify({
            'type': 'start_call',
            'employee_id': employeeId,
            'caller_name': callerName,
        }));
        $('#employee-id').val('');
        $('#caller-name').val('');
    });

    // Display the list of available employees
    function displayEmployeeList(employeeList) {
        var employeeListElement = $('#employee-list');
        employeeListElement.empty();
        if (employeeList.length === 0) {
            employeeListElement.append('<li>No available employees</li>');
        } else {
            employeeList.forEach(function (employee) {
                employeeListElement.append('<li>' + employee.name + ' (' + employee.employee_id + ')</li>');
            });
        }
    }
});