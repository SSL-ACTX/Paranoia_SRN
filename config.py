import json

def load_config(filename="paranoia_config.json"):
    """Loads configuration from a JSON file."""
    with open(filename, "r") as f:
        return json.load(f)

config = load_config()
