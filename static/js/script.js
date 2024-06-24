document.addEventListener('DOMContentLoaded', (event) => {
    const sendButton = document.getElementById('sendButton');
    const userInput = document.getElementById('userInput');
    const chat = document.getElementById('chat');
    const fileInput = document.getElementById('fileInput');

    const createMessageElement = (message, className) => {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${className}`;
        messageElement.innerHTML = message;
        return messageElement;
    };

    const sendMessage = () => {
        const userText = userInput.value;
        if (userText.trim() !== '') {
            chat.appendChild(createMessageElement(userText, 'user'));
            userInput.value = ''; // Clear input after sending

            const typingIndicator = createMessageElement('Typing...', 'bot');
            chat.appendChild(typingIndicator);

            fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userText }),
            })
            .then(response => response.json())
            .then(data => {
                chat.removeChild(typingIndicator);
                chat.appendChild(createMessageElement(data.message, 'bot'));
                hljs.highlightAll();
                chat.scrollTop = chat.scrollHeight; // Scroll to the bottom
            })
            .catch((error) => {
                chat.removeChild(typingIndicator);
                console.error('Error:', error);
            });
        }
    };

    const uploadFile = () => {
        const file = fileInput.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('file', file);

            const fileMessage = createMessageElement(`Uploading ${file.name}...`, 'file');
            chat.appendChild(fileMessage);

            fetch('/upload_file', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                fileMessage.innerHTML = data.message;
                hljs.highlightAll();
                chat.scrollTop = chat.scrollHeight; // Scroll to the bottom
            })
            .catch((error) => {
                fileMessage.innerHTML = `Error uploading ${file.name}`;
                console.error('Error:', error);
            });
        }
    };

    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
            e.preventDefault(); // Prevent the default action to stop form submission
        }
    });

    fileInput.addEventListener('change', uploadFile);
});
