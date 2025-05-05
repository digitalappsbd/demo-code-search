/**
 * Copies the provided text to clipboard using multiple methods as fallbacks
 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
  // Method 1: Using the Clipboard API (most modern browsers)
  try {
    console.log("Attempting to copy using Navigator Clipboard API");
    await navigator.clipboard.writeText(text);
    console.log("Successfully copied with Navigator Clipboard API");
    return true;
  } catch (error) {
    console.error('Failed to copy text using Navigator Clipboard API:', error);
    
    // Method 2: Fallback using document.execCommand (older browsers)
    try {
      console.log("Attempting to copy using execCommand fallback");
      const textarea = document.createElement('textarea');
      textarea.value = text;
      
      // Make the textarea out of viewport
      textarea.style.position = 'fixed';
      textarea.style.left = '-999999px';
      textarea.style.top = '-999999px';
      document.body.appendChild(textarea);
      
      // Select and copy the text
      textarea.focus();
      textarea.select();
      const success = document.execCommand('copy');
      document.body.removeChild(textarea);
      
      if (success) {
        console.log("Successfully copied with execCommand");
        return true;
      } else {
        console.error('Failed to copy text using execCommand fallback');
        return false;
      }
    } catch (fallbackError) {
      console.error('Failed to copy text using fallback method:', fallbackError);
      return false;
    }
  }
}; 