import subprocess

class TouchInterface:
    """ This class handles screen inputs. It assumes that only one devices is connected via ADB """
    def __init__(self):
        self.adb_path = r'C:\Fall 2024\Adv SE\Final Project\platform-tools\adb.exe'

    def touch(self, x: int, y: int):
        """
        A single tap anywhere on the screen
        """
        subprocess.run([self.adb_path, "shell", "input", "tap", str(x), str(y)])

    def swipe(self, x_start: int, y_start: int, x_end: int, y_end: int, time: int):
        """
        Swipe from the starting coordinates to the ending ones, over a given time (in ms)
        """
        subprocess.run([self.adb_path, "shell", "input", "swipe", str(x_start), str(y_start), str(x_end), str(y_end), str(time)])

    def text(self, text: str):
        """
        Enter a string of text into a text field (must already be selected)
        """
        subprocess.run([self.adb_path, "shell", "input", "text", text])

    def key(self, keycode: int):
        """
        Enter a keypress
        """
        # 3 -> Home Button
        # 4 -> Back Button
        subprocess.run([self.adb_path, "shell", "input", "keyevent", keycode])

    def dump_ui_hierarchy(self, path: str = "./"):
        """
        Get an XML readout of the current elements on the screen and download it to the given path
        """
        subprocess.run([self.adb_path, "shell", "uiautomator", "dump"])
        subprocess.run([self.adb_path, "pull", "//sdcard//window_dump.xml", path])
        
