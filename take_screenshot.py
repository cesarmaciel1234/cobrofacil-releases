from PIL import ImageGrab
import os

artifact_dir = r"C:\Users\cesar\.gemini\antigravity\brain\7ef542c2-e200-4638-9e30-e356f963fd7a"
screenshot_path = os.path.join(artifact_dir, "current_screen.png")

# Capturar toda la pantalla
try:
    screenshot = ImageGrab.grab()
    screenshot.save(screenshot_path)
    print(f"Screenshot saved to {screenshot_path}")
except Exception as e:
    print(f"Error capturing screen: {e}")
