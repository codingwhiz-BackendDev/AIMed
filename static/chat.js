/**
 * AI Medical Chat Interface
 * Handles message rendering, animations, and API interactions with Gemini
 */

document.addEventListener('DOMContentLoaded', function () {
    // DOM elements
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const chatMessagesContainer = document.getElementById('chat-messages-chat');
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');
    const recentChatsContainer = document.getElementById('recent-chats');

    // Get CSRF token for Django
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // Handle sending messages
    function handleSendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage('user', message);

        // Show loading indicator
        const loadingId = showLoadingIndicator();

        // Send message to backend
        fetch('/diagnose/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ symptoms: message })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                // Remove loading indicator
                removeLoadingIndicator(loadingId);

                if (data.answer) {
                    // Add AI response to chat
                    addMessage('ai', formatMessage(data.answer));
                } else if (data.error) {
                    addMessage('ai', `⚠️ Error: ${data.error}`);
                }
            })
            .catch(error => {
                // Remove loading indicator
                removeLoadingIndicator(loadingId);

                // Show error message
                addMessage('ai', '⚠️ Sorry, there was an error processing your request. Please try again.');
                console.error('Error:', error);
            });

        // Clear input field
        userInput.value = '';
    }

    function loadChatHistory() {
        fetch('/get-chat-history/')
            .then(response => response.json())
            .then(data => {
                if (data.chat_history && data.chat_history.length > 0) {
                    chatMessagesContainer.innerHTML = ''; // Clear any default welcome message

                    data.chat_history.forEach(chat => {
                        // Apply formatting to AI messages, leave user messages as is
                        const content = chat.role === 'ai' ? formatMessage(chat.message) : chat.message;
                        addMessage(chat.role, content);
                    });

                    // Scroll to the bottom after loading messages
                    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
                }
            })
            .catch(error => {
                console.error('Error loading chat history:', error);
            });
    }

    // Format message with markdown-like syntax
    function formatMessage(text) {
        if (!text) return '';

        // Convert line breaks to <br>
        let formatted = text.replace(/\n/g, '<br>');

        // Bold text between double asterisks
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Italic text between single asterisks
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Process bullet points (lines starting with - or •)
        let lines = formatted.split('<br>');
        let inList = false;

        for (let i = 0; i < lines.length; i++) {
            if (lines[i].trim().match(/^[-•] /)) {
                // If this is the first bullet point, start a list
                if (!inList) {
                    lines[i] = '<ul><li>' + lines[i].trim().substring(2) + '</li>';
                    inList = true;
                } else {
                    lines[i] = '<li>' + lines[i].trim().substring(2) + '</li>';
                }

                // If the next line is not a bullet point or it's the last line, close the list
                if (i === lines.length - 1 || !lines[i + 1].trim().match(/^[-•] /)) {
                    lines[i] = lines[i] + '</ul>';
                    inList = false;
                }
            } else if (inList) {
                // If we're in a list but this line is not a bullet point, close the list
                lines[i - 1] = lines[i - 1] + '</ul>';
                inList = false;
            }
        }

        formatted = lines.join('<br>');

        // Fix any potentially remaining unclosed lists
        if (inList) {
            formatted = formatted + '</ul>';
        }

        return formatted;
    }

    // Add message to chat UI
    function addMessage(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = sender === 'user' ? 'user-message' : 'ai-message';

        const avatar = document.createElement('div');
        avatar.className = sender === 'user' ? 'user-avatar' : 'ai-avatar';

        const icon = document.createElement('i');
        icon.className = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
        avatar.appendChild(icon);

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = content;

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);

        chatMessagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    }

    // Show loading indicator
    function showLoadingIndicator() {
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'ai-message';
        loadingDiv.innerHTML = `
      <div class="ai-avatar"><i class="fas fa-robot"></i></div>
      <div class="message-content">
        <div id="loading-spinner">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span>AI is analyzing your symptoms...</span>
        </div>
      </div>
    `;

        chatMessagesContainer.appendChild(loadingDiv);
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;

        return loadingId;
    }

    // Remove loading indicator
    function removeLoadingIndicator(loadingId) {
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            loadingElement.remove();
        }
    }

    // Event listeners
    if (sendButton) {
        sendButton.addEventListener('click', handleSendMessage);
    }

    if (userInput) {
        userInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        });
    }

    // Suggestion button clicks
    suggestionButtons.forEach(button => {
        button.addEventListener('click', function () {
            if (userInput) {
                userInput.value = this.textContent;
                handleSendMessage();
            }
        });
    });

    // Initial setup
    loadChatHistory();
    
});


//For voice note and image upload


let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let selectedImages = [];

// DOM Elements
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const attachmentButton = document.getElementById('attachment-button');
const imageUpload = document.getElementById('image-upload');
const imagePreview = document.getElementById('image-preview');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');
    setupEventListeners();
    checkMediaRecorderSupport();
});

function setupEventListeners() {
    console.log('Setting up event listeners');
    
    // Send button click handler
    sendButton.addEventListener('click', (e) => {
        console.log('Send button clicked');
        handleSendButtonClick();
    });
    
    // Attachment button click handler
    attachmentButton.addEventListener('click', (e) => {
        console.log('Attachment button clicked');
        e.preventDefault();
        imageUpload.click();
    });
    
    // Image upload handler
    imageUpload.addEventListener('change', (e) => {
        console.log('Image upload changed:', e.target.files);
        handleImageUpload(e);
    });
    
    // Input change handler for icon switching
    userInput.addEventListener('input', (e) => {
        console.log('Input changed:', e.target.value);
        handleInputChange();
    });
}

function handleInputChange() {
    console.log('Handling input change');
    const icon = sendButton.querySelector('i');
    const currentText = userInput.value.trim();
    console.log('Current text:', currentText);
    
    if (currentText !== '') {
        console.log('Changing to send icon');
        icon.className = 'fas fa-paper-plane';
        sendButton.title = 'Send message';
    } else {
        console.log('Changing to microphone icon');
        icon.className = 'fas fa-microphone';
        sendButton.title = 'Record voice note';
    }
}

async function handleSendButtonClick() {
    console.log('Handling send button click');
    const currentText = userInput.value.trim();
    
    if (currentText !== '') {
        console.log('Sending text message');
        await sendMessage(currentText);
    } else if (!isRecording) {
        console.log('Starting recording');
        await startRecording();
    } else {
        console.log('Stopping recording');
        stopRecording();
    }
}

async function startRecording() {
    console.log('Starting recording process');
    try {
        console.log('Requesting microphone access');
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('Microphone access granted');
        
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            console.log('Data available from recorder');
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            console.log('Recording stopped, processing audio');
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await sendVoiceNote(audioBlob);
        };
        
        mediaRecorder.start();
        console.log('MediaRecorder started');
        isRecording = true;
        sendButton.classList.add('recording');
        sendButton.querySelector('i').className = 'fas fa-stop';
    } catch (error) {
        console.error('Error accessing microphone:', error);
        alert('Unable to access microphone. Please check your permissions.');
    }
}

function stopRecording() {
    console.log('Stopping recording');
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        sendButton.classList.remove('recording');
        sendButton.querySelector('i').className = 'fas fa-microphone';
        
        // Stop all audio tracks
        mediaRecorder.stream.getTracks().forEach(track => {
            console.log('Stopping audio track');
            track.stop();
        });
    }
}

function handleImageUpload(event) {
    console.log('Handling image upload');
    const files = event.target.files;
    console.log('Files selected:', files);
    
    for (let file of files) {
        console.log('Processing file:', file.name, file.type);
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                console.log('File read complete');
                addImagePreview(e.target.result, file);
            };
            reader.readAsDataURL(file);
        } else {
            console.log('Invalid file type:', file.type);
        }
    }
    // Reset the input to allow selecting the same file again
    event.target.value = '';
}

function addImagePreview(src, file) {
    console.log('Adding image preview');
    const previewItem = document.createElement('div');
    previewItem.className = 'image-preview-item';
    
    const img = document.createElement('img');
    img.src = src;
    
    const removeButton = document.createElement('button');
    removeButton.className = 'remove-image';
    removeButton.innerHTML = '×';
    removeButton.onclick = () => {
        console.log('Removing image preview');
        previewItem.remove();
        selectedImages = selectedImages.filter(f => f !== file);
    };
    
    previewItem.appendChild(img);
    previewItem.appendChild(removeButton);
    imagePreview.appendChild(previewItem);
    selectedImages.push(file);
    console.log('Image preview added, total images:', selectedImages.length);
}

async function sendMessage(text) {
    try {
        console.log('Sending message:', text);
        
        // Create the request data in the format your view expects
        const requestData = {
            symptoms: text
        };

        // Show loading state
        const sendIcon = sendButton.querySelector('i');
        sendIcon.className = 'fas fa-spinner fa-spin';
        sendButton.disabled = true;
        
        // Send to backend
        const response = await fetch('/diagnose/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(requestData)  // Make sure to stringify the data
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Network response was not ok');
        }
        
        const data = await response.json();
        console.log('Response received:', data);
        
        // Display messages
        displayMessage(text, 'user', selectedImages);
        displayMessage(data.answer, 'ai');
        
        // Clear input and previews
        userInput.value = '';
        imagePreview.innerHTML = '';
        selectedImages = [];
        
        // Reset button icon
        handleInputChange();
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error sending message. Please try again.');
    } finally {
        // Reset button state
        sendButton.disabled = false;
    }
}

async function sendVoiceNote(audioBlob) {
    try {
        const formData = new FormData();
        formData.append('voice_note', audioBlob, 'voice_note.wav');
        
        // Show loading state
        const sendIcon = sendButton.querySelector('i');
        sendIcon.className = 'fas fa-spinner fa-spin';
        sendButton.disabled = true;
        
        const response = await fetch('/diagnose/', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        const data = await response.json();
        
        // Display voice note in chat
        displayVoiceNote(audioBlob);
        // Display AI response
        displayMessage(data.answer, 'ai');
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error sending voice note. Please try again.');
    } finally {
        // Reset button state
        const sendIcon = sendButton.querySelector('i');
        sendIcon.className = 'fas fa-microphone';
        sendButton.disabled = false;
    }
}

function displayMessage(text, type, images = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const avatar = document.createElement('div');
    avatar.className = type === 'ai' ? 'ai-avatar' : 'user-avatar';
    avatar.innerHTML = `<i class="fas fa-${type === 'ai' ? 'robot' : 'user'}"></i>`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // Add text if present
    if (text) {
        const textElement = document.createElement('p');
        textElement.textContent = text;
        bubble.appendChild(textElement);
    }
    
    // Add images if present
    if (images.length > 0) {
        const imagesContainer = document.createElement('div');
        imagesContainer.className = 'message-images';
        images.forEach(file => {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.className = 'message-image';
            imagesContainer.appendChild(img);
        });
        bubble.appendChild(imagesContainer);
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    
    document.getElementById('chat-messages-chat').appendChild(messageDiv);
    messageDiv.scrollIntoView({ behavior: 'smooth' });
}

function displayVoiceNote(audioBlob) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    
    const avatar = document.createElement('div');
    avatar.className = 'user-avatar';
    avatar.innerHTML = '<i class="fas fa-user"></i>';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    const voiceNote = document.createElement('div');
    voiceNote.className = 'voice-note';
    voiceNote.innerHTML = `
        <i class="fas fa-play"></i>
        <span class="duration">Voice Note</span>
    `;
    
    voiceNote.onclick = () => {
        const audio = new Audio(URL.createObjectURL(audioBlob));
        audio.play();
    };
    
    bubble.appendChild(voiceNote);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    
    document.getElementById('chat-messages-chat').appendChild(messageDiv);
    messageDiv.scrollIntoView({ behavior: 'smooth' });
}

function checkMediaRecorderSupport() {
    if (!navigator.mediaDevices || !window.MediaRecorder) {
        sendButton.style.display = 'none';
        alert('Voice recording is not supported in your browser.');
    }
}

// Add this function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
} 