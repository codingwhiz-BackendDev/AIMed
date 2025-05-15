// Add this to your dashboard.js or create a new script
document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    const toggleSidebar = document.getElementById('toggleSidebar');
    const mobileToggle = document.getElementById('mobileToggle');

    // Function to toggle sidebar
    function toggleSidebarVisibility() {
        sidebar.classList.toggle('active');
        mainContent.classList.toggle('sidebar-open');
    }

    // Event listeners for both toggle buttons
    if (toggleSidebar) {
        toggleSidebar.addEventListener('click', toggleSidebarVisibility);
    }

    if (mobileToggle) {
        mobileToggle.addEventListener('click', toggleSidebarVisibility);
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function (event) {
        const isMobile = window.innerWidth <= 768;
        const clickedOutsideSidebar = !event.target.closest('.sidebar') &&
            !event.target.closest('#mobileToggle') &&
            !event.target.closest('#toggleSidebar');

        if (isMobile && sidebar.classList.contains('active') && clickedOutsideSidebar) {
            sidebar.classList.remove('active');
            mainContent.classList.remove('sidebar-open');
        }
    });
});



document.addEventListener('DOMContentLoaded', function () {
    // Chat search functionality
    const searchInput = document.getElementById('chat-search');
    const chatEntries = document.querySelectorAll('.chat-entry');

    searchInput.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase();

        chatEntries.forEach(entry => {
            const title = entry.querySelector('.chat-entry-title').textContent.toLowerCase();
            const preview = entry.querySelector('.chat-entry-preview').textContent.toLowerCase();

            if (title.includes(searchTerm) || preview.includes(searchTerm)) {
                entry.style.display = 'flex';
            } else {
                entry.style.display = 'none';
            }
        });
    });

    // Filter functionality
    const dateFilter = document.getElementById('date-filter');
    const topicFilter = document.getElementById('topic-filter');

    function applyFilters() {
        const dateValue = dateFilter.value;
        const topicValue = topicFilter.value;

        // This is just a simple simulation - in a real app you'd have actual data attributes
        chatEntries.forEach(entry => {
            let showByDate = true;
            let showByTopic = true;

            // Simple date filter simulation
            const time = entry.querySelector('.chat-entry-time').textContent.toLowerCase();
            if (dateValue === 'today' && !time.includes('today')) {
                showByDate = false;
            } else if (dateValue === 'week' && (!time.includes('today') && !time.includes('yesterday') && !time.includes('apr 7') && !time.includes('apr 5'))) {
                showByDate = false;
            }

            // Simple topic filter simulation
            const title = entry.querySelector('.chat-entry-title').textContent.toLowerCase();
            if (topicValue !== 'all') {
                if (topicValue === 'symptoms' && !title.includes('symptom') && !title.includes('cardiac') && !title.includes('fever')) {
                    showByTopic = false;
                } else if (topicValue === 'lifestyle' && !title.includes('exercise') && !title.includes('nutrition')) {
                    showByTopic = false;
                } else if (topicValue === 'medication' && !title.includes('medication')) {
                    showByTopic = false;
                } else if (topicValue === 'conditions' && !title.includes('diabetes')) {
                    showByTopic = false;
                }
            }

            entry.style.display = (showByDate && showByTopic) ? 'flex' : 'none';
        });
    }

    dateFilter.addEventListener('change', applyFilters);
    topicFilter.addEventListener('change', applyFilters);

    // Continue chat button
    const continueButtons = document.querySelectorAll('.continue-chat-btn');
    continueButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.stopPropagation();
            const chatTitle = this.closest('.chat-entry').querySelector('.chat-entry-title').textContent;
            // In a real application, you would redirect to the chat with the specific chat ID
            window.location.href = "{% url 'chat' %}?continue=" + encodeURIComponent(chatTitle);
        });
    });

    // Make entire chat entry clickable
    chatEntries.forEach(entry => {
        entry.addEventListener('click', function () {
            const chatTitle = this.querySelector('.chat-entry-title').textContent;
            //window.location.href = "{% url 'chat' %}?continue=" + encodeURIComponent(chatTitle);
        });
    });

    // Pagination functionality (simplified for demo)
    const paginationButtons = document.querySelectorAll('.pagination-btn');
    paginationButtons.forEach(button => {
        if (!button.classList.contains('active')) {
            button.addEventListener('click', function () {
                document.querySelector('.pagination-btn.active').classList.remove('active');
                this.classList.add('active');
                // In a real app, this would load the appropriate page of history items
            });
        }
    });
});