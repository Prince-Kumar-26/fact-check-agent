document.addEventListener('DOMContentLoaded', () => {
    const checkBtn = document.getElementById('check-btn');
    const claimInput = document.getElementById('claim-input');
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const resultsDashboard = document.getElementById('results-dashboard');
    const verdictText = document.getElementById('verdict-text');
    const verdictConfidence = document.getElementById('verdict-confidence');
    const verdictSummary = document.getElementById('verdict-summary');
    const citationsList = document.getElementById('citations-list');
    const supportCase = document.getElementById('support-case');
    const opposeCase = document.getElementById('oppose-case');
    const supportRebuttal = document.getElementById('support-rebuttal');
    const opposeRebuttal = document.getElementById('oppose-rebuttal');

    checkBtn.addEventListener('click', async () => {
        const claim = claimInput.value.trim();
        if (!claim) return;

        // Reset UI
        errorState.classList.add('hidden');
        resultsDashboard.classList.add('hidden');
        loadingState.classList.remove('hidden');
        checkBtn.disabled = true;

        try {
            // Note: In development, point to the FastAPI server running on localhost:8000
            const response = await fetch('http://localhost:8000/api/factcheck', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ claim: claim })
            });

            const data = await response.json();

            if (data.status === 'REJECTED') {
                errorState.textContent = data.rejection_reason || "The claim was rejected by our guardrails.";
                errorState.classList.remove('hidden');
            } else if (data.status === 'COMPLETED') {
                // Populate dashboard
                verdictText.textContent = data.verdict;
                
                // Color coding based on verdict
                verdictText.style.color = data.verdict === 'True' || data.verdict === 'Mostly True' 
                    ? 'var(--accent-support)' 
                    : data.verdict === 'False' || data.verdict === 'Misleading' 
                        ? 'var(--accent-oppose)' 
                        : 'var(--text-color)';

                verdictConfidence.textContent = `${data.confidence}% Confidence`;
                verdictSummary.textContent = data.summary;

                // Render markdown content
                supportCase.innerHTML = marked.parse(data.support_case || "No case built.");
                opposeCase.innerHTML = marked.parse(data.oppose_case || "No case built.");
                supportRebuttal.innerHTML = marked.parse(data.support_rebuttal || "No rebuttal.");
                opposeRebuttal.innerHTML = marked.parse(data.oppose_rebuttal || "No rebuttal.");

                // Render citations
                citationsList.innerHTML = '';
                if (data.citations && data.citations.length > 0) {
                    data.citations.forEach(c => {
                        const li = document.createElement('li');
                        li.innerHTML = `<a href="${c.url}" target="_blank">${c.title}</a>`;
                        citationsList.appendChild(li);
                    });
                } else {
                    citationsList.innerHTML = '<li>No citations provided.</li>';
                }

                resultsDashboard.classList.remove('hidden');
            } else {
                errorState.textContent = "An unknown error occurred.";
                errorState.classList.remove('hidden');
            }

        } catch (error) {
            errorState.textContent = "Failed to connect to the backend API. Ensure it is running.";
            errorState.classList.remove('hidden');
        } finally {
            loadingState.classList.add('hidden');
            checkBtn.disabled = false;
        }
    });
});
