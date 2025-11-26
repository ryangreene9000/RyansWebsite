/**
 * Ryan Greene Portfolio - Housing Price Estimator
 * Handles the ML API integration for the real estate price estimator
 */

(function() {
    'use strict';

    // ============================================
    // Configuration
    // ============================================
    
    // UPDATE THIS URL with your Render API URL after deployment
    const API_URL = 'https://your-api-name.onrender.com';
    
    // Fallback/demo mode when API is not available
    const DEMO_MODE = true;

    // ============================================
    // DOM Elements
    // ============================================
    const form = document.getElementById('estimator-form');
    const resultPlaceholder = document.getElementById('result-placeholder');
    const resultLoading = document.getElementById('result-loading');
    const resultSuccess = document.getElementById('result-success');
    const resultError = document.getElementById('result-error');
    const estimateValue = document.getElementById('estimate-value');
    const estimateLow = document.getElementById('estimate-low');
    const estimateHigh = document.getElementById('estimate-high');
    const errorMessage = document.getElementById('error-message');
    const tryAgainBtn = document.getElementById('try-again');
    const tryAgainErrorBtn = document.getElementById('try-again-error');

    // ============================================
    // Utility Functions
    // ============================================
    
    /**
     * Format a number as currency (USD)
     * @param {number} amount - The amount to format
     * @returns {string} Formatted currency string
     */
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }

    /**
     * Show a specific result state and hide others
     * @param {string} state - The state to show: 'placeholder', 'loading', 'success', 'error'
     */
    function showResultState(state) {
        // Hide all states
        resultPlaceholder.style.display = 'none';
        resultLoading.classList.remove('active');
        resultSuccess.classList.remove('active');
        resultError.classList.remove('active');

        // Show requested state
        switch (state) {
            case 'placeholder':
                resultPlaceholder.style.display = 'block';
                break;
            case 'loading':
                resultLoading.classList.add('active');
                break;
            case 'success':
                resultSuccess.classList.add('active');
                break;
            case 'error':
                resultError.classList.add('active');
                break;
        }
    }

    /**
     * Generate a demo estimate based on input features
     * This is used when the API is not available
     * @param {object} data - The property data
     * @returns {number} Estimated price
     */
    function generateDemoEstimate(data) {
        // Simple estimation model for demo purposes
        // Base price per sqft varies by "region" (based on zip code first digit)
        const zipPrefix = parseInt(data.zipcode.toString()[0]) || 5;
        const basePricePerSqft = 150 + (zipPrefix * 20);
        
        // Base calculation
        let estimate = data.sqft * basePricePerSqft;
        
        // Bedroom adjustment (+$15,000 per bedroom after 2)
        if (data.beds > 2) {
            estimate += (data.beds - 2) * 15000;
        }
        
        // Bathroom adjustment (+$10,000 per bathroom after 1)
        if (data.baths > 1) {
            estimate += (data.baths - 1) * 10000;
        }
        
        // Age depreciation (-0.5% per year, max 30%)
        const ageDepreciation = Math.min(data.age * 0.005, 0.30);
        estimate *= (1 - ageDepreciation);
        
        // Add some randomness for realism (±5%)
        const randomFactor = 0.95 + (Math.random() * 0.10);
        estimate *= randomFactor;
        
        return Math.round(estimate);
    }

    // ============================================
    // API Functions
    // ============================================
    
    /**
     * Send prediction request to the ML API
     * @param {object} data - The property data to send
     * @returns {Promise<object>} The prediction result
     */
    async function getPrediction(data) {
        // If in demo mode or API URL not set, use demo estimate
        if (DEMO_MODE || API_URL.includes('your-api-name')) {
            // Simulate API delay
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            const estimate = generateDemoEstimate(data);
            return {
                estimate: estimate,
                low: Math.round(estimate * 0.9),
                high: Math.round(estimate * 1.1)
            };
        }

        // Make actual API call
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sqft: data.sqft,
                beds: data.beds,
                baths: data.baths,
                age: data.age
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();
        
        // Calculate range (±10% of estimate)
        const estimate = result.estimate;
        return {
            estimate: estimate,
            low: Math.round(estimate * 0.9),
            high: Math.round(estimate * 1.1)
        };
    }

    // ============================================
    // Form Handling
    // ============================================
    
    /**
     * Handle form submission
     * @param {Event} e - The submit event
     */
    async function handleSubmit(e) {
        e.preventDefault();

        // Collect form data
        const formData = {
            zipcode: document.getElementById('zipcode').value.trim(),
            sqft: parseFloat(document.getElementById('sqft').value),
            beds: parseInt(document.getElementById('beds').value),
            baths: parseFloat(document.getElementById('baths').value),
            age: parseInt(document.getElementById('age').value)
        };

        // Validate data
        if (!formData.zipcode || formData.zipcode.length !== 5) {
            showError('Please enter a valid 5-digit ZIP code.');
            return;
        }

        if (isNaN(formData.sqft) || formData.sqft < 200) {
            showError('Please enter a valid square footage (minimum 200 sq ft).');
            return;
        }

        if (isNaN(formData.beds) || formData.beds < 0) {
            showError('Please enter a valid number of bedrooms.');
            return;
        }

        if (isNaN(formData.baths) || formData.baths < 0) {
            showError('Please enter a valid number of bathrooms.');
            return;
        }

        if (isNaN(formData.age) || formData.age < 0) {
            showError('Please enter a valid age for the home.');
            return;
        }

        // Show loading state
        showResultState('loading');

        try {
            // Get prediction from API
            const result = await getPrediction(formData);
            
            // Display results
            estimateValue.textContent = formatCurrency(result.estimate);
            estimateLow.textContent = formatCurrency(result.low);
            estimateHigh.textContent = formatCurrency(result.high);
            
            showResultState('success');
        } catch (error) {
            console.error('Prediction error:', error);
            showError('Unable to get estimate. Please try again later.');
        }
    }

    /**
     * Show error message
     * @param {string} message - The error message to display
     */
    function showError(message) {
        errorMessage.textContent = message;
        showResultState('error');
    }

    /**
     * Reset the form and show placeholder
     */
    function resetForm() {
        form.reset();
        showResultState('placeholder');
    }

    // ============================================
    // Event Listeners
    // ============================================
    
    if (form) {
        form.addEventListener('submit', handleSubmit);
    }

    if (tryAgainBtn) {
        tryAgainBtn.addEventListener('click', resetForm);
    }

    if (tryAgainErrorBtn) {
        tryAgainErrorBtn.addEventListener('click', function() {
            showResultState('placeholder');
        });
    }

    // ============================================
    // Input Formatting
    // ============================================
    
    // Format ZIP code input (numbers only)
    const zipcodeInput = document.getElementById('zipcode');
    if (zipcodeInput) {
        zipcodeInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/\D/g, '').slice(0, 5);
        });
    }

    // Format square footage with commas (visual only)
    const sqftInput = document.getElementById('sqft');
    if (sqftInput) {
        sqftInput.addEventListener('blur', function() {
            if (this.value) {
                const num = parseFloat(this.value.replace(/,/g, ''));
                if (!isNaN(num)) {
                    // Store the raw value and display formatted
                    this.dataset.rawValue = num;
                }
            }
        });
    }

    // Initialize
    showResultState('placeholder');

})();

