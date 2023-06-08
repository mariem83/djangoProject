$(document).ready(function () {


    $('#loginForm').submit(function (e) {
        e.preventDefault(); // Prevent form submission

        // Get the form data
        const username = $('#username').val();
        const password = $('#password').val();

        // Create the JSON object
        const data = {
            username: username,
            password: password
        };

        // Send POST request to the server using Fetch API
        fetch('https://smartfarmcallcenter.azurewebsites.net/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
            .then(response => {
                if (response.status === 200) {
                    return response.json().then(data => {
                        // Extract the token value from response
                        const token = data.token_info.access;

                        // Save the token in local storage
                        localStorage.setItem('token', token);
                        const tokenData = parseJwt(token)
                        console.log(tokenData)
                        // Check if the token has the role "callCenter.view_caller" in its permissions list
                        if (tokenData.permissions && tokenData.permissions.includes("callCenter.view_customer")) {
                            // Redirect to the employee page
                            window.location.href = 'employee.html';
                        } else {
                            // Redirect to the caller chat page
                            window.location.href = 'chatRoom.html';
                        }
                    });
                } else {
                    if (response.status === 403) {
                        // Redirect to the chat room page
                        $("#unknownError").remove();
                    } else {
                        $("#wrongLogin").remove();
                    }
                    $('#failureModal').modal('show');
                }
            })
            .catch(e => {
                console.error('An error occurred:', e);
                $("#wrongLogin").remove();
                $('#failureModal').modal('show');
            });
    });
});