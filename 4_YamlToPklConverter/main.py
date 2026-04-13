"""
YAML to PKL Converter - Main Entry Point
Handles file input/output operations.
"""

import sys
from pathlib import Path
from converter import YamlToPklConverter


def main():
    """Main function to handle file conversion."""
    
    # Get file paths
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "input.yaml"
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "output.pkl"
    
    product_name = sys.argv[3] if len(sys.argv) > 3 else ""
    
    # Read input YAML
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
        print(f"✓ Loaded YAML schema from: {input_file}")
    except FileNotFoundError:
        print(f"✗ Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except IOError as e:
        print(f"✗ Error reading file: {e}")
        sys.exit(1)
    
    # Convert
    try:
        print("Converting YAML schema to PKL format...")
        converter = YamlToPklConverter()
        pkl_content = converter.convert(yaml_content, product_name)
        print("✓ Conversion successful")
    except ValueError as e:
        print(f"✗ Conversion error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)
    
    # Write output PKL
    try:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pkl_content)
        print(f"✓ PKL file written to: {output_file}")
    except IOError as e:
        print(f"✗ Error writing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
