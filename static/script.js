// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    // Hide results and errors
    hideResults();
    hideError();
}

// CNR Form Submission
document.getElementById('cnr-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const cnr = document.getElementById('cnr').value.trim();
    const submitBtn = document.getElementById('cnr-submit');
    
    // Validation
    if (cnr.length !== 16) {
        showError('CNR must be exactly 16 characters');
        return;
    }
    
    // Show loading state
    setLoading(submitBtn, true);
    hideResults();
    hideError();
    
    try {
        const response = await fetch('/api/search/cnr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cnr: cnr })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            displayCNRResults(data.data);
        } else {
            showError(data.error || 'Failed to fetch case details');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        setLoading(submitBtn, false);
    }
});

// Case Form Submission
document.getElementById('case-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        state_code: document.getElementById('state').value,
        dist_code: document.getElementById('district').value,
        case_type: document.getElementById('case-type').value.trim(),
        case_no: document.getElementById('case-no').value.trim(),
        case_year: document.getElementById('case-year').value.trim()
    };
    
    const submitBtn = document.getElementById('case-submit');
    
    // Validation
    if (!formData.state_code || !formData.dist_code || !formData.case_type || 
        !formData.case_no || !formData.case_year) {
        showError('All fields are required');
        return;
    }
    
    if (formData.case_year.length !== 4) {
        showError('Year must be 4 digits');
        return;
    }
    
    // Show loading state
    setLoading(submitBtn, true);
    hideResults();
    hideError();
    
    try {
        const response = await fetch('/api/search/case', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            displayCaseResults(data.data);
        } else {
            showError(data.error || 'Failed to fetch case details');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        setLoading(submitBtn, false);
    }
});

// Load states on page load
window.addEventListener('DOMContentLoaded', async function() {
    try {
        const response = await fetch('/api/states');
        const data = await response.json();
        
        if (data.success && data.data) {
            const stateSelect = document.getElementById('state');
            data.data.forEach(state => {
                const option = document.createElement('option');
                option.value = state.code;
                option.textContent = state.name;
                stateSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading states:', error);
    }
});

// Load districts when state changes
document.getElementById('state').addEventListener('change', async function() {
    const stateCode = this.value;
    const districtSelect = document.getElementById('district');
    
    // Clear existing options
    districtSelect.innerHTML = '<option value="">Select District</option>';
    
    if (!stateCode) return;
    
    try {
        const response = await fetch(`/api/districts/${stateCode}`);
        const data = await response.json();
        
        if (data.success && data.data) {
            data.data.forEach(district => {
                const option = document.createElement('option');
                option.value = district.code;
                option.textContent = district.name;
                districtSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading districts:', error);
    }
});

// Display CNR Results
function displayCNRResults(data) {
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');
    
    let html = '<div class="result-item">';
    html += '<h4>Case Details</h4>';
    
    const fields = [
        { label: 'CNR', value: data.cnr },
        { label: 'Case Number', value: data.case_number },
        { label: 'Case Type', value: data.case_type },
        { label: 'Filing Date', value: data.filing_date },
        { label: 'Petitioner', value: data.petitioner },
        { label: 'Respondent', value: data.respondent },
        { label: 'Court Name', value: data.court_name },
        { label: 'Judge', value: data.judge },
        { label: 'Status', value: data.status },
        { label: 'Next Hearing', value: data.next_hearing }
    ];
    
    fields.forEach(field => {
        if (field.value && field.value !== 'None' && field.value !== 'N/A') {
            html += `
                <div class="result-row">
                    <div class="result-label">${field.label}:</div>
                    <div class="result-value">${field.value}</div>
                </div>
            `;
        }
    });
    
    html += '</div>';
    
    resultsContent.innerHTML = html;
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Display Case Results
function displayCaseResults(cases) {
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');
    
    let html = '';
    
    cases.forEach((caseData, index) => {
        html += `<div class="result-item">`;
        html += `<h4>Case ${index + 1}</h4>`;
        
        const fields = [
            { label: 'Case Number', value: caseData.case_number },
            { label: 'Petitioner', value: caseData.petitioner },
            { label: 'Respondent', value: caseData.respondent },
            { label: 'Status', value: caseData.status }
        ];
        
        fields.forEach(field => {
            if (field.value && field.value !== 'None' && field.value !== 'N/A') {
                html += `
                    <div class="result-row">
                        <div class="result-label">${field.label}:</div>
                        <div class="result-value">${field.value}</div>
                    </div>
                `;
            }
        });
        
        html += '</div>';
    });
    
    resultsContent.innerHTML = html;
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Show error message
function showError(message) {
    const errorSection = document.getElementById('error-section');
    const errorMessage = document.getElementById('error-message');
    
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
    
    // Scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

// Hide error message
function hideError() {
    document.getElementById('error-section').style.display = 'none';
}

// Hide results
function hideResults() {
    document.getElementById('results-section').style.display = 'none';
}

// Set loading state for button
function setLoading(button, isLoading) {
    const btnText = button.querySelector('.btn-text');
    const btnLoader = button.querySelector('.btn-loader');
    
    if (isLoading) {
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
        button.disabled = true;
    } else {
        btnText.style.display = 'inline-block';
        btnLoader.style.display = 'none';
        button.disabled = false;
    }
}
