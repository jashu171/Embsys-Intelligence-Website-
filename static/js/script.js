// Global variables
let isWelcomeVisible = true;
let chatHistory = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function () {
    initializeEventListeners();
    setupFileUpload();
});

function initializeEventListeners() {
    // Welcome screen message input event listeners
    const messageInput = document.getElementById('messageInput');
    messageInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    messageInput.addEventListener('input', function () {
        const sendBtn = document.getElementById('sendBtn');
        if (this.value.trim()) {
            sendBtn.style.color = '#6366f1';
        } else {
            sendBtn.style.color = '#d1d5db';
        }
    });

    // Chat message input event listeners
    const chatMessageInput = document.getElementById('chatMessageInput');
    chatMessageInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    chatMessageInput.addEventListener('input', function () {
        const chatSendBtn = document.getElementById('chatSendBtn');
        if (this.value.trim()) {
            chatSendBtn.style.color = '#6366f1';
        } else {
            chatSendBtn.style.color = '#d1d5db';
        }
    });

    // File input change listener
    document.getElementById('fileInput').addEventListener('change', handleFileUpload);
}

function setupFileUpload() {
    const fileInput = document.getElementById('fileInput');

    // Drag and drop functionality
    document.addEventListener('dragover', function (e) {
        e.preventDefault();
    });

    document.addEventListener('drop', function (e) {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileUpload();
        }
    });
}

function startNewChat() {
    // Clear chat messages
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';

    // Show welcome screen and hide chat input
    const welcomeScreen = document.getElementById('welcomeScreen');
    const chatInputContainer = document.getElementById('chatInputContainer');
    welcomeScreen.style.display = 'flex';
    chatInputContainer.style.display = 'none';
    isWelcomeVisible = true;

    // Clear inputs
    document.getElementById('messageInput').value = '';
    document.getElementById('chatMessageInput').value = '';

    // Reset chat history
    chatHistory = [];
}

function hideWelcomeScreen() {
    if (isWelcomeVisible) {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const chatInputContainer = document.getElementById('chatInputContainer');
        welcomeScreen.style.display = 'none';
        chatInputContainer.style.display = 'block';
        isWelcomeVisible = false;
    }
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message) return;

    hideWelcomeScreen();
    addMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    showTypingIndicator();

    // Send request to backend
    sendQueryToBackend(message);
}

function sendChatMessage() {
    const input = document.getElementById('chatMessageInput');
    const message = input.value.trim();

    if (!message) return;

    addMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    showTypingIndicator();

    // Send request to backend
    sendQueryToBackend(message);
}

function sendQueryToBackend(message) {
    fetch('/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: message })
    })
        .then(response => response.json())
        .then(data => {
            hideTypingIndicator();

            if (data.error || data.error_code) {
                const errorMsg = data.message || data.error || 'An error occurred processing your request.';
                addMessage(`Sorry, I encountered an error: ${errorMsg}`, 'assistant');
            } else {
                addMessage(data.answer, 'assistant');

                // Add source information if available
                if (data.sources && data.sources.length > 0) {
                    addSourceInfo(data.sources);
                }
            }

            // Update chat history
            chatHistory.push({
                user: message,
                assistant: data.answer || 'Error occurred',
                timestamp: new Date()
            });
        })
        .catch(error => {
            hideTypingIndicator();
            console.error('Error:', error);
            addMessage('Sorry, I encountered a network error. Please try again.', 'assistant');
        });
}

function sendSuggestion(suggestion) {
    const input = document.getElementById('messageInput');
    input.value = suggestion;
    sendMessage();
}

function addMessage(text, sender) {
    const messagesContainer = document.getElementById('messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = sender === 'user' ? 'U' : 'AI';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = text;

    contentDiv.appendChild(textDiv);
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);

    messagesContainer.appendChild(messageDiv);

    // Smooth scroll to bottom
    setTimeout(() => {
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

function addSourceInfo(sources) {
    const messagesContainer = document.getElementById('messages');
    const lastMessage = messagesContainer.lastElementChild;

    if (lastMessage && lastMessage.classList.contains('assistant')) {
        const contentDiv = lastMessage.querySelector('.message-content');
        const sourceDiv = document.createElement('div');
        sourceDiv.className = 'message-source';
        
        if (Array.isArray(sources)) {
            sourceDiv.textContent = `Sources: ${sources.join(', ')}`;
        } else {
            sourceDiv.textContent = `Source: ${sources.substring(0, 150)}...`;
        }
        
        contentDiv.appendChild(sourceDiv);
    }
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('messages');

    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant typing-indicator';
    typingDiv.id = 'typingIndicator';

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = 'AI';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';

    contentDiv.appendChild(textDiv);
    typingDiv.appendChild(avatarDiv);
    typingDiv.appendChild(contentDiv);

    messagesContainer.appendChild(typingDiv);
    
    // Smooth scroll to bottom
    setTimeout(() => {
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);

    // Add typing animation CSS if not already added
    if (!document.getElementById('typingCSS')) {
        const style = document.createElement('style');
        style.id = 'typingCSS';
        style.textContent = `
            .typing-dots {
                display: flex;
                gap: 4px;
                align-items: center;
            }
            .typing-dots span {
                width: 6px;
                height: 6px;
                background-color: #b4b4b4;
                border-radius: 50%;
                animation: typing 1.4s infinite ease-in-out;
            }
            .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
            .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
            @keyframes typing {
                0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
                40% { transform: scale(1); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function handleFileUpload() {
    const files = document.getElementById('fileInput').files;
    if (files.length === 0) return;

    showUploadModal();

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.error || data.error_code) {
                const errorMsg = data.message || data.error || 'Upload failed';
                showUploadStatus(`<div class="error-message">Error: ${errorMsg}</div>`);
            } else {
                let statusHtml = `
                <div class="success-message">
                    Successfully uploaded and processed ${data.uploaded_files.length} files:
                    <ul style="margin-top: 8px; padding-left: 20px;">
                        ${data.uploaded_files.map(file => `<li>${file}</li>`).join('')}
                    </ul>
                </div>
            `;
                
                // Add email alert information if available
                if (data.email_alert_results && data.email_alert_results.length > 0) {
                    statusHtml += `
                    <div style="margin-top: 12px; padding: 12px; background-color: #e8f5e8; border-radius: 6px;">
                        <strong>Email Alerts:</strong>
                        ${data.email_alert_results.map(result => 
                            `<div>• ${result.filename}: ${result.email_result.sent_count} emails sent</div>`
                        ).join('')}
                    </div>
                `;
                }
                
                showUploadStatus(statusHtml);
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            showUploadStatus('<div class="error-message">Network error occurred during upload</div>');
        });

    // Clear file input
    document.getElementById('fileInput').value = '';
}

function showUploadModal() {
    const modal = document.getElementById('uploadModal');
    const statusDiv = document.getElementById('uploadStatus');

    statusDiv.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Processing documents...</p>
        </div>
    `;

    modal.style.display = 'block';
}

function showUploadStatus(html) {
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.innerHTML = html;
}

function closeModal() {
    const modal = document.getElementById('uploadModal');
    modal.style.display = 'none';
}

function toggleTools() {
    // Placeholder for tools functionality
    console.log('Tools functionality to be implemented');
}

function updateChatHistory() {
    const historyContainer = document.querySelector('.chat-history');

    // Clear existing history except the "New conversation" item
    const existingItems = historyContainer.querySelectorAll('.chat-history-item:not(.active)');
    existingItems.forEach(item => item.remove());

    // Add recent chats (last 10)
    const recentChats = chatHistory.slice(-10).reverse();
    recentChats.forEach((chat, index) => {
        const historyItem = document.createElement('div');
        historyItem.className = 'chat-history-item';
        historyItem.textContent = chat.user.substring(0, 30) + (chat.user.length > 30 ? '...' : '');
        historyItem.onclick = () => loadChatHistory(index);
        historyContainer.appendChild(historyItem);
    });
}

function loadChatHistory(index) {
    // Placeholder for loading specific chat history
    console.log('Loading chat history:', index);
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('uploadModal');
    if (event.target === modal) {
        closeModal();
    }
}

// Additional functions
function toggleConnectStore() {
    console.log('Connect store functionality to be implemented');
}

function exploreUsecases() {
    console.log('Explore usecases functionality to be implemented');
}