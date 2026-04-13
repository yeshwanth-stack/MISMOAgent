#!/usr/bin/env python3
"""
YAML Enum Enrichment Agent - Main Entry Point
Enriches YAML schema files by adding enum values from definitions files.
"""

import sys
import os
from enricher import enrich_yaml_file


def main():
    """Main entry point."""
    
    if len(sys.argv) < 3:
        print("Usage: python main.py <yaml_schema_file> <enum_definitions_file> [output_file]")
        print()
        print("Arguments:")
        print("  yaml_schema_file       Path to YAML schema file to enrich")
        print("  enum_definitions_file  Path to enum definitions file (any format)")
        print("  output_file            Path to write enriched YAML (default: input_enriched.yaml)")
        print()
        print("Example:")
        print("  python main.py schema.yaml enum_definitions.txt schema_enriched.yaml")
        sys.exit(1)
    
    yaml_file = sys.argv[1]
    enum_defs_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else ""
    
    # Validate input files exist
    if not os.path.exists(yaml_file):
        print(f"Error: YAML schema file not found: {yaml_file}")
        sys.exit(1)
    
    if not os.path.exists(enum_defs_file):
        print(f"Error: Enum definitions file not found: {enum_defs_file}")
        sys.exit(1)
    
    # Determine output file
    if not output_file:
        base, ext = os.path.splitext(yaml_file)
        output_file = f"{base}_enriched{ext}"
    
    try:
        enrich_yaml_file(yaml_file, enum_defs_file, output_file)
        print()
        print(f"Successfully enriched YAML schema!")
        print(f"Output file: {output_file}")
    except Exception as e:
        print(f"Error during enrichment: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
