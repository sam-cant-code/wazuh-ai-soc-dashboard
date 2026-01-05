import yaml
import logging

CONFIG_PATH = "config.yaml"

def load_config(path=CONFIG_PATH):
    """Load configuration from a YAML file."""
    try:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        raise

def print_config(config):
    """Pretty print the configuration."""
    import pprint
    pprint.pprint(config)

def get_uvicorn_log_level(config):
    """Get the log level for Uvicorn from config."""
    # Default to 'info' if not specified
    return config.get("logging", {}).get("level", "info").lower()

def should_expose_errors(config):
    """
    Determine if detailed errors should be exposed.
    Returns True if we are in dev mode (reload=True) or explicit feature flag.
    """
    # Expose errors if auto-reload is on (typical for dev)
    return config.get("server", {}).get("reload", False)