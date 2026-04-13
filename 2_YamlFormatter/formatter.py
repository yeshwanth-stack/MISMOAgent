"""
YAML Formatter
Transforms raw YAML into Order Management standard format with interactive property placement
"""

import yaml
from typing import Dict, List, Any, Optional
from collections import OrderedDict


class YamlFormatter:
    """Formats raw YAML into standardized Order Management structure"""
    
    def __init__(self):
        self.root_properties = []
        self.loan_details_properties = []
        self.order_details_properties = []
    
    def load_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """Load and parse YAML content"""
        return yaml.safe_load(yaml_content)
    
    def extract_root_properties(self, yaml_dict: Dict[str, Any]) -> List[str]:
        """Extract all root-level properties from YAML"""
        if isinstance(yaml_dict, dict) and 'properties' in yaml_dict:
            return list(yaml_dict['properties'].keys())
        return []
    
    def interactive_categorization(self, properties: List[str]) -> tuple:
        """
        Ask user to categorize properties into loanDetails and orderDetails
        Returns (loan_properties, order_properties)
        """
        print("\n" + "="*70)
        print("YAML FORMATTER - INTERACTIVE PROPERTY CATEGORIZATION")
        print("="*70)
        
        print(f"\nFound {len(properties)} root-level properties:")
        for i, prop in enumerate(properties, 1):
            print(f"  {i}. {prop}")
        
        print("\n" + "-"*70)
        print("INSTRUCTIONS:")
        print("  • Enter property NUMBERS separated by commas: 1,2,3")
        print("  • OR enter property NAMES separated by commas: loans,assets")
        print("  • The remaining properties will go to orderDetails")
        print("-"*70)
        
        loan_details = []
        
        while True:
            print(f"\nAvailable properties: {properties}")
            
            loan_input = input("\n→ Enter properties for 'loanDetails' (numbers or names): ").strip()
            
            if not loan_input:
                print("  ⚠ Please enter at least one property, or press Ctrl+C to exit")
                continue
            
            # Parse user input
            entries = [x.strip() for x in loan_input.split(',')]
            parsed_loan = []
            errors = []
            
            for entry in entries:
                found = False
                
                # Try as number (1-indexed)
                try:
                    idx = int(entry) - 1
                    if 0 <= idx < len(properties):
                        parsed_loan.append(properties[idx])
                        found = True
                except ValueError:
                    pass
                
                # Try as property name (case-insensitive)
                if not found:
                    for prop in properties:
                        if prop.lower() == entry.lower():
                            parsed_loan.append(prop)
                            found = True
                            break
                
                if not found:
                    errors.append(entry)
            
            # Check for errors
            if errors:
                print(f"  ⚠ Could not find: {errors}")
                print(f"     Use numbers 1-{len(properties)} or exact property names")
                continue
            
            # Check for duplicates
            if len(parsed_loan) != len(set(parsed_loan)):
                print(f"  ⚠ Duplicate entries detected")
                continue
            
            # Confirm selection
            loan_details = parsed_loan
            order_details = [p for p in properties if p not in loan_details]
            
            print(f"\n✓ Selected for loanDetails:  {loan_details}")
            print(f"✓ Assigned to orderDetails: {order_details}")
            
            confirm = input("\n→ Is this correct? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                break
            elif confirm not in ['no', 'n']:
                print("  ⚠ Please enter 'yes' or 'no'")
        
        print("\n" + "="*70)
        print("✓ Categorization complete!")
        print("="*70)
        
        return loan_details, order_details
    
    def format_yaml(self, yaml_dict: Dict[str, Any], loan_props: List[str], 
                    order_props: List[str]) -> str:
        """
        Format raw YAML into standardized structure with exact indentation
        """
        output_lines = []
        
        # Root level
        output_lines.append("type: object")
        output_lines.append("properties:")
        
        # Payload wrapper
        output_lines.append("  payload:")
        output_lines.append("    type: object")
        output_lines.append("    properties:")
        
        # Get original properties
        original_properties = yaml_dict.get('properties', {})
        
        # loanDetails section
        output_lines.append("      loanDetails:")
        output_lines.append("        type: object")
        output_lines.append("        properties:")
        
        if loan_props:
            for prop in loan_props:
                if prop in original_properties:
                    # Add the property with its original structure
                    prop_lines = self._format_property(original_properties[prop], prop)
                    for line in prop_lines:
                        output_lines.append("          " + line)
        else:
            output_lines.append("          # No properties assigned to loanDetails")
        
        # orderDetails section
        output_lines.append("      orderDetails:")
        output_lines.append("        type: object")
        output_lines.append("        properties:")
        
        if order_props:
            for prop in order_props:
                if prop in original_properties:
                    # Add the property with its original structure
                    prop_lines = self._format_property(original_properties[prop], prop)
                    for line in prop_lines:
                        output_lines.append("          " + line)
        else:
            output_lines.append("          # No properties assigned to orderDetails")
        
        return '\n'.join(output_lines)
    
    def _format_property(self, prop_value: Any, prop_name: str, indent: int = 0) -> List[str]:
        """
        Format a property with its structure, maintaining exact indentation
        indent is in terms of property-level indentation (each level = 2 spaces)
        """
        lines = []
        indent_str = ""  # Will be added by parent
        
        # Property name line
        lines.append(f"{prop_name}:")
        
        if isinstance(prop_value, dict):
            # Handle type
            if 'type' in prop_value:
                lines.append(f"  type: {prop_value['type']}")
            
            # Handle enum
            if 'enum' in prop_value:
                lines.append(f"  enum:")
                for enum_val in prop_value['enum']:
                    lines.append(f"    - {enum_val}")
            
            # Handle jpath
            if 'jpath' in prop_value:
                lines.append(f"  jpath: {prop_value['jpath']}")
            
            # Handle properties (nested)
            if 'properties' in prop_value and isinstance(prop_value['properties'], dict):
                lines.append(f"  properties:")
                for nested_prop_name, nested_prop_value in prop_value['properties'].items():
                    nested_lines = self._format_property(nested_prop_value, nested_prop_name, indent + 1)
                    for line in nested_lines:
                        lines.append(f"    {line}")
            
            # Handle items (array)
            if 'items' in prop_value:
                lines.append(f"  items:")
                items_value = prop_value['items']
                if isinstance(items_value, dict):
                    for key, val in items_value.items():
                        if key == 'properties' and isinstance(val, dict):
                            lines.append(f"    {key}:")
                            for nested_prop_name, nested_prop_value in val.items():
                                nested_lines = self._format_property(nested_prop_value, nested_prop_name, indent + 1)
                                for line in nested_lines:
                                    lines.append(f"      {line}")
                        elif key != 'properties':
                            lines.append(f"    {key}: {val}")
        else:
            lines.append(f"  {prop_value}")
        
        return lines


def format_yaml_file(input_file: str, output_file: str) -> bool:
    """
    Main function to format YAML file interactively
    """
    try:
        # Read input
        with open(input_file, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
        
        # Parse
        formatter = YamlFormatter()
        yaml_dict = formatter.load_yaml(yaml_content)
        
        # Extract properties
        properties = formatter.extract_root_properties(yaml_dict)
        
        if not properties:
            print("⚠ No properties found in YAML schema")
            return False
        
        # Ask user for categorization
        loan_props, order_props = formatter.interactive_categorization(properties)
        
        # Format
        formatted_yaml = formatter.format_yaml(yaml_dict, loan_props, order_props)
        
        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_yaml)
        
        print(f"\n✓ Formatted YAML written to: {output_file}")
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False
