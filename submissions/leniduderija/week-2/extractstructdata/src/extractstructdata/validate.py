import json
from pathlib import Path
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from .errors import SchemaValidationError

SCHEMA_PATH = Path(__file__).parent / "schema.json"

def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

SCHEMA = load_schema()

def validate_extraction(data):
    try:
        validate(instance=data, schema=SCHEMA)
        
    except ValidationError as e:
        raise SchemaValidationError(e.message) from e