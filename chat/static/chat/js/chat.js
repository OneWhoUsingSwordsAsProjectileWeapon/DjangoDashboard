/**
 * Chat functionality using WebSockets
 */

let chatSocket = null;
let userId = null;

/**
 * Initialize WebSocket connection for chat
 */
function initChatSocket(conversationId, currentUserId) {
    userId = currentUserId;
    
    // Close any existing socket
    if (chatSocket && chatSocket.readyState !== WebSocket.CLOSED) {
        chatSocket.close();
    }
    
    // Determine if we're using secure connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/chat/${conversationId}/`;
    
    // Create WebSocket connection
    chatSocket = new WebSocket(wsUrl);
    
    // Connection opened
    chatSocket.onopen = function(e) {
        console.log('WebSocket connection established');
        
        // Update connection status indicator if exists
        const statusIndicator = document.getElementById('connection-status');
        if (statusIndicator) {
            statusIndicator.classList.remove('bg-danger', 'bg-warning');
            statusIndicator.classList.add('bg-success');
            statusIndicator.setAttribute('title', 'Connected');
        }
    };
    
    // Listen for messages
    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        displayMessage(data);
    };
    
    // Connection closed
    chatSocket.onclose = function(e) {
        console.log('WebSocket connection closed');
        
        // Update connection status indicator if exists
        const statusIndicator = document.getElementById('connection-status');
        if (statusIndicator) {
            statusIndicator.classList.remove('bg-success', 'bg-warning');
            statusIndicator.classList.add('bg-danger');
            statusIndicator.setAttribute('title', 'Disconnected');
        }
        
        // Try to reconnect after a few seconds
        setTimeout(function() {
            initChatSocket(conversationId, currentUserId);
        }, 5000);
    };
    
    // Error handler
    chatSocket.onerror = function(e) {
        console.error('WebSocket error:', e);
        
        // Update connection status indicator if exists
        const statusIndicator = document.getElementById('connection-status');
        if (statusIndicator) {
            statusIndicator.classList.remove('bg-success', 'bg-danger');
            statusIndicator.classList.add('bg-warning');
            statusIndicator.setAttribute('title', 'Connection Error');
        }
    };
}

/**
 * Send a message through the WebSocket
 */
function sendMessage(message) {
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'message': message
        }));
    } else {
        console.error('WebSocket is not connected. Message not sent.');
        
        // Show connection error message
        const chatMessages = document.getElementById('chat-messages');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger text-center my-2';
        errorDiv.textContent = 'Connection error. Message not sent. Trying to reconnect...';
        chatMessages.appendChild(errorDiv);
        
        // Scroll to show the error
        scrollToBottom();
    }
}

/**
 * Display a received message in the chat UI
 */
function displayMessage(data) {
    const chatMessages = document.getElementById('chat-messages');
    const isSelf = parseInt(data.sender_id) === parseInt(userId);
    
    // Create message container
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message mb-3';
    messageDiv.dataset.messageId = data.message_id;
    
    // Format timestamp
    const timestamp = new Date(data.timestamp);
    const formattedTime = timestamp.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    
    // Create message content based on sender
    if (isSelf) {
        // Own message (right-aligned)
        messageDiv.innerHTML = `
            <div class="chat-bubble sent">
                <p class="mb-0">${escapeHtml(data.message)}</p>
                
                <div class="message-options position-absolute top-0 end-0 d-none">
                    <div class="dropdown">
                        <button class="btn btn-sm btn-link text-white p-0" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" href="#" onclick="editMessage(${data.message_id})"><i class="fas fa-edit me-2"></i> Edit</a></li>
                            <li><a class="dropdown-item" href="#" onclick="deleteMessage(${data.message_id})"><i class="fas fa-trash me-2"></i> Delete</a></li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="chat-timestamp text-end">
                <span class="small text-muted">${formattedTime}</span>
            </div>
        `;
    } else {
        // Others' message (left-aligned)
        messageDiv.innerHTML = `
            <div class="d-flex">
                <div class="rounded-circle bg-primary d-flex align-items-center justify-content-center me-2 align-self-start text-white" style="width: 30px; height: 30px; font-size: 0.8rem;">
                    ${data.sender_username.charAt(0).toUpperCase()}
                </div>
                
                <div>
                    <div class="chat-bubble received">
                        <p class="mb-0">${escapeHtml(data.message)}</p>
                        
                        <div class="message-options position-absolute top-0 end-0 d-none">
                            <div class="dropdown">
                                <button class="btn btn-sm btn-link text-dark p-0" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                                    <i class="fas fa-ellipsis-v"></i>
                                </button>
                                <ul class="dropdown-menu dropdown-menu-end">
                                    <li><a class="dropdown-item" href="#" onclick="reportMessage(${data.message_id})"><i class="fas fa-flag me-2"></i> Report</a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="chat-timestamp">
                        <span class="small text-muted">${formattedTime}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add message to chat container
    chatMessages.appendChild(messageDiv);
    
    // Scroll to the new message
    scrollToBottom();
    
    // Show message options on hover
    addMessageHoverListeners(messageDiv);
}

/**
 * Scroll the chat container to the bottom
 */
function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Add hover event listeners to a message to show options
 */
function addMessageHoverListeners(messageElement) {
    const options = messageElement.querySelector('.message-options');
    if (options) {
        messageElement.addEventListener('mouseenter', function() {
            options.classList.remove('d-none');
        });
        
        messageElement.addEventListener('mouseleave', function() {
            options.classList.add('d-none');
        });
    }
}

/**
 * Initialize all message hover listeners
 */
function initMessageHoverListeners() {
    const messages = document.querySelectorAll('.chat-message');
    messages.forEach(addMessageHoverListeners);
}

/**
 * Edit a message
 */
function editMessage(messageId) {
    console.log('Edit message:', messageId);
    // In a real app, this would open an edit modal or inline editor
    alert('Message editing is not implemented in this demo');
}

/**
 * Delete a message
 */
function deleteMessage(messageId) {
    if (confirm('Are you sure you want to delete this message?')) {
        console.log('Delete message:', messageId);
        // In a real app, this would send a deletion request to the server
        alert('Message deletion is not implemented in this demo');
    }
}

/**
 * Report a message
 */
function reportMessage(messageId) {
    // This is implemented in the chat_room.html template
    console.log('Report message:', messageId);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Initialize hover listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initMessageHoverListeners();
});
