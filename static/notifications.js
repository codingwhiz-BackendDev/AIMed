// Notification system
class NotificationSystem {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'notification-container';
        document.body.appendChild(this.container);
    }

    show(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        // Create icon based on type
        const icon = document.createElement('i');
        icon.className = this.getIconClass(type);
        
        // Create message element
        const messageElement = document.createElement('span');
        messageElement.textContent = message;
        
        // Create close button
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '&times;';
        closeButton.className = 'close-btn';
        closeButton.onclick = () => this.removeNotification(notification);
        
        // Assemble notification
        notification.appendChild(icon);
        notification.appendChild(messageElement);
        notification.appendChild(closeButton);
        
        // Add to container
        this.container.appendChild(notification);
        
        // Trigger animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Auto remove after 4 seconds
        setTimeout(() => {
            this.removeNotification(notification);
        }, 4000);
    }

    removeNotification(notification) {
        notification.classList.remove('show');
        notification.classList.add('hide');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }

    getIconClass(type) {
        switch(type) {
            case 'success':
                return 'fas fa-check-circle';
            case 'error':
                return 'fas fa-exclamation-circle';
            case 'warning':
                return 'fas fa-exclamation-triangle';
            default:
                return 'fas fa-info-circle';
        }
    }
}

// Add styles for notifications
const style = document.createElement('style');
style.textContent = `
    .notification-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
    }

    .notification {
        background: white;
        border-radius: 0.5rem;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        transform: translateX(120%);
        transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        max-width: 350px;
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    .notification.show {
        transform: translateX(0);
    }

    .notification.hide {
        transform: translateX(120%);
    }

    .notification i {
        font-size: 1.1rem;
    }

    .notification.success {
        border-left: 4px solid #4CAF50;
    }

    .notification.success i {
        color: #4CAF50;
    }

    .notification.error {
        border-left: 4px solid #f44336;
    }

    .notification.error i {
        color: #f44336;
    }

    .notification.warning {
        border-left: 4px solid #ff9800;
    }

    .notification.warning i {
        color: #ff9800;
    }

    .notification.info {
        border-left: 4px solid var(--primary-color);
        background: linear-gradient(to right, rgba(37, 99, 235, 0.05), white);
    }

    .notification.info i {
        color: var(--primary-color);
    }

    .close-btn {
        background: none;
        border: none;
        color: var(--light-text);
        font-size: 1.25rem;
        cursor: pointer;
        padding: 0;
        margin-left: auto;
        transition: all 0.2s ease;
    }

    .close-btn:hover {
        color: var(--text-color);
        transform: scale(1.1);
    }

    .notification span {
        color: var(--text-color);
        font-size: 0.95rem;
        line-height: 1.4;
    }
`;
document.head.appendChild(style);

// Create global notification system instance
window.notificationSystem = new NotificationSystem();

document.addEventListener('DOMContentLoaded', function() {
    // Get all messages
    const messages = document.querySelectorAll('.message');
    
    // Function to show message
    function showMessage(message) {
        message.classList.add('show');
        
        // Auto hide after 4 seconds
        setTimeout(() => {
            message.classList.remove('show');
            message.classList.add('hide');
            
            // Remove from DOM after animation
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 4000);
    }
    
    // Show each message
    messages.forEach(message => {
        // Add close button
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '&times;';
        closeButton.className = 'close-btn';
        closeButton.onclick = () => {
            message.classList.remove('show');
            message.classList.add('hide');
            setTimeout(() => message.remove(), 300);
        };
        message.appendChild(closeButton);
        
        // Show message
        setTimeout(() => showMessage(message), 100);
    });
}); 