document.addEventListener('DOMContentLoaded', function() {
    // Text animation for welcome message
    const welcomeText = document.querySelector('h2');
    const subtext = document.querySelector('.subtext');
    let isInverted = false;

    // Function to invert text colors with enhanced glow effect
    function invertTextColors() {
        if (!isInverted) {
            welcomeText.style.color = '#00D4FF';
            welcomeText.style.textShadow = '0 0 15px #00D4FF, 0 0 30px #00D4FF, 0 0 45px #00D4FF';
            welcomeText.style.transition = 'all 1s ease-in-out';
            subtext.style.color = '#00D4FF';
            subtext.style.textShadow = '0 0 10px #00D4FF, 0 0 20px #00D4FF';
            subtext.style.transition = 'all 1s ease-in-out';
        } else {
            welcomeText.style.color = '#004085';
            welcomeText.style.textShadow = 'none';
            welcomeText.style.transition = 'all 1s ease-in-out';
            subtext.style.color = '#666';
            subtext.style.textShadow = 'none';
            subtext.style.transition = 'all 1s ease-in-out';
        }
        isInverted = !isInverted;
    }

    // Invert colors every 2 seconds for more frequent changes
    setInterval(invertTextColors, 2000);

    // Add floating animation to the logo
    const logo = document.querySelector('.logo img');
    logo.style.animation = 'float 2s ease-in-out infinite';

    // Add hover effect to input fields
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'scale(1.02)';
            this.parentElement.style.transition = 'transform 0.3s ease';
        });

        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'scale(1)';
        });
    });

    // Add typing effect to input placeholders
    const placeholders = {
        username: 'Enter your Username',
        password: 'Enter your Password',
        email: 'Enter your Email'
    };

    function typeWriter(element, text, i = 0) {
        if (i < text.length) {
            element.placeholder = text.substring(0, i + 1);
            setTimeout(() => typeWriter(element, text, i + 1), 100);
        }
    }

    // Start typing effect for each input
    inputs.forEach(input => {
        const placeholderText = placeholders[input.id] || input.placeholder;
        input.placeholder = '';
        setTimeout(() => typeWriter(input, placeholderText), 500);
    });

    // Add ripple effect to the login button
    const loginButton = document.querySelector('button[type="submit"]');
    loginButton.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        ripple.classList.add('ripple');
        
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = `${size}px`;
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;
        
        this.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    });

    // Add keyframe animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }

        .ripple {
            position: absolute;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 600ms ease-in-out;
        }

        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }

        button {
            position: relative;
            overflow: hidden;
        }

        h2, .subtext {
            transition: all 1s ease-in-out;
        }
    `;
    document.head.appendChild(style);
});
