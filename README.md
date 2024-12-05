# Android UI Automation Framework

A sophisticated framework for automated Android UI testing using Large Language Models (LLMs) to drive dynamic interaction decisions. This framework combines the power of ADB (Android Debug Bridge) for device control with LLM-based decision making to create intelligent, adaptive UI testing scenarios.

## Overview

This framework enables automated UI testing by:
1. Capturing the current UI state of an Android device
2. Using an LLM to analyze the UI and determine appropriate actions
3. Executing those actions through ADB commands
4. Repeating this cycle until test conditions are met

The system is designed to be modular, extensible, and robust, with comprehensive error handling and logging capabilities.

## Project Structure

```
android-ui-automation/
├── adb_interface.py     # Android device interaction layer
├── automator.py         # Main automation orchestration
├── config.yaml          # Configuration settings
├── prompt.txt          # System prompt for LLM
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Core Components

- **adb_interface.py**: Handles all direct device interactions through ADB, including:
  - Touch and swipe gestures
  - Text input
  - Key events
  - UI hierarchy capture
  
- **automator.py**: Orchestrates the automation process by:
  - Managing the testing lifecycle
  - Communicating with the LLM
  - Processing commands
  - Handling errors and logging

## Prerequisites

- Python 3.8 or higher
- Android SDK Platform Tools (for ADB)
- Connected Android device or emulator
- Ollama running locally with appropriate models installed

## Required Environment Variables

- `ANDROID_HOME`: Path to Android SDK installation

## Dependencies

Primary Python packages:
```
ollama==0.1.0
pyyaml==6.0.1
typing-extensions>=4.0.0
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Jacob-Greenberg/CS-5130-Final-Project.git android-ui-automation
cd android-ui-automation
```

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Create configuration file (config.yaml):
```yaml
prompt_file: "prompt.txt"
llm_model: "llama3.2:3b"
ollama_host: "127.0.0.1:11434"
device_id: null  # Optional, for specific device targeting
```

4. Ensure ADB is properly set up:
- Add Android SDK platform-tools to your PATH
- Set ANDROID_HOME environment variable
- Enable USB debugging on your Android device

## Usage

1. Connect your Android device via USB or start an emulator

2. Verify device connection:
```bash
adb devices
```

3. Run the automation script:
```bash
python automator.py
```

4. Enter your test condition when prompted

## Configuration

The `config.yaml` file supports the following settings:

- `prompt_file`: Path to the LLM system prompt file
- `llm_model`: Ollama model to use for decision making
- `ollama_host`: Ollama server address
- `device_id`: (Optional) Specific device identifier for multi-device setups

## Logging

The framework implements a hierarchical logging system:
- Application-specific logs are captured at INFO level by default
- External library logs are suppressed to WARNING level
- Log format includes timestamps, module names, and log levels
- Logs can be adjusted using the `setup_logging()` function in automator.py

## Error Handling

The framework implements comprehensive error handling for:
- ADB communication issues
- Device connection problems
- Invalid commands or coordinates
- LLM communication errors
- Configuration issues

## Key Classes

### TouchInterface
Handles direct device interaction through ADB commands:
```python
touch_interface = TouchInterface(device_id="optional_device_id")
touch_interface.touch(Coordinates(x=100, y=200))
touch_interface.swipe(
    start=Coordinates(100, 200),
    end=Coordinates(300, 400),
    duration_ms=300
)
```

### Automator
Manages the automation lifecycle:
```python
config = AutomatorConfig.from_yaml('config.yaml')
automator = Automator(config)
automator.execute_command(command)
```

## Contributing

We welcome contributions! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Best Practices

When using this framework:
- Keep the system prompt focused and specific
- Use appropriate logging levels for different environments
- Implement proper error handling in custom commands
- Test commands thoroughly before automation
- Monitor device state during long-running tests


## Support

For issues, questions, or contributions, please:
1. Check existing issues on GitHub
2. Create a new issue if needed
3. Include relevant logs and configuration details

## Future Improvements

Planned enhancements include:
- Unit test suite
- Command retry mechanisms
- Compound command support
- Test scenario management
- Performance metrics collection
- Enhanced logging options

## Acknowledgments

This project uses several open-source components and tools:
- Android Debug Bridge (ADB)
- Ollama
- Gemini
- Python standard library