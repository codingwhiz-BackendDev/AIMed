
document.addEventListener("DOMContentLoaded", () => {

    const themeToggle = document.getElementById("themeToggle");
    if (!themeToggle) {
        console.error("Theme toggle button not found!");
        return;
    }

    const currentTheme = localStorage.getItem("theme");
    console.log("Current theme from localStorage:", currentTheme);

    // Apply the saved theme on page load
    if (currentTheme) {
        document.body.setAttribute("data-theme", currentTheme);
        updateToggleIcon(currentTheme);
    } else {
        // Default to light mode if no theme is saved
        document.body.setAttribute("data-theme", "light");
    }

    themeToggle.addEventListener("click", () => {
        const currentTheme = document.body.getAttribute("data-theme");
        console.log("Current theme:", currentTheme);

        // Toggle between light and dark modes
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        document.body.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
        updateToggleIcon(newTheme);

        console.log("New theme set:", newTheme);
    });

    function updateToggleIcon(theme) {
        const icon = themeToggle.querySelector("i");
        if (!icon) {
            console.error("Icon element not found!");
            return;
        }

        if (theme === "dark") {
            icon.classList.remove("fa-moon");
            icon.classList.add("fa-sun");
        } else {
            icon.classList.remove("fa-sun");
            icon.classList.add("fa-moon");
        }
    }
});