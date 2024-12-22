// Function to check if the URL is from YouTube
function isYouTubeUrl(url) {
  return url.includes("youtube.com") || url.includes("youtu.be");
}

// Function to check if the URL is from Instagram
function isInstagramUrl(url) {
  return url.includes("instagram.com");
}

// Function to send the URL to the appropriate backend based on platform
function sendUrlToBackend(url) {
  let backendUrl;

  // Check for YouTube URL
  if (isYouTubeUrl(url)) {
    backendUrl = "http://127.0.0.1:8000/api/generate-summary/"; // YouTube URL processing
  } 
  // Check for Instagram URL
  else if (isInstagramUrl(url)) {
    backendUrl = "http://127.0.0.1:8000/instagram/api/analyze-instagram/"; // Instagram URL processing
  }
  // Handle all other URLs (generic websites)
  else {
    backendUrl = "http://127.0.0.1:8000/web/api/analyze-website/"; // New endpoint for other websites
  }

  // Send the URL to the appropriate backend
  fetch(backendUrl + "?url=" + encodeURIComponent(url), {
    method: "GET",
  })
  .then(response => response.json())
  .then(data => {
    console.log("Backend response:", data);
    alert("Data processed successfully!");
  })
  .catch(error => {
    console.error("Error sending URL to backend:", error);
    alert("Error processing URL.");
  });
}

// Listen for button click to send the URL
document.getElementById("sendUrlBtn").addEventListener("click", function() {
  // Get the current tab's URL
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    const currentUrl = tabs[0].url;
    sendUrlToBackend(currentUrl);
  });
});
