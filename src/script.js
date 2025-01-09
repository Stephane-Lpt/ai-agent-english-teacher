const chatContainer = document.getElementById('chat-container');

// Function to push a new message to the chat
function pushMessage(sender, message) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);

    const bubble = document.createElement('div');
    bubble.classList.add('bubble');
    bubble.textContent = message;

    messageDiv.appendChild(bubble);
    chatContainer.appendChild(messageDiv);

    // Scroll to the bottom of the chat container
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Example usage (to be replaced by actual conversation logic)
pushMessage('user', 'Hello, AI!');
pushMessage('ai', 'Hello! How can I assist you today?');

// Placeholder for the record button functionality
const recordButton = document.getElementById('record-button');
recordButton.addEventListener('click', () => {
    console.log('Record button clicked. Implement the recording logic.');
});