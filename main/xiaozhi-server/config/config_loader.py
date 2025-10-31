import os
import yaml
from collections.abc import Mapping
from pydantic import ValidationError
from config.manage_api_client import init_service, get_server_config
from config.models import Config


def get_project_dir():
    """Get the root directory of the project."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"


def read_config(config_path):
    """
    Read and parse YAML configuration file, optionally validate and return Config object.
    
    Args:
        config_path: Path to the YAML config file (if provided, will read from file)
        
    Returns:
        If validate=True: Config object
        If validate=False: Raw dictionary from YAML file or provided dict
        
    Raises:
        ValidationError: If validate=True and configuration fails validation
        FileNotFoundError: If config_path is provided but file is not found
        ValueError: If neither config_path nor config_dict is provided
    """
    # If config_dict is provided, use it; otherwise read from file
    with open(config_path, "r", encoding="utf-8") as file:
        config_data = yaml.safe_load(file)
    try:
        config = Config(**config_data)
    except ValidationError as e:
        raise ValueError(f"Configuration validation error in {config_path}: {e}")
    return config


def load_config() -> Config:
    """
    Load and validate configuration file with Pydantic models.
    
    Returns:
        Config: Validated and strongly-typed configuration object
        
    Raises:
        ValidationError: If configuration fails validation
        FileNotFoundError: If config files are not found
    """
    default_config_path = get_project_dir() + "config.yaml"
    # local_config_path = get_project_dir() + "data/.config.yaml"

    # Load default configuration
    default_config = read_config(default_config_path)


    return default_config