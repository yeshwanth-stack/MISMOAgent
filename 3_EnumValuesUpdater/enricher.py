"""
YAML Enum Enrichment
Enriches YAML schema files by adding enum values from definitions files.
Supports any freeform input format and auto-generates OtherDescription fields.
"""

import re
import yaml
from typing import Dict, List, Tuple, Set, Optional


class EnumDefinition:
    """Represents a single enum definition entry."""
    
    def __init__(self, jpath: str, field_name: str, values: List[str]):
        self.jpath = jpath
        self.field_name = field_name
        self.values = values
        self.has_other = "Other" in values
    
    def __repr__(self):
        return f"EnumDef({self.field_name} @ {self.jpath}: {self.values})"


class YamlEnumEnricher:
    """Enriches YAML schema with enum values from definitions file."""
    
    def __init__(self):
        self.enum_definitions: List[EnumDefinition] = []
    
    def parse_enum_definitions(self, text: str) -> List[EnumDefinition]:
        """
        Parse freeform enum definitions text in ANY format.
        Returns list of EnumDefinition objects.
        """
        definitions = []
        
        # Split by blank lines to identify blocks
        blocks = re.split(r'\n\s*\n', text.strip())
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            parsed = self._parse_block(block)
            if parsed:
                definitions.append(parsed)
        
        return definitions
    
    def _parse_block(self, block: str) -> Optional[EnumDefinition]:
        """Parse a single block and return EnumDefinition or None."""
        
        lines = block.split('\n')
        jpath = None
        field_name = None
        values = []
        
        # Extract jpath from first line or any line starting with $
        jpath_line_idx = None
        for idx, line in enumerate(lines):
            line_stripped = line.strip()
            match = re.search(r'(\$\.[^\s:,|]*)', line_stripped)
            if match:
                jpath = match.group(1)
                jpath_line_idx = idx
                break
        
        if not jpath:
            return None
        
        # Extract field name from jpath (last segment, strip array indices)
        field_name = self._extract_field_name(jpath)
        
        # Extract values from all lines
        for idx, line in enumerate(lines):
            line_stripped = line.strip()
            
            # For the jpath line itself, extract values that come after the jpath
            if idx == jpath_line_idx:
                # If there's content after the jpath (e.g., "$.path: value, value, value"),extract it
                # Find the part after the colon or pipe or other separator
                after_jpath = re.sub(r'(\$\.[^\s:,|]*)\s*[:=|]?\s*', '', line_stripped)
                if after_jpath:
                    line_values = self._extract_values_from_line(after_jpath)
                    values.extend(line_values)
                continue
            
            # Skip other jpath-only lines or label lines
            if line_stripped.startswith('$') or re.match(r'^(path|values|Field|jpath|type|enum)\s*[:=]', line_stripped, re.IGNORECASE):
                continue
            
            # Extract values from this line
            line_values = self._extract_values_from_line(line_stripped)
            values.extend(line_values)
        
        if not values:
            return None
        
        return EnumDefinition(jpath, field_name, values)
    
    def _extract_field_name(self, jpath: str) -> str:
        """Extract field name from jpath, stripping array indices."""
        # Remove array indices: $.path[0].field[1].name -> $.path.field.name
        normalized = re.sub(r'\[\d+\]', '', jpath)
        # Get last segment after final dot
        parts = normalized.rstrip('.').split('.')
        return parts[-1] if parts else ''
    
    def _extract_values_from_line(self, line: str) -> List[str]:
        """Extract enum values from a line, handling various formats."""
        
        # Skip empty lines and labels
        if not line or re.match(r'^(path|values|Field|jpath|type|enum|$)', line, re.IGNORECASE):
            return []
        
        values = []
        
        # Try different delimiters: comma, pipe, tab, forward slash, newline
        # First, try to split by common delimiters
        if ',' in line:
            parts = line.split(',')
        elif '|' in line:
            parts = line.split('|')
        elif '\t' in line:
            parts = line.split('\t')
        elif '/' in line:
            parts = line.split('/')
        else:
            # Single value or bullet list item
            parts = [line]
        
        for part in parts:
            part = part.strip()
            
            # Skip empty, labels, and jpaths
            if not part or part.startswith('$'):
                continue
            if re.match(r'^(path|values|Field|jpath|type|enum)\s*[:=]', part, re.IGNORECASE):
                continue
            
            # Remove leading bullets, numbers, dots
            part = re.sub(r'^[-*•]\s*', '', part)  # bullets
            part = re.sub(r'^\d+\.\s*', '', part)  # numbered
            part = re.sub(r'^\.+\s*', '', part)    # dots
            
            part = part.strip()
            
            # Should be a PascalCase or UPPERCASE word
            if part and re.match(r'^[A-Z][a-zA-Z0-9]*$', part):
                values.append(part)
        
        return values
    
    def enrich_yaml(self, yaml_content: str, definitions: List[EnumDefinition]) -> str:
        """
        Enrich YAML schema with enum values and OtherDescription fields.
        Returns enriched YAML as string with exact indentation formatting.
        """
        lines = yaml_content.split('\n')
        
        # First pass: identify all fields that need enrichment
        enrichments = []  # List of (type_line_idx, field_name, field_jpath, matched_def)
        
        for i in range(len(lines)):
            line = lines[i]
            
            # Check if this line has 'type: string'
            if re.search(r'type:\s*string\s*$', line):
                type_indent_match = re.match(r'^(\s*)', line)
                type_indent = type_indent_match.group(1) if type_indent_match else ''
                field_indent = len(type_indent)
                
                # Find field name (look back)
                field_name = None
                for k in range(i - 1, max(0, i - 5), -1):
                    if lines[k].strip():
                        field_match = re.match(r'^(\s*)(\w+):\s*$', lines[k])
                        if field_match:
                            field_indent_check = len(field_match.group(1))
                            if field_indent_check < field_indent:
                                field_name = field_match.group(2)
                                break
                
                # Find jpath (look ahead)
                field_jpath = None
                jpath_line_idx = None
                for j in range(i + 1, min(i + 10, len(lines))):
                    if 'jpath:' in lines[j]:
                        jpath_match = re.search(r'jpath:\s*(.+?)$', lines[j])
                        if jpath_match:
                            field_jpath = jpath_match.group(1).strip()
                            jpath_line_idx = j
                        break
                
                # Check for matching definition
                if field_name and field_jpath:
                    matched_def = self._find_matching_definition(field_name, field_jpath, definitions)
                    if matched_def:
                        enrichments.append({
                            'type_line_idx': i,
                            'jpath_line_idx': jpath_line_idx,
                            'field_name': field_name,
                            'field_jpath': field_jpath,
                            'matched_def': matched_def,
                            'type_indent': type_indent,
                            'field_indent_level': field_indent - 2  # Field name level
                        })
        
        # Second pass: apply enrichments in reverse order (to maintain line indices)
        for enrichment in reversed(enrichments):
            idx = enrichment['type_line_idx']
            type_indent = enrichment['type_indent']
            enum_value_indent = type_indent + '  '
            
            # Insert enum lines after type:
            enum_lines = [f"{type_indent}enum:"]
            for value in enrichment['matched_def'].values:
                enum_lines.append(f"{enum_value_indent}- {value}")
            
            # Insert at position after type line
            for enum_line in reversed(enum_lines):
                lines.insert(idx + 1, enum_line)
            
            # If "Other" is present, add OtherDescription field after jpath
            if enrichment['matched_def'].has_other:
                jpath_idx = enrichment['jpath_line_idx']
                # Adjust jpath index due to enum insertions
                jpath_idx += len(enum_lines)
                
                other_name = f"{enrichment['field_name']}OtherDescription"
                other_jpath = self._derive_other_description_jpath(enrichment['field_jpath'])
                
                field_level_indent = ' ' * enrichment['field_indent_level']
                type_level_indent = ' ' * (enrichment['field_indent_level'] + 2)
                
                # Insert OtherDescription field after jpath line
                lines.insert(jpath_idx + 1, f"{type_level_indent}jpath: {other_jpath}")
                lines.insert(jpath_idx + 1, f"{type_level_indent}type: string")
                lines.insert(jpath_idx + 1, f"{field_level_indent}{other_name}:")
        
        return '\n'.join(lines)
    
    def _enrich_dict(self, obj: dict, definitions: List[EnumDefinition], parent_path: str, 
                     added_other_descriptions: Set[str]):
        """Recursively walk YAML dict and enrich matching fields."""
        
        keys_to_add = {}  # New fields to add after processing
        
        for key in list(obj.keys()):
            value = obj[key]
            
            # Build current path
            current_path = f"{parent_path}.{key}" if parent_path else f"$.{key}"
            
            if isinstance(value, dict):
                # Check if this is a field definition (has 'type' and 'jpath')
                if 'type' in value and 'jpath' in value:
                    # Try to match against enum definitions
                    field_type = value.get('type')
                    field_jpath = value.get('jpath')
                    
                    if field_type == 'string':
                        matched_def = self._find_matching_definition(key, field_jpath, definitions)
                        
                        if matched_def:
                            # Add enum values
                            value['enum'] = matched_def.values
                            
                            # Check if we need to add OtherDescription
                            if matched_def.has_other:
                                other_desc_key = f"{key}OtherDescription"
                                
                                # Check if it already exists
                                if other_desc_key not in obj:
                                    other_desc_jpath = self._derive_other_description_jpath(field_jpath)
                                    keys_to_add[other_desc_key] = {
                                        'type': 'string',
                                        'jpath': other_desc_jpath
                                    }
                                    added_other_descriptions.add(other_desc_key)
                
                # Recurse into nested dicts (for nested objects)
                if 'properties' in value and isinstance(value['properties'], dict):
                    self._enrich_dict(value['properties'], definitions, current_path, added_other_descriptions)
                else:
                    self._enrich_dict(value, definitions, current_path, added_other_descriptions)
            
            elif isinstance(value, list):
                # Handle lists of items (array items in YAML)
                for item in value:
                    if isinstance(item, dict):
                        self._enrich_dict(item, definitions, current_path, added_other_descriptions)
        
        # Add new OtherDescription fields after processing
        for key, field_def in keys_to_add.items():
            obj[key] = field_def
    
    def _find_matching_definition(self, field_name: str, field_jpath: str, 
                                   definitions: List[EnumDefinition]) -> Optional[EnumDefinition]:
        """
        Find matching enum definition for a field using both field name and jpath.
        Implements fallback strategy.
        """
        
        candidates = []
        
        # Strategy 1: Exact match on both name and jpath
        for defn in definitions:
            if defn.field_name == field_name:
                # Check if jpaths match (with array index stripping)
                if self._jpaths_match(field_jpath, defn.jpath):
                    return defn
                candidates.append(defn)
        
        # Strategy 2: Match by field name only (if exactly one match)
        if len(candidates) == 1:
            return candidates[0]
        
        # Strategy 3: Match just by name (fallback for ambiguous cases)
        name_matches = [d for d in definitions if d.field_name == field_name]
        if len(name_matches) == 1:
            return name_matches[0]
        
        return None
    
    def _jpaths_match(self, yaml_jpath: str, defn_jpath: str) -> bool:
        """
        Check if two jpaths match, handling relative vs absolute paths and array indices.
        """
        
        # Normalize both paths (strip array indices and leading $)
        yaml_normalized = re.sub(r'\[\d+\]', '', yaml_jpath)
        defn_normalized = re.sub(r'\[\d+\]', '', defn_jpath)
        
        # Remove leading $ and . if present
        yaml_normalized = yaml_normalized.lstrip('$.').strip()
        defn_normalized = defn_normalized.lstrip('$.').strip()
        
        # Direct match (after normalization)
        if yaml_normalized == defn_normalized:
            return True
        
        # Try matching relative path
        # Check if YAML path ends with definition path (YAML is usually longer due to nesting)
        yaml_parts = yaml_normalized.split('.')
        defn_parts = defn_normalized.split('.')
        
        if len(yaml_parts) >= len(defn_parts):
            # Check if yaml path ends with defn path
            if yaml_parts[-len(defn_parts):] == defn_parts:
                return True
        
        return False
    
    def _derive_other_description_jpath(self, original_jpath: str) -> str:
        """
        Derive OtherDescription jpath from original jpath.
        Replace last segment with {segment}OtherDescription.
        """
        
        parts = original_jpath.rstrip('.').split('.')
        if not parts:
            return original_jpath
        
        last_segment = parts[-1]
        new_segment = f"{last_segment}OtherDescription"
        
        parts[-1] = new_segment
        return '.'.join(parts)


def enrich_yaml_file(yaml_file: str, enum_defs_file: str, output_file: str):
    """
    Main function to enrich YAML file with enum definitions.
    """
    
    # Read files
    with open(yaml_file, 'r', encoding='utf-8') as f:
        yaml_content = f.read()
    
    with open(enum_defs_file, 'r', encoding='utf-8') as f:
        enum_defs_text = f.read()
    
    # Create enricher and process
    enricher = YamlEnumEnricher()
    definitions = enricher.parse_enum_definitions(enum_defs_text)
    enriched_yaml = enricher.enrich_yaml(yaml_content, definitions)
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(enriched_yaml)
    
    print(f"✓ Loaded YAML schema from: {yaml_file}")
    print(f"✓ Loaded {len(definitions)} enum definitions from: {enum_defs_file}")
    print(f"Enriching YAML schema with enum values...")
    print(f"✓ Enrichment successful")
    print(f"✓ Enriched YAML written to: {output_file}")
