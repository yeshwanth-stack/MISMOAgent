# Order Management Schema Converter Pipeline

A Python toolkit to convert JSON to PKL configuration files with YAML schema generation and enum enrichment.

## Quick Start

```bash
pip install PyYAML==6.0

# Step 1: JSON → YAML Schema
cd JsonToYamlConverter && python main.py input.json output.yaml

# Step 2: Enrich with Enums
cd ../EnumValuesUpdater && python main.py ../JsonToYamlConverter/output.yaml enum_definitions.txt output_enriched.yaml

# Step 3: YAML → PKL Configuration
cd ../YamlToPklConverter && python main.py ../EnumValuesUpdater/output_enriched.yaml output.pkl
```

## What It Does

- **JsonToYamlConverter**: Converts JSON to YAML schema with type inference and jpath generation
- **EnumValuesUpdater**: Adds enum values to YAML fields and auto-generates OtherDescription fields
- **YamlToPklConverter**: Transforms YAML schema to PKL configuration format with test payloads

## Project Structure

```
Agent/
├── JsonToYamlConverter/
├── YamlToPklConverter/
└── EnumValuesUpdater/
```

Each converter has:
- `main.py` - Entry point
- `converter.py` or `enricher.py` - Core logic
- `requirements.txt` - Dependencies
- Sample input files

## Details

### JsonToYamlConverter

Converts JSON to YAML schema with automatic type detection.

**Usage**: `python main.py <input.json> [output.yaml]`

Type detection: string, number, integer, boolean, array, object

---

### EnumValuesUpdater

Adds enum values to YAML schema fields from a definitions file.

**Usage**: `python main.py <schema.yaml> <enums.txt> [output.yaml]`

**Enum formats supported**:
- Comma-separated: `$.field: Value1, Value2, Value3`
- Newline-separated: `$.field` followed by values on new lines
- Pipe-separated: `$.field | Value1 | Value2`
- Tab-separated, numbered lists, and mixed formats

Auto-generates `{fieldName}OtherDescription` when "Other" is in enum values.

---

### YamlToPklConverter

Converts YAML schema to PKL configuration format.

**Usage**: `python main.py <schema.yaml> [output.pkl]`

Generates property definitions, enum values, labels, jpaths, and test payloads.
