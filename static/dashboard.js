
document.addEventListener("DOMContentLoaded", function () {

  // Update current date
  const currentDate = new Date();
  document.getElementById("current-date").textContent =
    currentDate.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });

  // Initialize chart
  const ctx = document.getElementById("patientsChart").getContext("2d");
  new Chart(ctx, {
    type: "line",
    data: {
      labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      datasets: [
        {
          label: "Doctors",
          data: [12, 19, 15, 17, 14, 10, 8],
          borderColor: "#3b82f6",
          tension: 0.4,
        },
        {
          label: "Patients",
          data: [25, 30, 28, 32, 29, 20, 15],
          borderColor: "#10b981",
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });

  // Update stats with random data (for demo)
  setInterval(() => {
    document.getElementById("active-doctors").textContent =
      Math.floor(Math.random() * 20) + 10;
    document.getElementById("active-patients").textContent =
      Math.floor(Math.random() * 50) + 30;
    document.getElementById("ai-usage").textContent =
      Math.floor(Math.random() * 30) + 70 + "%";
  }, 5000);
});

document.addEventListener('DOMContentLoaded', function () {
  // Sidebar Toggle
  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('toggleSidebar');
  const mobileToggle = document.getElementById('mobileToggle');
  const mainContent = document.querySelector('.main-content');

  // Desktop sidebar toggle
  toggleBtn.addEventListener('click', function () {
    if (window.innerWidth > 768) {
      sidebar.classList.toggle('collapsed');
    }
  });

  // Mobile sidebar toggle
  mobileToggle.addEventListener('click', function () {
    sidebar.classList.toggle('show');
  });

  // Close sidebar when clicking outside on mobile
  document.addEventListener('click', function (e) {
    if (window.innerWidth <= 768 &&
      !sidebar.contains(e.target) &&
      !mobileToggle.contains(e.target)) {
      sidebar.classList.remove('show');
    }
  });

  // Update current date
  const currentDate = new Date();
  const dateElement = document.getElementById('currentDate');
  if (dateElement) {
    dateElement.textContent = currentDate.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  // Add hover effect to dashboard cards
  const cards = document.querySelectorAll('.dashboard-card');
  cards.forEach(card => {
    card.addEventListener('mouseenter', function () {
      this.style.transform = 'translateY(-5px)';
      this.style.boxShadow = '0 6px 12px rgba(0, 0, 0, 0.1)';
    });

    card.addEventListener('mouseleave', function () {
      this.style.transform = 'translateY(0)';
      this.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.05)';
    });
  });

  // Add active state to navigation links
  const navLinks = document.querySelectorAll('.sidebar-nav a');
  navLinks.forEach(link => {
    link.addEventListener('click', function () {
      navLinks.forEach(l => l.classList.remove('active'));
      this.classList.add('active');
      // Close sidebar on mobile after clicking a link
      if (window.innerWidth <= 768) {
        sidebar.classList.remove('show');
      }
    });
  });

  // Add smooth scroll to top button
  const scrollTopBtn = document.createElement('button');
  scrollTopBtn.className = 'scroll-top-btn';
  scrollTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
  document.body.appendChild(scrollTopBtn);

  window.addEventListener('scroll', function () {
    if (window.pageYOffset > 300) {
      scrollTopBtn.classList.add('show');
    } else {
      scrollTopBtn.classList.remove('show');
    }
  });

  scrollTopBtn.addEventListener('click', function () {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });

  // Add styles for new elements
  const style = document.createElement('style');
  style.textContent = `
        .scroll-top-btn {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--primary-color);
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
            z-index: 1000;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .scroll-top-btn.show {
            opacity: 1;
            transform: translateY(0);
        }

        .scroll-top-btn:hover {
            background: var(--secondary-color);
            transform: translateY(-3px);
        }
    `;
  document.head.appendChild(style);
});

