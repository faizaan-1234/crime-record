// static/js/script.js

document.addEventListener('DOMContentLoaded', (event) => {
    console.log('DOM fully loaded and parsed');

    // Add confirmation dialog to all delete forms
    const deleteForms = document.querySelectorAll('form.delete-form'); // Select forms with the 'delete-form' class

    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Get the button text or a generic message part
            let recordType = 'record'; // Default
            const button = form.querySelector('button[type="submit"]');
            // You could add data attributes to the form or button to specify type if needed
            // e.g., <form data-type="victim" ...> then use form.dataset.type

            const confirmed = confirm(`Are you sure you want to delete this ${recordType}? This action cannot be undone.`);

            if (!confirmed) {
                e.preventDefault(); // Stop the form submission if user cancels
            }
            // If confirmed, the form submits as normal
        });
    });


});
// --- JavaScript for Login Page (Add this to your existing static/js/script.js) ---

document.addEventListener('DOMContentLoaded', function() {
    // Check if the login form exists on the page
    const loginForm = document.querySelector('.login-form');

    if (loginForm) { // Only run this code if the .login-form element is found
        loginForm.addEventListener('submit', function(event) {
            // Optional: Prevent default submission if you want to handle with JS/Fetch
            // event.preventDefault();

            // Get input values (optional, you can get these on the backend too)
            const usernameInput = loginForm.querySelector('#username');
            const passwordInput = loginForm.querySelector('#password');

            console.log('Login form submitted!');
            console.log('Username:', usernameInput.value);
            console.log('Password:', passwordInput.value);

            // If you used event.preventDefault(), you would now use fetch()
            // or XMLHttpRequest to send this data to your backend login route.
            // Otherwise, the browser handles the POST request.

            // Example if using fetch (uncomment and adapt if needed):
            /*
            fetch(loginForm.action, {
                method: loginForm.method,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded', // or 'application/json' if sending JSON
                },
                body: new URLSearchParams({
                    username: usernameInput.value,
                    password: passwordInput.value
                })
            })
            .then(response => {
                // Handle response (e.g., check response.ok, parse JSON)
                if (!response.ok) {
                    // Handle login failure
                    console.error('Login failed');
                    // Display an error message to the user
                } else {
                    // Handle login success (e.g., redirect)
                    console.log('Login successful');
                    // window.location.href = '/dashboard'; // Redirect to a protected page
                }
                return response.json(); // or .text()
            })
            .then(data => {
                console.log('Server response:', data);
            })
            .catch(error => {
                console.error('Network error or issue:', error);
                // Display a network error message
            });
            */
        });
    }

    // --- Your other existing JavaScript code goes here ---
    // ... (e.g., code for your navigation bar or other parts of your app)
    // Example:
    // const myButton = document.getElementById('some-button');
    // if (myButton) {
    //     myButton.addEventListener('click', function() {
    //         alert('Button clicked!');
    //     });
    // }

});

// --- Any global JavaScript functions outside the DOMContentLoaded listener can go here ---