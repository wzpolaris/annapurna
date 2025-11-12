/**
 * Shared utility for persisting drawer width across all drawer types.
 * This allows PDF viewer, markdown drawers, and any future drawers
 * to remember and share the same width preference.
 */

const DRAWER_WIDTH_KEY = 'drawer-width';
const DEFAULT_DRAWER_WIDTH = 66; // 66% of screen (matches PDF viewer)

/**
 * Get the last used drawer width from localStorage.
 * Falls back to default if not set.
 */
export function getDrawerWidth(): number {
  try {
    const stored = localStorage.getItem(DRAWER_WIDTH_KEY);
    if (stored !== null) {
      const parsed = parseFloat(stored);
      if (!isNaN(parsed) && parsed >= 30 && parsed <= 70) {
        return parsed;
      }
    }
  } catch (error) {
    console.warn('Failed to read drawer width from localStorage:', error);
  }
  return DEFAULT_DRAWER_WIDTH;
}

/**
 * Save the drawer width to localStorage.
 * Clamps the value between 30 and 70.
 */
export function setDrawerWidth(width: number): void {
  try {
    const clamped = Math.min(Math.max(width, 30), 70);
    localStorage.setItem(DRAWER_WIDTH_KEY, String(clamped));
  } catch (error) {
    console.warn('Failed to save drawer width to localStorage:', error);
  }
}
