document.addEventListener('DOMContentLoaded', function() {
    // Transcript functionality
    const fetchTranscriptButton = document.getElementById('fetchTranscript');
    const videoIdInput = document.getElementById('videoId');
    const timestampsToggle = document.getElementById('includeTimestamps');
    const transcriptResultDiv = document.getElementById('transcriptResult');
    const transcriptResponseData = document.getElementById('transcriptResponseData');

    // Comments functionality
    const fetchCommentsButton = document.getElementById('fetchComments');
    const commentVideoIdInput = document.getElementById('commentVideoId');
    const maxResultsInput = document.getElementById('maxResults');
    const commentsResultDiv = document.getElementById('commentsResult');
    const commentsResponseData = document.getElementById('commentsResponseData');

    // Transcript fetch handler
    fetchTranscriptButton.addEventListener('click', async function() {
        const videoId = videoIdInput.value.trim();
        const includeTimestamps = timestampsToggle.checked;
        
        if (!videoId) {
            alert('Please enter a video ID');
            return;
        }

        try {
            fetchTranscriptButton.disabled = true;
            fetchTranscriptButton.innerHTML = 'Loading...';

            const url = `/api/transcript/${videoId}?timestamps=${includeTimestamps}`;
            const response = await fetch(url);
            const data = await response.json();

            transcriptResponseData.textContent = JSON.stringify(data, null, 2);
            transcriptResultDiv.style.display = 'block';
        } catch (error) {
            transcriptResponseData.textContent = JSON.stringify({
                error: 'Failed to fetch transcript',
                details: error.message
            }, null, 2);
            transcriptResultDiv.style.display = 'block';
        } finally {
            fetchTranscriptButton.disabled = false;
            fetchTranscriptButton.innerHTML = 'Get Transcript';
        }
    });

    // Comments fetch handler
    fetchCommentsButton.addEventListener('click', async function() {
        const videoId = commentVideoIdInput.value.trim();
        const maxResults = maxResultsInput.value.trim() || '100';
        
        if (!videoId) {
            alert('Please enter a video ID');
            return;
        }

        try {
            fetchCommentsButton.disabled = true;
            fetchCommentsButton.innerHTML = 'Loading...';

            const url = `/api/comments/${videoId}?max_results=${maxResults}`;
            const response = await fetch(url);
            const data = await response.json();

            commentsResponseData.textContent = JSON.stringify(data, null, 2);
            commentsResultDiv.style.display = 'block';
        } catch (error) {
            commentsResponseData.textContent = JSON.stringify({
                error: 'Failed to fetch comments',
                details: error.message
            }, null, 2);
            commentsResultDiv.style.display = 'block';
        } finally {
            fetchCommentsButton.disabled = false;
            fetchCommentsButton.innerHTML = 'Get Comments';
        }
    });

    // Enter key handlers
    videoIdInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            fetchTranscriptButton.click();
        }
    });

    commentVideoIdInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            fetchCommentsButton.click();
        }
    });

    maxResultsInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            fetchCommentsButton.click();
        }
    });
});
