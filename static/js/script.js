document.addEventListener('DOMContentLoaded', function() {
    const fetchButton = document.getElementById('fetchTranscript');
    const videoIdInput = document.getElementById('videoId');
    const resultDiv = document.getElementById('result');
    const responseData = document.getElementById('responseData');

    fetchButton.addEventListener('click', async function() {
        const videoId = videoIdInput.value.trim();
        
        if (!videoId) {
            alert('Please enter a video ID');
            return;
        }

        try {
            fetchButton.disabled = true;
            fetchButton.innerHTML = 'Loading...';

            const response = await fetch(`/api/transcript/${videoId}`);
            const data = await response.json();

            responseData.textContent = JSON.stringify(data, null, 2);
            resultDiv.style.display = 'block';
        } catch (error) {
            responseData.textContent = JSON.stringify({
                error: 'Failed to fetch transcript',
                details: error.message
            }, null, 2);
            resultDiv.style.display = 'block';
        } finally {
            fetchButton.disabled = false;
            fetchButton.innerHTML = 'Get Transcript';
        }
    });

    // Allow Enter key to trigger the fetch
    videoIdInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            fetchButton.click();
        }
    });
});
