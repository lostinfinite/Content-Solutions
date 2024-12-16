# Content Solutions Bot
>
> [!IMPORTANT]\
> Remember to read the License in the License file. Additionally please read the ContentLTD [ToS](https://contentltd.net) and [Privacy Policy](https://contentltd.net/privacy)
>
> 
## Overview
The **Content Solutions Bot** is a Python-based bot designed to help with server moderation, management, and utility functions. This bot includes features for banning users, quarantining, mass bans, and more. It operates using **beta.py** as the main script, which can be automatically executed after installing all required packages.

## Table of Contents
- [Installation](#installation)
- [Running the Bot](#running-the-bot)
- [Configuration](#configuration)
- [Bot Structure](#bot-structure)
  - [beta.py](#betapy)
  - [utils.py](#utilspy)
  - [config.py](#configpy)
  - [main.py](#mainpy)
- [Bot Features](#bot-features)
- [License](#license)

## Installation

To get started, clone the repository and install the required dependencies. **main.py** will automatically handle the installation of required packages.

Once you've cloned the repository:

1. Navigate into the project folder.
2. Run `python main.py`, which will install all the necessary dependencies for the bot.

### Requirements
- Python 3.8+
- `discord.py`
- `requests` (for API calls)
- `dotenv` (to handle environment variables)

## Running the Bot

Once the dependencies are installed, run the bot using the following command:

1. Run `python beta.py` to start the bot.
2. The bot will initialize and begin listening for events and commands.

## Configuration

Configuration settings are stored in **config.py**, where you can adjust roles, channels, and other parameters related to your server. All sensitive data such as token, channel IDs, and user IDs are hidden in this repository for security reasons. Make sure to configure the necessary settings in **config.py** before running the bot.

### Important Files:
- **config.py**: Contains the configuration constants (role IDs, guild IDs, etc.).
- **beta.py**: The main script that initializes the bot and listens for events.
- **utils.py**: Includes utility functions for banning, logging actions, and other auxiliary tasks.

## Bot Structure

### `beta.py`
This file contains the main bot code. It initializes the bot, listens for commands, and manages various features such as:
- Banning users
- Mass banning
- Quarantining members
- Role assignments
- Logging actions

### `utils.py`
Utility functions to handle common tasks like banning users, assigning roles, logging actions, and making API calls. It also interacts with the bot instance defined in **beta.py**.

### `config.py`
Configuration file where constants and role mappings are stored. This allows you to adjust the bot's behavior for your specific server needs.

### `main.py`
This file is responsible for setting up the bot environment and ensuring that all dependencies are installed before **beta.py** is executed. It automatically installs packages listed in a `requirements.txt` or using `pip` commands.

## Bot Features

- **Ban Users**: Automatically ban users with a single command.
- **Mass Ban**: Mass ban multiple users at once.
- **Quarantine**: Put users into a quarantine role for review.
- **Logging**: Log all actions such as bans, quarantines, and role assignments.
- **Automated Installation**: **main.py** auto-installs all dependencies.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

> [!IMPORTANT]\
> All channel, user, and guild IDs have been removed from this repository for privacy and security reasons. Please make sure to configure these in your local **config.py** file.

> [!WARNING]\
> Token and link filtering files have been excluded from this repository for security purposes.

Made with ❤️ by ContentLTD
