"""
YAML to PKL Schema Converter
Converts YAML schema definitions into PKL files for Xpanse Order Management platform.
"""

import yaml
from typing import Any, Dict, List, Optional, Mapping as MappingType
import re


class YamlToPklConverter:
    """Converts YAML schema to PKL format following exact specification."""
    
    def __init__(self):
        self.indent_level = 0
        self.indent_str = "  "
    
    def convert(self, yaml_content: str, product_name: str = "") -> str:
        """
        Convert YAML schema to PKL format.
        
        Args:
            yaml_content: The YAML schema as a string
            product_name: Product name for PRODUCT_NAME constant
            
        Returns:
            PKL file content as a string
        """
        yaml_data = yaml.safe_load(yaml_content)
        
        if not isinstance(yaml_data, dict) or 'properties' not in yaml_data:
            raise ValueError("YAML must be an object with 'properties' key at root level")
        
        pkl_content = self._build_pkl_file(yaml_data['properties'], product_name)
        return pkl_content
    
    def _build_pkl_file(self, properties: Dict[str, Any], product_name: str) -> str:
        """Build complete PKL file structure."""
        lines = []
        
        # Imports
        lines.append('import "@xpanse/std.pkl" as std')
        lines.append('import "@xpanse/common.pkl" as common')
        lines.append('import "@xpanse/test.pkl" as test')
        lines.append('')
        lines.append('local const PRODUCT_NAME = ""')
        lines.append('')
        
        # Config block
        lines.append('config = new std.ProductConfig {')
        lines.append(f'  name = PRODUCT_NAME')
        lines.append('  properties {')
        
        # Properties from YAML - skip payload wrapper
        self.indent_level = 2
        for key, val in properties.items():
            # Skip payload wrapper - output its children directly
            if key.lower() == 'payload' and isinstance(val, dict) and 'properties' in val:
                for sub_key, sub_val in val['properties'].items():
                    lines.extend(self._convert_top_level_property(sub_key, sub_val))
            else:
                lines.extend(self._convert_top_level_property(key, val))
        
        lines.append('  }')
        lines.append('}')
        lines.append('')
        
        # Test Suite
        lines.append('testSuite = new test.Suite {')
        lines.append('  valid {')
        lines.append('    minimal = (test.MINIMAL_PAYLOAD_TEMPLATE) {')
        self.indent_level = 3
        lines.extend(self._build_test_payload(properties, minimal=True))
        lines.append('    }')
        lines.append('    full = (test.FULL_PAYLOAD_TEMPLATE) {')
        self.indent_level = 3
        lines.extend(self._build_test_payload(properties, minimal=False))
        lines.append('    }')
        lines.append('  }')
        lines.append('}')
        
        return '\n'.join(lines)
    
    def _convert_top_level_property(self, key: str, value: Dict[str, Any]) -> List[str]:
        """Convert a top-level property from YAML."""
        lines = []
        
        # Check if it's a special type (loanDetails, orderDetails)
        if key in ['loanDetails', 'orderDetails']:
            common_type = 'common.' + ''.join(w.capitalize() for w in key.split('_'))
            lines.append(f'{self._indent()}{key} = new {common_type} {{')
            lines.append(f'{self._indent()}  properties {{')
            self.indent_level += 2
            
            if 'properties' in value:
                for sub_key, sub_val in value['properties'].items():
                    lines.extend(self._convert_property(sub_key, sub_val))
            
            self.indent_level -= 2
            lines.append(f'{self._indent()}  }}')
            lines.append(f'{self._indent()}}}')
        else:
            # Regular property
            lines.extend(self._convert_property(key, value))
        
        return lines
    
    def _convert_property(self, key: str, value: Dict[str, Any]) -> List[str]:
        """Convert a single property based on its type."""
        lines = []
        prop_type = value.get('type', 'string')
        label = self._generate_label(key)
        
        if prop_type == 'object':
            lines.append(f'{self._indent()}{key} = new std.ObjectProperty {{')
            lines.append(f'{self._indent()}  label = "{label}"')
            lines.append(f'{self._indent()}  required = false')
            lines.append(f'{self._indent()}  properties {{')
            self.indent_level += 2
            
            if 'properties' in value:
                for sub_key, sub_val in value['properties'].items():
                    lines.extend(self._convert_property(sub_key, sub_val))
            
            self.indent_level -= 2
            lines.append(f'{self._indent()}  }}')
            lines.append(f'{self._indent()}}}')
            
        elif prop_type == 'array':
            lines.append(f'{self._indent()}{key} = new std.ObjectArrayProperty {{')
            lines.append(f'{self._indent()}  label = "{label}"')
            lines.append(f'{self._indent()}  required = false')
            lines.append(f'{self._indent()}  items = new std.ObjectProperty {{')
            lines.append(f'{self._indent()}    properties {{')
            self.indent_level += 3
            
            if 'items' in value and 'properties' in value['items']:
                for item_key, item_val in value['items']['properties'].items():
                    lines.extend(self._convert_property(item_key, item_val))
            
            self.indent_level -= 3
            lines.append(f'{self._indent()}    }}')
            lines.append(f'{self._indent()}  }}')
            lines.append(f'{self._indent()}}}')
            
        elif prop_type == 'string':
            if 'enum' in value:
                lines.append(f'{self._indent()}{key} = new std.StringEnumProperty {{')
                lines.append(f'{self._indent()}  label = "{label}"')
                lines.append(f'{self._indent()}  required = false')
                lines.append(f'{self._indent()}  items = new Mapping {{')
                
                for enum_val in value['enum']:
                    readable = self._humanize_enum(enum_val)
                    lines.append(f'{self._indent()}    ["{enum_val}"] = "{readable}"')
                
                lines.append(f'{self._indent()}  }}')
                lines.append(f'{self._indent()}}}')
            else:
                lines.append(f'{self._indent()}{key} = new std.StringProperty {{')
                lines.append(f'{self._indent()}  label = "{label}"')
                lines.append(f'{self._indent()}  required = false')
                lines.append(f'{self._indent()}}}')
                
        elif prop_type == 'number':
            if self._should_use_integer(key):
                lines.append(f'{self._indent()}{key} = new std.IntegerProperty {{')
                lines.append(f'{self._indent()}  label = "{label}"')
                lines.append(f'{self._indent()}  required = false')
                lines.append(f'{self._indent()}}}')
            else:
                lines.append(f'{self._indent()}{key} = new std.DecimalProperty {{')
                lines.append(f'{self._indent()}  label = "{label}"')
                lines.append(f'{self._indent()}  required = false')
                lines.append(f'{self._indent()}  min = 0')
                lines.append(f'{self._indent()}}}')
                
        elif prop_type == 'boolean':
            lines.append(f'{self._indent()}{key} = new std.BooleanProperty {{')
            lines.append(f'{self._indent()}  label = "{label}"')
            lines.append(f'{self._indent()}  required = false')
            lines.append(f'{self._indent()}}}')
        
        return lines
    
    def _generate_label(self, field_name: str) -> str:
        """Convert camelCase/PascalCase to Title Case with spaces."""
        # Handle special cases
        if field_name.lower() == 'id':
            return 'ID'
        
        # Insert space before capitals
        spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', field_name)
        spaced = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', spaced)
        
        return spaced.title()
    
    def _humanize_enum(self, enum_val: Any) -> str:
        """Convert enum value to human-readable form."""
        # Convert non-string types to string
        if not isinstance(enum_val, str):
            return str(enum_val)
        
        # All-caps abbreviations stay as-is
        if enum_val.isupper() and len(enum_val) <= 4:
            return enum_val
        
        # Single word stays as-is
        if '_' not in enum_val and enum_val.isalnum():
            # Check if it's already Title Case or has mixed case
            if not enum_val[0].isupper():
                return enum_val  # lowercase, keep as-is
        
        # camelCase to Title Case with spaces
        spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', enum_val)
        spaced = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', spaced)
        
        return spaced.title() if spaced else enum_val
    
    def _should_use_integer(self, field_name: str) -> bool:
        """Check if field should use IntegerProperty instead of DecimalProperty."""
        keywords = ['count', 'sequencenumber', 'year', 'unitcount', 'creditscore']
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in keywords)
    
    def _indent(self) -> str:
        """Get current indentation."""
        return self.indent_str * self.indent_level
    
    def _build_test_payload(self, properties: Dict[str, Any], minimal: bool = True) -> List[str]:
        """Build test payload for testSuite following PKL test suite generator rules."""
        lines = []
        
        for key, val in properties.items():
            # Skip payload wrapper - output its children directly
            if key.lower() == 'payload' and isinstance(val, dict) and 'properties' in val:
                for sub_key, sub_val in val['properties'].items():
                    parent_section = sub_key  # loanDetails or orderDetails
                    lines.extend(self._build_section_block(sub_key, sub_val, minimal, parent_section))
            else:
                parent_section = key
                lines.extend(self._build_section_block(key, val, minimal, parent_section))
        
        return lines
    
    def _build_section_block(self, section_name: str, section_def: Dict[str, Any], minimal: bool, parent_section: str) -> List[str]:
        """Build loanDetails or orderDetails section block in test payload."""
        lines = []
        
        # Only process if it's loanDetails or orderDetails
        if section_name not in ['loanDetails', 'orderDetails']:
            return lines
        
        lines.append(f'{self._indent()}{section_name} {{')
        self.indent_level += 1
        
        if 'properties' in section_def:
            for key, val in section_def['properties'].items():
                lines.extend(self._build_test_property(key, val, minimal, section_name))
        
        self.indent_level -= 1
        lines.append(f'{self._indent()}}}')
        
        return lines
    
    def _is_inherited_property(self, prop_name: str, parent_section: str) -> bool:
        """Check if property is inherited from template class."""
        inherited_in_loandetails = {
            'loanNumber', 'loanPurpose', 'primaryBorrower', 'coBorrowers', 'propertyAddress'
        }
        inherited_in_orderdetails = set()  # orderDetails has no inherited properties
        
        if parent_section == 'loanDetails':
            return prop_name in inherited_in_loandetails
        elif parent_section == 'orderDetails':
            return prop_name in inherited_in_orderdetails
        return False
    
    def _build_test_property(self, key: str, value: Dict[str, Any], minimal: bool, parent_section: str) -> List[str]:
        """Build a single test property value following PKL test suite rules.
        
        Handles:
        - Inherited template properties (special rules for primaryBorrower, propertyAddress)
        - Declared properties (no = new Dynamic)
        - Minimal vs full payload differences
        - Proper syntax for objects, arrays, scalars, enums
        """
        lines = []
        prop_type = value.get('type', 'string')
        is_inherited = self._is_inherited_property(key, parent_section)
        
        if prop_type == 'object':
            return self._build_object_test_value(key, value, minimal, parent_section, is_inherited)
        elif prop_type == 'array':
            return self._build_array_test_value(key, value, minimal, parent_section)
        elif prop_type == 'string':
            return self._build_string_test_value(key, value)
        elif prop_type == 'number':
            return self._build_number_test_value(key)
        elif prop_type == 'boolean':
            lines.append(f'{self._indent()}{key} = false')
            return lines
        
        return lines
    
    def _build_object_test_value(self, key: str, value: Dict[str, Any], minimal: bool, parent_section: str, is_inherited: bool) -> List[str]:
        """Build test value for object properties.
        
        Rules:
        - propertyAddress: Always use = new Dynamic { ... } in both minimal and full
        - primaryBorrower (if has child objects): 
          - minimal: plain nesting { ... }
          - full: = new Dynamic { ... }
        - Other inherited properties: plain nesting
        - Declared properties (non-inherited): plain nesting
        - ALL properties from config are included in both minimal and full
        """
        lines = []
        
        # Special case: propertyAddress ALWAYS needs = new Dynamic in both minimal and full
        if key == 'propertyAddress' and is_inherited:
            lines.append(f'{self._indent()}{key} = new Dynamic {{')
            self.indent_level += 1
            if 'properties' in value:
                # Include ALL properties
                for sub_key, sub_val in value['properties'].items():
                    lines.extend(self._build_test_property(sub_key, sub_val, minimal, parent_section))
            self.indent_level -= 1
            lines.append(f'{self._indent()}}}')
            return lines
        
        # Special case: primaryBorrower in full payload uses = new Dynamic
        if key == 'primaryBorrower' and is_inherited and not minimal:
            lines.append(f'{self._indent()}{key} = new Dynamic {{')
            self.indent_level += 1
            if 'properties' in value:
                # Include ALL properties
                for sub_key, sub_val in value['properties'].items():
                    lines.extend(self._build_test_property(sub_key, sub_val, minimal, parent_section))
            self.indent_level -= 1
            lines.append(f'{self._indent()}}}')
            return lines
        
        # Default: plain nesting (for all other objects, or primaryBorrower in minimal)
        lines.append(f'{self._indent()}{key} {{')
        self.indent_level += 1
        
        if 'properties' in value:
            # Include ALL properties in both minimal and full payloads
            for sub_key, sub_val in value['properties'].items():
                lines.extend(self._build_test_property(sub_key, sub_val, minimal, parent_section))
        
        self.indent_level -= 1
        lines.append(f'{self._indent()}}}')
        
        return lines
    
    def _build_array_test_value(self, key: str, value: Dict[str, Any], minimal: bool, parent_section: str) -> List[str]:
        """Build test value for array properties - include ALL fields in both minimal and full."""
        lines = []
        
        lines.append(f'{self._indent()}{key} {{')
        self.indent_level += 1
        
        # Always include at least 1 item
        item_count = 1
        for i in range(item_count):
            lines.append(f'{self._indent()}new {{')
            self.indent_level += 1
            
            if 'items' in value and 'properties' in value['items']:
                # Include ALL properties in both minimal and full
                for item_key, item_val in value['items']['properties'].items():
                    lines.extend(self._build_test_property(item_key, item_val, minimal, parent_section))
            
            self.indent_level -= 1
            lines.append(f'{self._indent()}}}')
        
        self.indent_level -= 1
        lines.append(f'{self._indent()}}}')
        
        return lines
    
    def _build_string_test_value(self, key: str, value: Dict[str, Any]) -> List[str]:
        """Build test value for string properties."""
        lines = []
        
        if 'enum' in value and value['enum']:
            # Use first enum value
            enum_val = value['enum'][0]
            lines.append(f'{self._indent()}{key} = "{enum_val}"')
        else:
            # Generate sensible default based on field name
            test_val = self._generate_string_test_value(key)
            lines.append(f'{self._indent()}{key} = "{test_val}"')
        
        return lines
    
    def _build_number_test_value(self, key: str) -> List[str]:
        """Build test value for number properties."""
        lines = []
        
        if self._should_use_integer(key):
            # IntegerProperty: no decimal suffix
            lines.append(f'{self._indent()}{key} = 1')
        else:
            # DecimalProperty: MUST have .0 suffix
            lines.append(f'{self._indent()}{key} = 0.0')
        
        return lines
    
    def _generate_string_test_value(self, key: str) -> str:
        """Generate realistic test value for string field based on field name."""
        key_lower = key.lower()
        
        # Date fields
        if 'date' in key_lower:
            return "2025-01-15"
        # Name fields
        if 'firstname' in key_lower:
            return "John"
        if 'lastname' in key_lower:
            return "Doe"
        if 'name' in key_lower:
            return "John Doe"
        # Address fields
        if 'address' in key_lower:
            return "123 Main St"
        if 'city' in key_lower:
            return "Springfield"
        if 'state' in key_lower:
            return "IL"
        if 'postal' in key_lower or 'zipcode' in key_lower:
            return "62701"
        # ID fields
        if 'identifier' in key_lower or 'id' in key_lower:
            return "ID-001"
        # Type fields
        if 'type' in key_lower:
            return "Standard"
        # Generic fallback
        return f"sample-{key}"
    
    def _is_key_sample(self, key: str) -> bool:
        """Determine if a key should be included in minimal test payload."""
        # Include key fields in minimal payload
        priority_keywords = ['id', 'identifier', 'type', 'name', 'amount', 'firstname', 'lastname', 'address', 'city', 'state', 'postal']
        return any(keyword in key.lower() for keyword in priority_keywords)
