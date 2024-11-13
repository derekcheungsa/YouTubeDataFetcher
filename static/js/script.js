document.addEventListener('DOMContentLoaded', function() {
    // Helper function to safely get DOM elements
    function getElement(id, context = document) {
        const element = context.getElementById(id);
        if (!element) {
            console.warn(`Element with id '${id}' not found`);
            return null;
        }
        return element;
    }

    // Transcript functionality elements
    const fetchTranscriptButton = getElement('fetchTranscript');
    const videoIdInput = getElement('videoId');
    const timestampsToggle = getElement('includeTimestamps');
    const transcriptResultDiv = getElement('transcriptResult');
    const transcriptResponseData = getElement('transcriptResponseData');

    // Comments functionality elements
    const fetchCommentsButton = getElement('fetchComments');
    const commentVideoIdInput = getElement('commentVideoId');
    const maxResultsInput = getElement('maxResults');
    const commentsResultDiv = getElement('commentsResult');
    const commentsResponseData = getElement('commentsResponseData');

    // Transcript fetch handler
    if (fetchTranscriptButton && videoIdInput && timestampsToggle && transcriptResultDiv && transcriptResponseData) {
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

        // Enter key handler for transcript
        videoIdInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                fetchTranscriptButton.click();
            }
        });
    }

    // Comments fetch handler
    if (fetchCommentsButton && commentVideoIdInput && maxResultsInput && commentsResultDiv && commentsResponseData) {
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

        // Enter key handlers for comments
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
    }
});
