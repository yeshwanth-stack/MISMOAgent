#!/usr/bin/env python3
"""Quick test of the improved formatter"""

import yaml
from formatter import YamlFormatter

# Load sample YAML
with open('input.yaml', 'r') as f:
    yaml_dict = yaml.safe_load(f)

# Test formatter
formatter = YamlFormatter()
properties = formatter.extract_root_properties(yaml_dict)

print("✓ YamlFormatter - Interactive Test")
print(f"✓ Loaded {len(properties)} root properties:")
for i, prop in enumerate(properties, 1):
    print(f"  {i}. {prop}")

# Simulate user input: loans → loanDetails, others → orderDetails
print("\nTesting non-interactive categorization...")
loan_props = ['loans']
order_props = ['assets', 'collaterals', 'parties', 'documents']

formatted = formatter.format_yaml(yaml_dict, loan_props, order_props)
print("✓ Format successful!")

# Save output
with open('test_output.yaml', 'w') as f:
    f.write(formatted)
    
print("✓ Output written to test_output.yaml")
