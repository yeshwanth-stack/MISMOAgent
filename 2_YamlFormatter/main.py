#!/usr/bin/env python3
"""
YAML Formatter Agent - Entry Point
Transforms raw YAML into Order Management standard format
"""

import sys
import os
from formatter import format_yaml_file


def main():
    """Main entry point"""
    
    # Get arguments
    if len(sys.argv) < 2:
        print("Usage: python main.py <input_yaml> [output_yaml]")
        print("\nExample:")
        print("  python main.py raw_schema.yaml formatted_schema.yaml")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "formatted_schema.yaml"
    
    # Validate input file exists
    if not os.path.exists(input_file):
        print(f"✗ Error: Input file not found: {input_file}")
        sys.exit(1)
    
    print(f"✓ Loaded YAML schema from: {input_file}")
    
    # Format YAML
    success = format_yaml_file(input_file, output_file)
    
    if success:
        print(f"\nSuccessfully formatted YAML schema!")
        print(f"Output file: {output_file}")
        sys.exit(0)
    else:
        print("\nFailed to format YAML schema!")
        sys.exit(1)


if __name__ == "__main__":
    main()
