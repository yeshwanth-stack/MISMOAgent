"""
MISMO JSON to YAML Converter - Main Entry Point
Handles file input/output operations.
"""

import json
import sys
from pathlib import Path
from converter import convert_json_to_yaml


def main():
    """Main function to handle file conversion."""
    
    # Get file paths
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "input.json"
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "output.yaml"
    
    # Read input JSON
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            json_content = f.read()
        print(f"✓ Loaded JSON from: {input_file}")
    except FileNotFoundError:
        print(f"✗ Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except IOError as e:
        print(f"✗ Error reading file: {e}")
        sys.exit(1)
    
    # Convert
    try:
        print("Converting JSON to YAML schema...")
        yaml_content = convert_json_to_yaml(json_content)
        print("✓ Conversion successful")
    except ValueError as e:
        print(f"✗ Conversion error: {e}")
        sys.exit(1)
    
    # Write output YAML
    try:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        print(f"✓ Saved YAML schema to: {output_file}")
    except IOError as e:
        print(f"✗ Error writing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
