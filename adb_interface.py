from dataclasses import dataclass
import subprocess
import logging
import os
from typing import Optional, Tuple, Union
from enum import IntEnum

logger = logging.getLogger(__name__)
logger.propagate = False
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class AndroidKeyCode(IntEnum):
    """Standard Android key codes for common actions"""
    HOME = 3
    BACK = 4
    MENU = 82
    POWER = 26
    VOLUME_UP = 24
    VOLUME_DOWN = 25


@dataclass
class Coordinates:
    """Represents x,y coordinates for touch and swipe actions"""
    x: int
    y: int

    def validate(self) -> None:
        """Validate coordinate values are non-negative"""
        if self.x < 0 or self.y < 0:
            raise ValueError(f"Coordinates must be non-negative. Got x={self.x}, y={self.y}")


class ADBError(Exception):
    """Custom exception for ADB-related errors"""
    pass


class TouchInterface:
    """
    Handles screen inputs for Android devices via ADB.

    This class provides methods for interacting with Android devices through ADB,
    including touch events, swipe gestures, text input, and UI hierarchy inspection.

    Attributes:
        adb_path (str): Path to the ADB executable
        device_id (Optional[str]): Specific device identifier for multi-device setups
    """

    def __init__(self, device_id: Optional[str] = None):
        """
        Initialize the TouchInterface with optional device targeting.

        Args:
            device_id: Optional device serial number for targeting a specific device

        Raises:
            FileNotFoundError: If ADB executable is not found
            ADBError: If no devices are connected or multiple devices without specified ID
        """
        self.device_id = device_id
        self.adb_path = self._get_adb_path()
        self._verify_device_connection()

    def _get_adb_path(self) -> str:
        """
        Locate the ADB executable path.

        Returns:
            str: Path to ADB executable

        Raises:
            FileNotFoundError: If ADB executable cannot be found
        """
        android_home = os.environ.get('ANDROID_HOME')
        if not android_home:
            raise FileNotFoundError("ANDROID_HOME environment variable not set")

        adb_path = os.path.join(android_home, "platform-tools", "adb.exe")
        if not os.path.exists(adb_path):
            raise FileNotFoundError(f"ADB executable not found at: {adb_path}")

        return adb_path

    def _verify_device_connection(self) -> None:
        """
        Verify ADB device connection status.

        Raises:
            ADBError: If no devices are connected or multiple devices without specified ID
        """
        devices = self._run_adb_command(['devices'])
        device_lines = devices.split('\n')[1:]  # Skip first line (header)
        connected_devices = [line.split('\t')[0] for line in device_lines if line.strip()]

        if not connected_devices:
            raise ADBError("No devices connected")

        if len(connected_devices) > 1 and not self.device_id:
            raise ADBError("Multiple devices connected. Please specify device_id")

        if self.device_id and self.device_id not in connected_devices:
            raise ADBError(f"Specified device {self.device_id} not found")

    def _run_adb_command(self, command: list) -> str:
        """
        Execute an ADB command and return its output.

        Args:
            command: List of command components

        Returns:
            str: Command output

        Raises:
            ADBError: If command execution fails
        """
        if self.device_id:
            command = [self.adb_path, '-s', self.device_id] + command
        else:
            command = [self.adb_path] + command

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"ADB command failed: {e.stderr}")
            raise ADBError(f"ADB command failed: {e.stderr}")

    def touch(self, coordinates: Union[Coordinates, Tuple[int, int]]) -> None:
        """
        Perform a single tap at specified coordinates.

        Args:
            coordinates: Either a Coordinates object or tuple of (x, y) coordinates
        """
        if isinstance(coordinates, tuple):
            coordinates = Coordinates(*coordinates)

        coordinates.validate()
        logger.debug(f"Touching screen at coordinates ({coordinates.x}, {coordinates.y})")
        self._run_adb_command(['shell', 'input', 'tap', str(coordinates.x), str(coordinates.y)])

    def swipe(
            self,
            start: Union[Coordinates, Tuple[int, int]],
            end: Union[Coordinates, Tuple[int, int]],
            duration_ms: int = 300
    ) -> None:
        """
        Perform a swipe gesture from start to end coordinates.

        Args:
            start: Starting coordinates
            end: Ending coordinates
            duration_ms: Duration of swipe in milliseconds
        """
        if isinstance(start, tuple):
            start = Coordinates(*start)
        if isinstance(end, tuple):
            end = Coordinates(*end)

        start.validate()
        end.validate()

        if duration_ms < 0:
            raise ValueError("Duration must be non-negative")

        logger.debug(f"Swiping from ({start.x}, {start.y}) to ({end.x}, {end.y})")
        self._run_adb_command([
            'shell', 'input', 'swipe',
            str(start.x), str(start.y),
            str(end.x), str(end.y),
            str(duration_ms)
        ])

    def input_text(self, text: str) -> None:
        """
        Enter text into the focused field.

        Args:
            text: Text to input
        """
        logger.debug(f"Inputting text: {text}")
        self._run_adb_command(['shell', 'input', 'text', text])

    def press_key(self, keycode: Union[AndroidKeyCode, int]) -> None:
        """
        Simulate a keypress event.

        Args:
            keycode: Either an AndroidKeyCode enum value or integer keycode
        """
        keycode_value = int(keycode)
        logger.debug(f"Pressing key with keycode: {keycode_value}")
        self._run_adb_command(['shell', 'input', 'keyevent', str(keycode_value)])

    def dump_ui_hierarchy(self, output_path: str = "./") -> str:
        """
        Capture and save the current UI hierarchy as XML.

        Args:
            output_path: Directory to save the UI hierarchy XML

        Returns:
            str: Path to the saved XML file
        """
        logger.debug("Dumping UI hierarchy")
        self._run_adb_command(['shell', 'uiautomator', 'dump'])

        output_file = os.path.join(output_path, "window_dump.xml")
        self._run_adb_command(['pull', '/sdcard/window_dump.xml', output_file])

        return output_file