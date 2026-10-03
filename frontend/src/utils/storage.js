// ============================================================
// CareerLens – Local Storage Utilities
// File: frontend/src/utils/storage.js
// ============================================================

export const APP_STORAGE_PREFIX = 'careerlens'

/**
 * Clear all cached user data, resume texts, and session storage
 * upon sign out or session termination.
 */
export function clearLocalUserData() {
  try {
    const keysToRemove = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (
        key &&
        (key.startsWith(APP_STORAGE_PREFIX) ||
          key.startsWith('careerlens_') ||
          key.startsWith('careerlens:') ||
          key.startsWith('last_resume_analysis'))
      ) {
        keysToRemove.push(key)
      }
    }
    keysToRemove.forEach((k) => localStorage.removeItem(k))

    const sessionKeysToRemove = []
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i)
      if (
        key &&
        (key.startsWith(APP_STORAGE_PREFIX) ||
          key.startsWith('careerlens_') ||
          key.startsWith('careerlens:') ||
          key.startsWith('last_resume_analysis'))
      ) {
        sessionKeysToRemove.push(key)
      }
    }
    sessionKeysToRemove.forEach((k) => sessionStorage.removeItem(k))
  } catch (err) {
    console.warn('Could not clear local user data:', err)
  }
}
