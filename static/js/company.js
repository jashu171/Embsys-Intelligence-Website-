// Company website JavaScript functionality
document.addEventListener('DOMContentLoaded', function () {
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Handle background image loading
    const background = document.querySelector('.perfect-background');
    if (background) {
        background.style.opacity = '1';
    }

    // Billing toggle functionality
    const toggle = document.getElementById('billing-toggle');
    const monthlyOption = document.querySelector('.billing-option:first-child');
    const yearlyOption = document.querySelector('.billing-option:last-child');
    const priceAmounts = document.querySelectorAll('.price-amount');
    const pricePeriods = document.querySelectorAll('.price-period');

    // Monthly prices
    const monthlyPrices = ['4', '0', '99'];
    // Yearly prices (with discount)
    const yearlyPrices = ['40', '0', '990'];

    if (toggle) {
        toggle.addEventListener('change', function () {
            if (this.checked) {
                // Yearly billing
                monthlyOption.classList.remove('active');
                yearlyOption.classList.add('active');
                priceAmounts.forEach((amount, index) => {
                    amount.textContent = yearlyPrices[index];
                });
                pricePeriods.forEach(period => {
                    period.textContent = '/year';
                });
            } else {
                // Monthly billing
                yearlyOption.classList.remove('active');
                monthlyOption.classList.add('active');
                priceAmounts.forEach((amount, index) => {
                    amount.textContent = monthlyPrices[index];
                });
                pricePeriods.forEach(period => {
                    period.textContent = '/month';
                });
            }
        });
    }

    // Add click handlers for CTA buttons
    document.querySelectorAll('.btn-primary, .btn-secondary').forEach(button => {
        button.addEventListener('click', function(e) {
            // Add a subtle animation effect
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    });
});