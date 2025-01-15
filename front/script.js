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

// Function to push an audio message to the chat
function pushAudioMessage(sender, audioUrl) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);

    const bubble = document.createElement('div');
    bubble.classList.add('bubble');

    const audioElement = document.createElement('audio');
    audioElement.controls = true;
    audioElement.src = audioUrl;

    bubble.appendChild(audioElement);
    messageDiv.appendChild(bubble);
    chatContainer.appendChild(messageDiv);

    // Scroll to the bottom of the chat container
    chatContainer.scrollTop = chatContainer.scrollHeight;
}




const recordButton = document.getElementById('record-button');
let isRecording = false;
let mediaRecorder;
let audioChunks = [];

// Toggle recording logic
recordButton.addEventListener('click', async () => {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
});

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await sendAudioToApi(audioBlob);
        };

        mediaRecorder.start();
        isRecording = true;
        recordButton.textContent = "⏹️ Stop";
    } catch (error) {
        console.error('Error accessing microphone:', error);
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        recordButton.textContent = "🎙️ Record";
    }
}

async function sendAudioToApi(audioBlob, processingMessageId) {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recorded-audio.wav');

    try {
        const response = await fetch('http://127.0.0.1:8000/process-audio/', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Failed to process audio');
        }

        const audioBlob = await response.blob(); // Get audio file blob from API response
        const audioUrl = URL.createObjectURL(audioBlob); // Create a URL for the blob
        
        // Push the audio as a new message
        pushAudioMessage('ai', audioUrl);
    } catch (error) {
        console.error('Error sending audio:', error);
        // Update the "Processing" message with an error
        pushMessage('ai', 'There was an error processing your audio.');
    }
}