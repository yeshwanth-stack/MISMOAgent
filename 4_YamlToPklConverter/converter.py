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
    
    def _humanize_enum(self, enum_val: str) -> str:
        """Convert enum value to human-readable form."""
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
        """Build test payload for testSuite - skip payload wrapper."""
        lines = []
        
        for key, val in properties.items():
            # Skip payload wrapper - output its children directly
            if key.lower() == 'payload' and isinstance(val, dict) and 'properties' in val:
                for sub_key, sub_val in val['properties'].items():
                    lines.extend(self._build_test_property(sub_key, sub_val, minimal, is_top_level=True))
            else:
                lines.extend(self._build_test_property(key, val, minimal, is_top_level=True))
        
        return lines
    
    def _build_test_property(self, key: str, value: Dict[str, Any], minimal: bool = True, is_top_level: bool = False) -> List[str]:
        """Build a test property value.
        
        is_top_level: True if this property is a direct child of loanDetails/orderDetails.
                     At top level, the first field is always included (for structure).
                     At nested levels, only key sample fields are included.
        """
        lines = []
        prop_type = value.get('type', 'string')
        
        if prop_type == 'object':
            lines.append(f'{self._indent()}{key} {{')
            self.indent_level += 1
            
            if 'properties' in value:
                properties_list = list(value['properties'].items())
                for idx, (sub_key, sub_val) in enumerate(properties_list):
                    if not minimal:
                        # Full payload: include all
                        lines.extend(self._build_test_property(sub_key, sub_val, minimal, is_top_level=False))
                    else:
                        # Minimal payload
                        is_first = idx == 0
                        is_key_sample = self._is_key_sample(sub_key)
                        
                        # Rules:
                        # - At top level: include first field OR key samples
                        # - At nested levels: ONLY key samples
                        should_include = False
                        if is_top_level and is_first:
                            should_include = True
                        elif is_key_sample:
                            should_include = True
                        
                        if should_include:
                            lines.extend(self._build_test_property(sub_key, sub_val, minimal, is_top_level=False))
            
            self.indent_level -= 1
            lines.append(f'{self._indent()}}}')
            
        elif prop_type == 'array':
            lines.append(f'{self._indent()}{key} {{')
            self.indent_level += 1
            
            item_count = 1 if minimal else 2
            for i in range(item_count):
                lines.append(f'{self._indent()}new {{')
                self.indent_level += 1
                
                if 'items' in value and 'properties' in value['items']:
                    items_list = list(value['items']['properties'].items())
                    for idx, (item_key, item_val) in enumerate(items_list):
                        if not minimal:
                            # Full payload: include all
                            lines.extend(self._build_test_property(item_key, item_val, minimal, is_top_level=False))
                        else:
                            # Minimal: ONLY include key sample fields in arrays
                            if self._is_key_sample(item_key):
                                lines.extend(self._build_test_property(item_key, item_val, minimal, is_top_level=False))
                
                self.indent_level -= 1
                lines.append(f'{self._indent()}}}')
            
            self.indent_level -= 1
            lines.append(f'{self._indent()}}}')
            
        elif prop_type == 'string':
            if 'enum' in value:
                enum_val = value['enum'][0]
                lines.append(f'{self._indent()}{key} = "{enum_val}"')
            else:
                lines.append(f'{self._indent()}{key} = "sample-value"')
                
        elif prop_type == 'number':
            if self._should_use_integer(key):
                lines.append(f'{self._indent()}{key} = 1')
            else:
                lines.append(f'{self._indent()}{key} = 0.0')
                
        elif prop_type == 'boolean':
            lines.append(f'{self._indent()}{key} = false')
        
        return lines
    
    def _is_key_sample(self, key: str) -> bool:
        """Determine if a key should be included in minimal test payload."""
        # Include key fields in minimal payload
        priority_keywords = ['id', 'identifier', 'type', 'name', 'amount']
        return any(keyword in key.lower() for keyword in priority_keywords)
