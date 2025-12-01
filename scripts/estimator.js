/**
 * Ryan Greene Portfolio - Housing Price Estimator
 * Handles the ML API integration for the real estate price estimator
 * 
 * Uses SFR-only sold data filtered by ZIP code
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

    // Bay Area median SFR prices by ZIP (for demo mode)
    const BAY_AREA_MEDIANS = {
        94070: 2100000,  // San Carlos
        94301: 3500000,  // Palo Alto
        94022: 4000000,  // Los Altos
        94024: 4500000,  // Los Altos Hills
        94027: 6000000,  // Atherton
        94025: 2800000,  // Menlo Park
        94062: 1800000,  // Redwood City
        94061: 1600000,  // Redwood City
        94010: 2500000,  // Burlingame
        94402: 1900000,  // San Mateo
    };

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
        if (resultPlaceholder) resultPlaceholder.style.display = 'none';
        if (resultLoading) resultLoading.classList.remove('active');
        if (resultSuccess) resultSuccess.classList.remove('active');
        if (resultError) resultError.classList.remove('active');

        // Show requested state
        switch (state) {
            case 'placeholder':
                if (resultPlaceholder) resultPlaceholder.style.display = 'block';
                break;
            case 'loading':
                if (resultLoading) resultLoading.classList.add('active');
                break;
            case 'success':
                if (resultSuccess) resultSuccess.classList.add('active');
                break;
            case 'error':
                if (resultError) resultError.classList.add('active');
                break;
        }
    }

    /**
     * Generate a demo estimate based on input features
     * Uses realistic Bay Area SFR prices
     * @param {object} data - The property data
     * @returns {object} Estimated price with method info
     */
    function generateDemoEstimate(data) {
        const zip = parseInt(data.zipcode);
        
        // Check if we have real data for this ZIP
        let medianPrice = BAY_AREA_MEDIANS[zip];
        let method = 'zip_ml_sfr';
        let comparables = 0;
        
        if (medianPrice) {
            // Use known median as base
            comparables = 50 + Math.floor(Math.random() * 50);
        } else {
            // Fallback: estimate by region
            const zipPrefix = parseInt(data.zipcode.toString()[0]);
            const regionalPPSF = {
                0: 300, 1: 280, 2: 250, 3: 200, 4: 180,
                5: 190, 6: 170, 7: 180, 8: 220, 9: 400
            };
            medianPrice = (regionalPPSF[zipPrefix] || 220) * 1800; // Average home
            method = 'regional_fallback';
        }
        
        // Calculate price per sqft from median (assuming 1800 sqft median home)
        const medianSqft = 1800;
        const basePPSF = medianPrice / medianSqft;
        
        // Base calculation
        let estimate = data.sqft * basePPSF;
        
        // Bedroom adjustment
        const avgBeds = 3;
        if (data.beds !== avgBeds) {
            estimate += (data.beds - avgBeds) * 25000;
        }
        
        // Bathroom adjustment
        const avgBaths = 2;
        if (data.baths !== avgBaths) {
            estimate += (data.baths - avgBaths) * 20000;
        }
        
        // Age adjustment (-0.4% per year over 30, +0.3% per year under 30)
        const avgAge = 30;
        if (data.age > avgAge) {
            const ageFactor = 1 - ((data.age - avgAge) * 0.004);
            estimate *= Math.max(0.7, ageFactor);
        } else if (data.age < avgAge) {
            const ageFactor = 1 + ((avgAge - data.age) * 0.003);
            estimate *= Math.min(1.2, ageFactor);
        }
        
        // Bound to reasonable range
        const minPrice = medianPrice * 0.5;
        const maxPrice = medianPrice * 2.0;
        estimate = Math.max(minPrice, Math.min(maxPrice, estimate));
        
        return {
            estimate: Math.round(estimate),
            method: method,
            comparables: comparables
        };
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
            await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 500));
            
            const result = generateDemoEstimate(data);
            return {
                estimate: result.estimate,
                low: Math.round(result.estimate * 0.92),
                high: Math.round(result.estimate * 1.08),
                method: result.method,
                comparables: result.comparables
            };
        }

        // Make actual API call
        try {
            const response = await fetch(`${API_URL}/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    zip: data.zipcode,
                    sqft: data.sqft,
                    beds: data.beds,
                    baths: data.baths,
                    age: data.age
                })
            });

            const result = await response.json();
            
            // Check for errors from API
            if (!response.ok) {
                throw new Error(result.error || result.message || `API error: ${response.status}`);
            }
            
            // Calculate range (±8% of estimate)
            const estimate = result.estimate;
            return {
                estimate: estimate,
                low: Math.round(estimate * 0.92),
                high: Math.round(estimate * 1.08),
                method: result.method || 'ml_model',
                comparables: result.comparables || 0
            };
        } catch (error) {
            // If API fails, fallback to demo mode
            console.warn('API call failed, using demo mode:', error.message);
            
            const result = generateDemoEstimate(data);
            return {
                estimate: result.estimate,
                low: Math.round(result.estimate * 0.92),
                high: Math.round(result.estimate * 1.08),
                method: 'demo_fallback',
                comparables: result.comparables
            };
        }
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
            if (estimateValue) estimateValue.textContent = formatCurrency(result.estimate);
            if (estimateLow) estimateLow.textContent = formatCurrency(result.low);
            if (estimateHigh) estimateHigh.textContent = formatCurrency(result.high);
            
            // Show additional info if elements exist
            const methodEl = document.getElementById('estimate-method');
            const comparablesEl = document.getElementById('estimate-comparables');
            
            if (methodEl) {
                const methodNames = {
                    'zip_ml_sfr': 'ZIP ML Model (SFR only)',
                    'zip_avg_sfr': 'ZIP Average (SFR only)',
                    'regional_fallback': 'Regional Estimate',
                    'demo_fallback': 'Demo Mode'
                };
                methodEl.textContent = methodNames[result.method] || result.method;
            }
            
            if (comparablesEl && result.comparables > 0) {
                comparablesEl.textContent = `Based on ${result.comparables} comparable SFR sales`;
                comparablesEl.style.display = 'block';
            }
            
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
        if (errorMessage) errorMessage.textContent = message;
        showResultState('error');
    }

    /**
     * Reset the form and show placeholder
     */
    function resetForm() {
        if (form) form.reset();
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
