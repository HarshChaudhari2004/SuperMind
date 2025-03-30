// Initialize Supabase client
const SUPABASE_URL = 'https://fwdvbffemldsiustobyd.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ3ZHZiZmZlbWxkc2l1c3RvYnlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzgzMzUzNDksImV4cCI6MjA1MzkxMTM0OX0.Nud4_Aqz9xsTRs6ZXzbkHSZK9IzcSElH4j6AacS9Z1Q';

// Create context menu when extension is installed
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'saveToSupermind',
    title: 'Save to SuperMind',
    contexts: ['selection']
  });
  console.log("SuperMind extension installed.");
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'saveToSupermind') {
    try {
      // Get the selected text
      const selectedText = info.selectionText;
      
      // Get session from storage
      const { sessionData } = await chrome.storage.local.get(['sessionData']);
      if (!sessionData) {
        // If not logged in, open the extension popup
        chrome.action.openPopup();
        return;
      }

      // Show saving notification
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon48.png',
        title: 'SuperMind',
        message: 'Saving your note...'
      });

      // Generate a smart title from the first sentence or line
      const generateSmartTitle = (text) => {
        const firstSentence = text.split(/[.!?]\s+/)[0];
        if (firstSentence.length > 100) {
          const firstLine = text.split('\n')[0];
          return firstLine.length > 100 ? 
            firstLine.slice(0, 97) + '...' : 
            firstLine;
        }
        return firstSentence;
      };

      // Prepare the data
      const data = {
        id: Math.random().toString(36).substr(2, 9),
        user_id: sessionData.user_id,
        title: generateSmartTitle(selectedText),
        video_type: 'note',
        tags: 'shared_note',
        user_notes: selectedText,
        date_added: new Date().toISOString(),
        thumbnail_url: null,
        original_url: tab.url,
        channel_name: 'Shared Notes'
      };

      // First try to refresh the session
      const refreshResponse = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=refresh_token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'apikey': SUPABASE_ANON_KEY
        },
        body: JSON.stringify({
          refresh_token: sessionData.refresh_token
        })
      });

      if (!refreshResponse.ok) {
        const errorData = await refreshResponse.json();
        console.error('Session refresh failed:', errorData);
        throw new Error('Session expired. Please log in again.');
      }

      const { access_token, expires_at } = await refreshResponse.json();

      // Update session in storage
      await chrome.storage.local.set({
        sessionData: {
          ...sessionData,
          access_token,
          expires_at
        }
      });

      // Save to Supabase with new token
      const response = await fetch(`${SUPABASE_URL}/rest/v1/content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${access_token}`,
          'apikey': SUPABASE_ANON_KEY
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Save note failed:', errorData);
        throw new Error(errorData.message || 'Failed to save note');
      }

      // Show success notification
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon48.png',
        title: 'SuperMind',
        message: 'Note saved successfully!'
      });

    } catch (error) {
      console.error('Error saving note:', error);
      // Show error notification
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon48.png',
        title: 'SuperMind',
        message: error.message || 'Failed to save note. Please try again.'
      });
    }
  }
});

// Listen for auth state changes
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local' && changes.sessionData) {
    const newSession = changes.sessionData.newValue;
    if (newSession) {
      console.log('User authenticated');
    } else {
      console.log('User signed out');
    }
  }
});
