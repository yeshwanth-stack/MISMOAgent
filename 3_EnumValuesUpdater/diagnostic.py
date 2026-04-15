#!/usr/bin/env python3
"""
Diagnostic tool to identify which enum definitions are matched vs skipped.
"""

import sys
from enricher import YamlEnumEnricher
import yaml
import re


def main():
    """Run diagnostic."""
    
    # Read files
    with open('enum_definitions.txt', 'r', encoding='utf-8') as f:
        enum_defs_text = f.read()
    
    with open('sample_schema.yaml', 'r', encoding='utf-8') as f:
        yaml_content = f.read()
    
    # Parse enum definitions
    enricher = YamlEnumEnricher()
    definitions = enricher.parse_enum_definitions(enum_defs_text)
    
    print(f"Total enum definitions parsed: {len(definitions)}\n")
    
    # Parse YAML to find all string fields
    yaml_data = yaml.safe_load(yaml_content)
    
    # Collect all string fields from YAML
    yaml_fields = {}
    
    def extract_fields(obj, path=''):
        if isinstance(obj, dict):
            for key, val in obj.items():
                current_path = f"{path}.{key}" if path else f"$.{key}"
                
                if isinstance(val, dict):
                    if 'type' in val and val['type'] == 'string':
                        jpath = val.get('jpath', '')
                        yaml_fields[key] = (jpath, val)
                    
                    if 'properties' in val:
                        extract_fields(val['properties'], current_path)
                    elif 'items' in val and isinstance(val['items'], dict):
                        if 'properties' in val['items']:
                            extract_fields(val['items']['properties'], current_path)
    
    extract_fields(yaml_data.get('properties', {}))
    
    print(f"Total string fields in YAML: {len(yaml_fields)}\n")
    
    # Check matches
    matched = []
    skipped = []
    
    for yaml_field, (yaml_jpath, field_def) in yaml_fields.items():
        matched_def = enricher._find_matching_definition(yaml_field, yaml_jpath, definitions)
        
        if matched_def:
            matched.append({
                'field': yaml_field,
                'yaml_jpath': yaml_jpath,
                'enum_count': len(matched_def.values),
                'values': matched_def.values[:3],  # First 3 values
                'def_jpath': matched_def.jpath
            })
        else:
            skipped.append({
                'field': yaml_field,
                'jpath': yaml_jpath,
                'has_def': any(d.field_name == yaml_field for d in definitions)
            })
    
    print("=" * 80)
    print(f"✓ MATCHED FIELDS: {len(matched)}")
    print("=" * 80)
    for m in sorted(matched, key=lambda x: x['field']):
        print(f"\n{m['field']}:")
        print(f"  YAML jpath:    {m['yaml_jpath']}")
        print(f"  Def jpath:     {m['def_jpath']}")
        print(f"  Enum count:    {m['enum_count']}")
        print(f"  Sample values: {', '.join(m['values'][:3])}")
    
    print("\n" + "=" * 80)
    print(f"✗ SKIPPED FIELDS: {len(skipped)}")
    print("=" * 80)
    for s in sorted(skipped, key=lambda x: x['field']):
        def_status = "HAS definition" if s['has_def'] else "NO definition"
        print(f"\n{s['field']}: [{def_status}]")
        print(f"  YAML jpath: {s['jpath']}")
        
        if s['has_def']:
            # Find the definition
            for d in definitions:
                if d.field_name == s['field']:
                    print(f"  Def jpath:  {d.jpath}")
                    print(f"  Values:     {', '.join(d.values[:5])}")
                    break


if __name__ == "__main__":
    main()
