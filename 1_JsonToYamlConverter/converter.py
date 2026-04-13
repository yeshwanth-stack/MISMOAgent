"""
MISMO JSON to YAML Schema Converter
Converts MISMO JSON payloads into YAML schema definitions.
"""

import json
import yaml
from typing import Any, Dict, List, Optional


class MISMOConverter:
    """Converts MISMO JSON to YAML schema following exact rules."""
    
    def __init__(self):
        self.path_stack: List[str] = []  # Track path for non-array context
        self.in_array: bool = False  # Track if we're inside array items
    
    def convert(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert MISMO JSON to YAML schema.
        
        Args:
            json_data: Parsed JSON dictionary
            
        Returns:
            YAML schema dictionary
        """
        self.path_stack = []
        self.in_array = False
        return self._convert_object(json_data, is_root=True)
    
    def _infer_type(self, value: Any) -> str:
        """Infer YAML type from JSON value."""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, dict):
            return "object"
        elif isinstance(value, list):
            return "array"
        return "string"
    
    def _get_jpath(self) -> str:
        """Get current jpath based on context."""
        if self.in_array:
            # Inside array items, jpath is relative to $ of the array item
            if not self.path_stack:
                return "$"
            return "$." + ".".join(self.path_stack)
        else:
            # Not in array, absolute path from root
            if not self.path_stack:
                return ""
            return "$." + ".".join(self.path_stack)
    
    def _merge_array_elements(self, array: List[Any]) -> Dict[str, Any]:
        """
        Merge all array elements into one representative object.
        Handles homogeneous and heterogeneous arrays.
        """
        if not array or not isinstance(array[0], dict):
            return {}
        
        merged = {}
        for element in array:
            if isinstance(element, dict):
                for key, value in element.items():
                    if key not in merged:
                        merged[key] = value
                    else:
                        # Deep merge for nested objects
                        if isinstance(value, dict) and isinstance(merged[key], dict):
                            merged[key] = self._deep_merge_objects(merged[key], value)
                        elif isinstance(value, list) and isinstance(merged[key], list):
                            # Merge array elements
                            merged_arr = self._merge_array_elements(merged[key] + value)
                            merged[key] = [merged_arr] if merged_arr else []
        
        return merged
    
    def _deep_merge_objects(self, obj1: Dict[str, Any], obj2: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two objects."""
        result = obj1.copy()
        for key, value in obj2.items():
            if key not in result:
                result[key] = value
            elif isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = self._deep_merge_objects(result[key], value)
            elif isinstance(value, list) and isinstance(result[key], list):
                merged_arr = self._merge_array_elements(result[key] + value)
                result[key] = [merged_arr] if merged_arr else []
        
        return result
    
    def _convert_primitive(self, value: Any) -> Dict[str, Any]:
        """Convert primitive value to schema."""
        schema = {"type": self._infer_type(value)}
        
        jpath = self._get_jpath()
        if jpath:  # Don't add jpath for root
            schema["jpath"] = jpath
        
        return schema
    
    def _convert_object(self, obj: Dict[str, Any], is_root: bool = False) -> Dict[str, Any]:
        """Convert object to schema."""
        schema = {"type": "object"}
        
        # Root object has no jpath
        # Non-root objects inside arrays have no jpath either (only their children do)
        # Non-root objects NOT in arrays have no jpath
        
        properties = {}
        for key, value in obj.items():
            self.path_stack.append(key)
            properties[key] = self._convert_value(value)
            self.path_stack.pop()
        
        schema["properties"] = properties
        return schema
    
    def _convert_array(self, array: List[Any]) -> Dict[str, Any]:
        """Convert array to schema."""
        schema = {
            "type": "array",
            "jpath": self._get_jpath()
        }
        
        # Merge all array elements
        merged_element = self._merge_array_elements(array)
        
        if merged_element:
            # Enter array items context
            prev_path_stack = self.path_stack
            prev_in_array = self.in_array
            
            self.path_stack = []  # Reset path stack for array items
            self.in_array = True
            
            schema["items"] = self._convert_object(merged_element)
            
            # Restore context
            self.path_stack = prev_path_stack
            self.in_array = prev_in_array
        else:
            schema["items"] = {"type": "object"}
        
        return schema
    
    def _convert_value(self, value: Any) -> Dict[str, Any]:
        """Convert any value to schema."""
        if isinstance(value, dict):
            return self._convert_object(value)
        elif isinstance(value, list):
            return self._convert_array(value)
        else:
            return self._convert_primitive(value)
    
    def to_yaml(self, json_data: Dict[str, Any]) -> str:
        """Convert to YAML string."""
        schema = self.convert(json_data)
        return yaml.dump(schema, default_flow_style=False, sort_keys=False, allow_unicode=True)


def convert_json_to_yaml(json_string: str) -> str:
    """
    Main conversion function.
    
    Args:
        json_string: Input JSON string
        
    Returns:
        YAML schema string
    """
    try:
        json_data = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    
    converter = MISMOConverter()
    return converter.to_yaml(json_data)
