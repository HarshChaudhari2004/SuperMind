chrome.runtime.onInstalled.addListener(() => {
  console.log("SuperMind extension installed.")
})

// Listen for auth state changes
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local' && changes.session) {
    const newSession = changes.session.newValue
    if (newSession) {
      console.log('User authenticated')
    } else {
      console.log('User signed out')
    }
  }
})
