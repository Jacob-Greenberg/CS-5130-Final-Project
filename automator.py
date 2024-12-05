import os
import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
from pathlib import Path
import yaml
from ollama import Client, ChatResponse
from adb_interface import TouchInterface, Coordinates, AndroidKeyCode, ADBError


def setup_logging(level=logging.INFO):
    """
    Configure logging for the application with custom handlers and formatters.
    Focuses logging on our application modules while suppressing external logs.

    Args:
        level: The logging level to use (default: logging.INFO)
    """
    logging.getLogger().setLevel(logging.WARNING)

    app_logger = logging.getLogger('automator')
    app_logger.setLevel(level)
    app_logger.propagate = False

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
        )
    )
    app_logger.addHandler(handler)

    modules = ['adb_interface', 'automator']
    for module in modules:
        module_logger = logging.getLogger(module)
        module_logger.setLevel(level)
        module_logger.propagate = False
        module_logger.addHandler(handler)

    return app_logger


logger = setup_logging()

class CommandType(Enum):
    """Supported automation command types"""
    TOUCH = "touch"
    SWIPE = "swipe"
    TEXT = "text"
    KEY = "key"
    END = "end"
    ERROR = "error"


@dataclass
class AutomatorConfig:
    """Configuration settings for the Automator"""
    prompt_file: str
    llm_model: str
    ollama_host: str
    device_id: Optional[str] = None

    @classmethod
    def from_yaml(cls, config_path: str) -> 'AutomatorConfig':
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return cls(**config)


class AutomationCommand:
    """Represents a parsed automation command with validation"""

    def __init__(self, command_json: Dict):
        self.raw_command = command_json.get('command', '')
        self.parse_command()

    def parse_command(self) -> None:
        """Parse the raw command string into components"""
        parts = self.raw_command.split()
        if not parts:
            raise ValueError("Empty command received")

        self.command_type = CommandType(parts[0])
        self.args = parts[1:]

    def validate(self) -> None:
        """Validate command arguments"""
        if self.command_type in (CommandType.END, CommandType.ERROR):
            return

        if self.command_type == CommandType.TOUCH:
            if len(self.args) != 2:
                raise ValueError("Touch command requires X and Y coordinates")
            x, y = map(int, self.args)
            Coordinates(x, y).validate()

        elif self.command_type == CommandType.SWIPE:
            if len(self.args) != 5:
                raise ValueError("Swipe command requires start X,Y, end X,Y, and duration")
            x1, y1, x2, y2, duration = map(int, self.args)
            Coordinates(x1, y1).validate()
            Coordinates(x2, y2).validate()
            if duration < 0:
                raise ValueError("Swipe duration must be non-negative")

        elif self.command_type == CommandType.KEY:
            if len(self.args) != 1:
                raise ValueError("Key command requires exactly one keycode")
            try:
                int(self.args[0])
            except ValueError:
                raise ValueError("Invalid keycode")


class Automator:
    """
    Manages automated UI testing through LLM-guided interactions.

    This class coordinates between the TouchInterface for device control and
    an LLM for decision-making based on UI state analysis.
    """

    def __init__(self, config: AutomatorConfig):
        """
        Initialize the Automator with configuration settings.

        Args:
            config: AutomatorConfig object containing settings
        """
        self.config = config
        self.touch_interface = TouchInterface(device_id=config.device_id)
        self.llm_client = Client(
            host=config.ollama_host,
            timeout=300
        )
        self.messages: List[Dict] = []
        self.system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load the system prompt from file"""
        try:
            with open(self.config.prompt_file, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {self.config.prompt_file}")

    def get_ui_hierarchy(self) -> str:
        """Capture current UI hierarchy"""
        try:
            self.touch_interface.dump_ui_hierarchy()
            with open('window_dump.xml', 'r') as f:
                return f.read()
        except (ADBError, FileNotFoundError) as e:
            logger.error(f"Failed to get UI hierarchy: {e}")
            raise

    def query_llm(self, ui_hierarchy: str, user_prompt: str) -> AutomationCommand:
        """
        Query the LLM for next action based on UI state.

        Args:
            ui_hierarchy: Current UI hierarchy XML
            user_prompt: User's test condition

        Returns:
            AutomationCommand object representing next action
        """
        prompt = f"{self.system_prompt}{user_prompt}\n###END TESTER PROMPT###"

        try:
            response: ChatResponse = self.llm_client.chat(
                model=self.config.llm_model,
                messages=self.messages + [
                    {'role': 'user', 'content': ui_hierarchy},
                    {'role': 'user', 'content': prompt}
                ]
            )

            content = response['message']['content'].replace("<|eom_id|>", "")
            command_json = json.loads(content)
            logger.info(f"Response from LLM: {content}")

            self.messages.extend([
                {'role': 'assistant', 'content': content},
                {'role': 'user', 'content': ui_hierarchy}
            ])

            return AutomationCommand(command_json)

        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            raise

    def execute_command(self, command: AutomationCommand) -> None:
        """
        Execute the given automation command.

        Args:
            command: AutomationCommand to execute
        """
        try:
            command.validate()

            if command.command_type == CommandType.TOUCH:
                x, y = map(int, command.args)
                self.touch_interface.touch(Coordinates(x, y))

            elif command.command_type == CommandType.SWIPE:
                x1, y1, x2, y2, duration = map(int, command.args)
                self.touch_interface.swipe(
                    Coordinates(x1, y1),
                    Coordinates(x2, y2),
                    duration
                )

            elif command.command_type == CommandType.TEXT:
                self.touch_interface.input_text(" ".join(command.args))

            elif command.command_type == CommandType.KEY:
                self.touch_interface.press_key(int(command.args[0]))

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise


def main():
    """Main entry point for the automation script"""
    try:
        logger.info("Starting automation process")
        # Load configuration
        config = AutomatorConfig.from_yaml('config.yaml')
        automator = Automator(config)

        # Get test condition from user
        user_prompt = input("Enter the condition you would like to be tested: ")

        while True:
            logger.debug("Processing next automation cycle")
            # Get current UI state
            ui_hierarchy = automator.get_ui_hierarchy()

            # Get next command from LLM
            command = automator.query_llm(ui_hierarchy, user_prompt)

            # Check for end conditions
            if command.command_type in (CommandType.END, CommandType.ERROR):
                logger.info(f"Automation ended with status: {command.command_type}")
                break

            # Execute command
            automator.execute_command(command)
    except KeyboardInterrupt:
        logger.info("Automation stopped by user")
    except Exception as e:
        logger.error(f"Automation failed: {e}")
        raise
    finally:
        logger.info("Cleaning up resources...")

if __name__ == "__main__":
    main()