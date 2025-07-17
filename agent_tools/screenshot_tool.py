from datetime import datetime
import pyautogui

def take_screenshot(save_path: str = None, window_title: str = None) -> str:
    """
    Capture a screenshot; auto‑names file if no path given.
    Optionally activates a window by title before capturing.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Ensure path has .png extension
    path = save_path or f"screenshot_{ts}.png"
    if path and not path.lower().endswith(('.png', '.jpg', '.jpeg')):
        path += '.png'

    if window_title:
        try:
            import pygetwindow as gw
            wins = gw.getWindowsWithTitle(window_title)
            if wins:
                wins[0].activate()
        except Exception:
            pass

    img = pyautogui.screenshot()
    img.save(path)
    return f"Screenshot saved to {path}"


if __name__ == "__main__":
    take_screenshot(save_path="screenshot.png", window_title="Notepad")