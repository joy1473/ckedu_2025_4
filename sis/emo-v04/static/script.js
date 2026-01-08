document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const menuBtn = document.getElementById('menuBtn');
    const closeSidebarBtn = document.getElementById('closeSidebar');

    // Header Actions
    const profileContainer = document.getElementById('profileContainer');
    const profileDropdown = document.getElementById('profileDropdown');
    const settingsContainer = document.getElementById('settingsContainer');
    const settingsDropdown = document.getElementById('settingsDropdown');
    const iconGrid = document.getElementById('iconGrid');
    const userBtns = document.querySelectorAll('.user-btn');
    const profileIcon = document.querySelector('.profile-icon');

    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatContainer = document.getElementById('chatContainer');
    const themeBtns = document.querySelectorAll('.theme-circle');
    const voiceBtn = document.getElementById('voiceBtn');
    const emptyState = document.querySelector('.empty-state');

    // State
    let isRecording = false;
    let isGenerating = false;

    // Sidebar Logic
    const appContainer = document.querySelector('.app-container');
    function toggleSidebar() {
        if (window.innerWidth > 768) {
            // PC: Toggle Collapse Mode
            appContainer.classList.toggle('sidebar-collapsed');
        } else {
            // Mobile: Toggle Off-Canvas Mode
            const isOpen = appContainer.classList.toggle('sidebar-open');
            if (isOpen) {
                sidebarOverlay.style.display = 'block';
            } else {
                sidebarOverlay.style.display = 'none';
            }
        }
    }

    if (menuBtn) {
        menuBtn.addEventListener('click', toggleSidebar);
    }

    // Also allow closing from inside the sidebar (hamburger icon)
    if (closeSidebarBtn) {
        closeSidebarBtn.addEventListener('click', toggleSidebar);
    }

    // Mobile overlay click to close
    sidebarOverlay.addEventListener('click', () => {
        appContainer.classList.remove('sidebar-open');
        sidebarOverlay.style.display = 'none';
    });

    // Dropdown Toggles
    function toggleDropdown(container, dropdown) {
        dropdown.classList.toggle('hidden');
    }

    profileContainer.addEventListener('click', (e) => {
        e.stopPropagation();
        settingsDropdown.classList.add('hidden'); // Close others
        toggleDropdown(profileContainer, profileDropdown);
    });

    settingsContainer.addEventListener('click', (e) => {
        e.stopPropagation();
        profileDropdown.classList.add('hidden'); // Close others
        toggleDropdown(settingsContainer, settingsDropdown);
    });

    document.addEventListener('click', (e) => {
        if (!profileContainer.contains(e.target)) profileDropdown.classList.add('hidden');
        if (!settingsContainer.contains(e.target)) settingsDropdown.classList.add('hidden');
    });

    // Load saved settings
    const savedIcon = localStorage.getItem('lazy_egg_icon');
    const savedTheme = localStorage.getItem('lazy_egg_theme');

    if (savedIcon) profileIcon.textContent = savedIcon;
    if (savedTheme) document.body.setAttribute('data-theme', savedTheme);

    // Populate Random Icons
    const emojis = ['🐣', '🥚', '🍳', '🐤', '🐥', '🧊', '🎈', '⭐', '🌙', '☁️', '🎨', '🎲'];
    function populateIcons() {
        iconGrid.innerHTML = '';
        // Select 10 random unique emojis
        const shuffled = emojis.sort(() => 0.5 - Math.random());
        const selected = shuffled.slice(0, 10);

        selected.forEach(icon => {
            const span = document.createElement('span');
            span.className = 'icon-option';
            span.textContent = icon;
            span.addEventListener('click', () => {
                const newIcon = icon;
                profileIcon.textContent = newIcon;
                localStorage.setItem('lazy_egg_icon', newIcon);

                // Update existing user messages to match new identity
                const userAvatars = document.querySelectorAll('.message.user .avatar');
                userAvatars.forEach(av => av.textContent = newIcon);
            });
            iconGrid.appendChild(span);
        });
    }
    populateIcons();

    // User Selection
    userBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const user = btn.dataset.user;
            addMessage(`[SYSTEM] Switched to ${user}`, 'assistant');
            // Here you would add logic to switch context/persona
        });
    });

    // Theme Switching
    themeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const theme = btn.dataset.theme;
            document.body.setAttribute('data-theme', theme);
            localStorage.setItem('lazy_egg_theme', theme);
        });
    });

    // Chat Logic
    function addMessage(text, sender) {
        if (!text.trim()) return;

        // Remove empty state if it's the first message
        if (emptyState && emptyState.style.display !== 'none') {
            emptyState.style.display = 'none';
        }

        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;

        // Get current user icon from header if sender is user
        const userIcon = profileIcon.textContent;
        const assistantIcon = '🍳'; // Fixed icon for Lazy Egg

        const avatarIcon = sender === 'user' ? userIcon : assistantIcon;

        msgDiv.innerHTML = `
            <div class="avatar">${avatarIcon}</div>
            <div class="message-content">${text}</div>
        `;

        chatContainer.appendChild(msgDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    async function handleSendMessage() {
        if (isGenerating) return;

        const text = chatInput.value;
        if (!text.trim()) return;

        isGenerating = true;

        addMessage(text, 'user');
        chatInput.value = '';
        chatInput.style.height = 'auto'; // Reset height

        // 1. Change Icon to Square (Thinking)
        const originalIcon = sendBtn.innerHTML;
        sendBtn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="7" y="7" width="10" height="10" rx="1"></rect></svg>`;

        // 2. Add Thinking Bubble
        const thinkingId = 'thinking-' + Date.now();
        const thinkingHtml = `<div class="thinking-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;

        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = `message assistant`;
        thinkingDiv.id = thinkingId;
        const assistantIcon = '🍳';
        thinkingDiv.innerHTML = `
            <div class="avatar">${assistantIcon}</div>
            <div class="message-content">${thinkingHtml}</div>
        `;
        chatContainer.appendChild(thinkingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await response.json();

            // Remove Thinking Bubble
            const tBubble = document.getElementById(thinkingId);
            if (tBubble) tBubble.remove();

            addMessage(data.reply, 'assistant');
        } catch (error) {
            console.error('Error:', error);

            // Remove Thinking Bubble
            const tBubble = document.getElementById(thinkingId);
            if (tBubble) tBubble.remove();

            // Fallback
            setTimeout(() => {
                addMessage("게으른 달걀이 서버 연결을 확인하라고 하네요... (백엔드 연결 필요)", 'assistant');
            }, 500);
        } finally {
            // 3. Revert Icon
            isGenerating = false;
            sendBtn.innerHTML = originalIcon; // Use stored original or hardcode the paper plane if nicer.
            // Hardcode to ensure clean state:
            sendBtn.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>`;
        }
    }

    sendBtn.addEventListener('click', handleSendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Auto-resize textarea
    chatInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') this.style.height = 'auto';
    });

    // Voice Input (Web Speech API)
    if ('webkitSpeechRecognition' in window) {
        const recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = 'ko-KR';

        recognition.onstart = () => {
            isRecording = true;
            voiceBtn.classList.add('listening');
        };

        recognition.onend = () => {
            isRecording = false;
            voiceBtn.classList.remove('listening');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[event.results.length - 1][0].transcript;
            chatInput.value += transcript;
            // Optionally auto-submit
            // handleSendMessage(); 
        };

        voiceBtn.addEventListener('click', () => {
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });
    } else {
        voiceBtn.style.display = 'none'; // Hide if not supported
    }

    // Default Greeting Check (if needed)

    // Service Worker Registration
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/service-worker.js')
            .then(reg => console.log('Service Worker Registered!', reg))
            .catch(err => console.log('Service Worker Registration failed', err));
    }
});
