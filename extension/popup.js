document.addEventListener('DOMContentLoaded', async () => {
  const authForm = document.getElementById('authForm')
  const actionSection = document.getElementById('actionSection')
  const email = document.getElementById('email')
  const password = document.getElementById('password')
  const authButton = document.getElementById('authButton')
  const switchAuth = document.getElementById('switchAuth')
  const signOutBtn = document.getElementById('signOutBtn')
  const sendUrlBtn = document.getElementById('sendUrlBtn')
  const responseMessage = document.getElementById('responseMessage')
  const progressContainer = document.getElementById('progressContainer')
  const progressFill = document.getElementById('progressFill')
  const progressText = document.getElementById('progressText')

  let isSignUp = false

  // Function to update progress bar
  const updateProgress = (percent, text) => {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = text;
  };

  // Function to show/hide progress bar
  const toggleProgress = (show) => {
    progressContainer.style.display = show ? 'block' : 'none';
    if (!show) {
      updateProgress(0, 'Processing...');
    }
  };

  // Enhanced checkAuth to handle persistent sessions
  const checkAuth = async () => {
    try {
      // First check chrome storage for cached session
      const stored = await chrome.storage.local.get(['sessionData']);
      if (stored.sessionData) {
        // Validate stored session with Supabase
        const { session, error } = await supabaseClient.getSession();
        if (session) {
          authForm.style.display = 'none';
          actionSection.style.display = 'flex';
          return;
        }
      }
      
      // No valid session found
      authForm.style.display = 'flex';
      actionSection.style.display = 'none';
    } catch (error) {
      console.error('Auth check failed:', error);
      authForm.style.display = 'flex';
      actionSection.style.display = 'none';
    }
  };

  checkAuth()

  // Modify the successful sign in handler
  const handleSuccessfulAuth = async (session) => {
    // Store session data in chrome storage
    await chrome.storage.local.set({
      sessionData: {
        access_token: session.access_token,
        refresh_token: session.refresh_token,
        expires_at: session.expires_at,
        user_id: session.user.id
      }
    });
    checkAuth();
  };

  // Update auth form submit handler
  authButton.addEventListener('click', async () => {
    if (!email.value || !password.value) {
      responseMessage.textContent = 'Please fill in all fields'
      responseMessage.className = 'error'
      return
    }

    try {
      const { data, error } = isSignUp 
        ? await supabaseClient.signUp(email.value, password.value)
        : await supabaseClient.signIn(email.value, password.value)

      if (error) throw error

      if (isSignUp) {
        responseMessage.textContent = 'Check your email for verification!'
        responseMessage.className = 'success'
      } else if (data.session) {
        await handleSuccessfulAuth(data.session);
      }
    } catch (error) {
      responseMessage.textContent = error.message
      responseMessage.className = 'error'
    }
  })

  // Switch between sign in/up
  switchAuth.addEventListener('click', () => {
    isSignUp = !isSignUp
    authButton.textContent = isSignUp ? 'Sign Up' : 'Sign In'
    switchAuth.textContent = isSignUp 
      ? 'Already have an account? Sign In'
      : "Don't have an account? Sign Up"
  })

  // Update sign out handler
  signOutBtn.addEventListener('click', async () => {
    try {
      const { error } = await supabaseClient.signOut();
      if (error) throw error;
      
      // Clear stored session data
      await chrome.storage.local.remove(['sessionData']);
      checkAuth();
    } catch (error) {
      responseMessage.textContent = error.message;
      responseMessage.className = 'error';
    }
  })

  // Update the Send URL handler
  sendUrlBtn.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
    
    try {
      // Show loading state
      sendUrlBtn.disabled = true;
      sendUrlBtn.innerHTML = '<span class="loading-spinner"></span>Saving...';
      toggleProgress(true);
      updateProgress(20, '\u{1F680} Initializing...');
      
      const { session, error } = await supabaseClient.getSession();
      if (error || !session) {
        throw new Error('Authentication required');
      }

      responseMessage.textContent = '';
      updateProgress(40, '\u{1F50D} Processing URL...');
      
      // Determine the correct endpoint and method based on URL type
      let endpoint = '/web/api/analyze-website/';
      let method = 'GET';
      let requestConfig = {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Accept': 'application/json',
          'X-CSRFToken': '', // Will be updated if we get a CSRF token
        },
        credentials: 'include' // Important for CORS and cookies
      };
      
      // Add query parameters for website analysis
      const params = new URLSearchParams({
        url: tab.url,
        user_id: session.user.id
      });
      endpoint += `?${params.toString()}`;
      
      if (tab.url.includes("youtube.com") || tab.url.includes("youtu.be")) {
        endpoint = '/api/generate-summary/';
        method = 'POST';
        requestConfig = {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`,
            'Accept': 'application/json',
            'X-CSRFToken': '', // Will be updated if we get a CSRF token
          },
          credentials: 'include',
          body: JSON.stringify({
            url: tab.url,
            user_id: session.user.id
          })
        };
      } else if (/instagram\.com\/(?:p|reels|reel)\/[A-Za-z0-9_-]+/.test(tab.url)) {
        endpoint = '/instagram/api/analyze-instagram/';
        method = 'GET';
        const params = new URLSearchParams({
          url: tab.url,
          user_id: session.user.id
        });
        endpoint += `?${params.toString()}`;
        requestConfig = {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Accept': 'application/json',
            'X-CSRFToken': '', // Will be updated if we get a CSRF token
          },
          credentials: 'include'
        };
      } else if (tab.url.includes('reddit.com/r/') || tab.url.includes('redd.it/')) {
        endpoint = `/web/api/analyze-reddit/`;
        method = 'GET';
        const params = new URLSearchParams({
          url: tab.url,
          user_id: session.user.id
        });
        endpoint += `?${params.toString()}`;
        requestConfig = {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Accept': 'application/json',
            'X-CSRFToken': '', // Will be updated if we get a CSRF token
          },
          credentials: 'include'
        };
      }

      updateProgress(60, '\u{1F4E4} Sending request...');

      // Try to get CSRF token first
      try {
        const csrfResponse = await fetch(`https://crazymind.up.railway.app/web/get-csrf-token/`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Accept': 'application/json'
          },
          credentials: 'include'
        });
        
        if (csrfResponse.ok) {
          const csrfData = await csrfResponse.json();
          requestConfig.headers['X-CSRFToken'] = csrfData.csrfToken || '';
        }
      } catch (csrfError) {
        console.warn('Failed to get CSRF token:', csrfError);
      }

      updateProgress(80, '\u{2699} Processing response...');

      const response = await fetch(`https://crazymind.up.railway.app${endpoint}`, {
        method,
        ...requestConfig
      });

      // First get the response text to check if it's JSON
      const responseText = await response.text();
      
      // Try to parse as JSON, if it fails, we know it's not JSON
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('Server returned non-JSON response:', responseText.substring(0, 200));
        throw new Error('Server returned an invalid response. Please try again later.');
      }

      if (!response.ok) {
        throw new Error(data.error || `Server error: ${response.status}`);
      }
      
      if (!data.error) {
        updateProgress(100, '\u{2705} Success!');
        responseMessage.textContent = 'Saved to SuperMind!';
        responseMessage.className = 'success';
        setTimeout(() => window.close(), 1500);
      } else {
        throw new Error(data.error || 'Failed to save URL');
      }
    } catch (error) {
      console.error('Error:', error);
      responseMessage.textContent = error.message;
      responseMessage.className = 'error';
    } finally {
      // Reset button state and hide progress bar
      sendUrlBtn.disabled = false;
      sendUrlBtn.textContent = 'Save to SuperMind';
      setTimeout(() => toggleProgress(false), 1000);
    }
  })
})
