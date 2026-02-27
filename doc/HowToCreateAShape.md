# Writing SHACL Shapes for Kastor

This document explains how to write SHACL (Shapes Constraint Language) shape files for use with the Kastor framework. Shapes define the structure of RDF data that the system will extract from text.

## Table of Contents

1. [Overview](#overview)
2. [Basic Structure](#basic-structure)
3. [Required Elements](#required-elements)
4. [Property Definitions](#property-definitions)
5. [Supported Datatypes](#supported-datatypes)
6. [Object Properties](#object-properties)
7. [Advanced Features](#advanced-features)
8. [Complete Examples](#complete-examples)
9. [Best Practices](#best-practices)
10. [Validation](#validation)

---

## Overview

In Kastor, SHACL shapes serve two purposes:

1. **Define target entities**: Specify which class of entities to extract (e.g., `dbo:Person`, `dbo:Film`)
2. **Define extractable properties**: List the properties and their types that the model should learn to extract

The shape file is parsed by `kstor/src/triple_shapes.py` using SPARQL queries to extract:
- The target class (`sh:targetClass`)
- All property paths (`sh:path`)
- Property types (`sh:datatype` or `sh:class`)

---

## Basic Structure

A shape file is a Turtle (`.ttl`) file with the following structure:

```turtle
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dbo: <http://dbpedia.org/ontology/> .
@prefix schema: <http://schema.org/> .

schema:YourShape a sh:NodeShape ;
    sh:targetClass dbo:YourTargetClass ;
    sh:property [
        sh:path dbo:someProperty ;
        sh:datatype xsd:string ;
    ] .
```

---

## Required Elements

### 1. Prefixes

Always include these standard prefixes:

```turtle
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dbo: <http://dbpedia.org/ontology/> .
```

Optional but recommended:
```turtle
@prefix schema: <http://schema.org/> .
```

### 2. Shape Declaration

```turtle
schema:YourShape a sh:NodeShape ;
```

Or using full URI:
```turtle
<http://shaclshapes.org/YourShape> a sh:NodeShape ;
```

### 3. Target Class

**This is mandatory.** Specifies which DBpedia ontology class the shape applies to:

```turtle
sh:targetClass dbo:Person ;
```

Common target classes:
- `dbo:Person` - People (artists, politicians, scientists, etc.)
- `dbo:Film` - Movies
- `dbo:Company` - Organizations and companies
- `dbo:Place` - Locations (cities, countries, etc.)
- `dbo:University` - Educational institutions
- `dbo:MusicalWork` - Songs and albums
- `dbo:WrittenWork` - Books and publications

---

## Property Definitions

Properties are defined using blank nodes with `sh:property`:

```turtle
sh:property [
    sh:path <property_URI> ;
    sh:datatype <datatype_URI> ;    # For literal values
    # OR
    sh:class <class_URI> ;          # For object properties (links to other entities)
    sh:minCount <integer> ;         # Optional: minimum occurrences
    sh:maxCount <integer> ;         # Optional: maximum occurrences
    sh:nodeKind sh:Literal ;        # Optional: explicit node kind
] ;
```

### Property Path (`sh:path`)

The property path specifies which RDF predicate to use. Common patterns:

```turtle
# DBpedia ontology properties
sh:path dbo:birthDate ;
sh:path dbo:nationality ;

# RDFS label (entity name)
sh:path rdfs:label ;

# Full URI (alternative syntax)
sh:path <http://dbpedia.org/ontology/birthDate> ;
```

### Cardinality Constraints

```turtle
sh:minCount 1 ;    # Required property (at least 1 value)
sh:minCount 0 ;    # Optional property
sh:maxCount 1 ;    # Single-valued property
sh:maxCount 10 ;   # Multi-valued property (up to 10 values)
```

---

## Supported Datatypes

Use `sh:datatype` for literal (data) properties:

| Datatype | Description | Example Value |
|----------|-------------|---------------|
| `xsd:string` | Text strings | `"Albert Einstein"` |
| `xsd:date` | Full dates | `"1879-03-14"` |
| `xsd:gYear` | Year only | `"1879"` |
| `xsd:double` | Decimal numbers | `"175.5"` |
| `xsd:integer` | Whole numbers | `"42"` |
| `xsd:nonNegativeInteger` | Non-negative integers | `"100"` |
| `rdf:langString` | Language-tagged strings | `"Einstein"@en` |

### Examples

```turtle
# String property
sh:property [
    sh:path dbo:birthName ;
    sh:datatype xsd:string ;
    sh:minCount 0 ;
    sh:maxCount 1 ;
] ;

# Date property
sh:property [
    sh:path dbo:birthDate ;
    sh:datatype xsd:date ;
    sh:minCount 1 ;
    sh:maxCount 1 ;
] ;

# Year property
sh:property [
    sh:path dbo:birthYear ;
    sh:datatype xsd:gYear ;
    sh:minCount 1 ;
    sh:maxCount 1 ;
] ;

# Numeric property
sh:property [
    sh:path dbo:runtime ;
    sh:datatype xsd:double ;
] ;
```

---

## Object Properties

Object properties link to other entities (URIs) rather than literal values. Use `sh:class` instead of `sh:datatype`:

```turtle
# Links to a Place entity
sh:property [
    sh:path dbo:birthPlace ;
    sh:class dbo:Place ;
    sh:minCount 0 ;
    sh:maxCount 1 ;
] ;

# Links to a Country entity
sh:property [
    sh:path dbo:nationality ;
    sh:class dbo:Country ;
    sh:minCount 0 ;
    sh:maxCount 10 ;
] ;

# Links to a Person entity
sh:property [
    sh:path dbo:spouse ;
    sh:class dbo:Person ;
] ;
```

### Common Object Property Ranges

| Range Class | Used For |
|-------------|----------|
| `dbo:Place` | birthPlace, deathPlace, residence |
| `dbo:Country` | nationality, citizenship, country |
| `dbo:Person` | spouse, parent, child, relative |
| `dbo:Organisation` | employer, almaMater, distributor |
| `dbo:Language` | language |
| `dbo:Genre` | genre |
| `dbo:Award` | award |

---

## Advanced Features

### Alternative Properties with `sh:or`

When a property can be satisfied by multiple alternatives (e.g., birthDate OR birthYear):

```turtle
sh:or (
    [
        sh:property [
            sh:path dbo:birthDate ;
            sh:datatype xsd:date ;
            sh:minCount 1 ;
            sh:maxCount 1 ;
        ]
    ]
    [
        sh:property [
            sh:path dbo:birthYear ;
            sh:datatype xsd:gYear ;
            sh:minCount 1 ;
            sh:maxCount 1 ;
        ]
    ]
) ;
```

### Node Kind Specification

Explicitly specify the kind of RDF node:

```turtle
sh:property [
    sh:path dbo:alias ;
    sh:datatype xsd:string ;
    sh:nodeKind sh:Literal ;  # Ensures it's a literal, not a URI
] ;
```

---

## Complete Examples

### Example 1: Simple Person Shape (Datatype Properties Only)

```turtle
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dbo: <http://dbpedia.org/ontology/> .
@prefix schema: <http://schema.org/> .

schema:PersonShape a sh:NodeShape ;
    sh:targetClass dbo:Person ;
    sh:property [
        sh:path rdfs:label ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        sh:path dbo:birthDate ;
        sh:datatype xsd:date ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path dbo:deathDate ;
        sh:datatype xsd:date ;
        sh:minCount 0 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path dbo:birthName ;
        sh:datatype xsd:string ;
        sh:minCount 0 ;
        sh:maxCount 1 ;
    ] .
```

### Example 2: Person Shape with Object Properties

```turtle
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dbo: <http://dbpedia.org/ontology/> .
@prefix schema: <http://schema.org/> .

schema:PersonShape a sh:NodeShape ;
    sh:targetClass dbo:Person ;
    # Required: entity label
    sh:property [
        sh:path rdfs:label ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
    ] ;
    # Datatype properties
    sh:property [
        sh:path dbo:birthDate ;
        sh:datatype xsd:date ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path dbo:deathDate ;
        sh:datatype xsd:date ;
        sh:minCount 0 ;
        sh:maxCount 1 ;
    ] ;
    # Object properties (links to other entities)
    sh:property [
        sh:path dbo:birthPlace ;
        sh:class dbo:Place ;
        sh:minCount 0 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path dbo:nationality ;
        sh:class dbo:Country ;
        sh:minCount 0 ;
        sh:maxCount 10 ;
    ] ;
    sh:property [
        sh:path dbo:spouse ;
        sh:class dbo:Person ;
        sh:minCount 0 ;
        sh:maxCount 5 ;
    ] .
```

### Example 3: Film Shape

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dbo: <http://dbpedia.org/ontology/> .

<http://shaclshapes.org/FilmShape> a sh:NodeShape ;
    sh:targetClass dbo:Film ;
    sh:property [
        sh:path dbo:director ;
        sh:class dbo:Person ;
    ] ;
    sh:property [
        sh:path dbo:starring ;
        sh:class dbo:Actor ;
    ] ;
    sh:property [
        sh:path dbo:releaseDate ;
        sh:datatype xsd:date ;
    ] ;
    sh:property [
        sh:path dbo:runtime ;
        sh:datatype xsd:double ;
    ] ;
    sh:property [
        sh:path dbo:budget ;
        sh:datatype xsd:double ;
    ] ;
    sh:property [
        sh:path dbo:language ;
        sh:class dbo:Language ;
    ] .
```

---

## Best Practices

### 1. Start Simple

Begin with a small number of properties and expand as needed:

```turtle
# Start with core properties
sh:property [ sh:path rdfs:label ; sh:datatype xsd:string ; ] ;
sh:property [ sh:path dbo:birthDate ; sh:datatype xsd:date ; ] ;
```

### 2. Use Consistent Naming

Name your shape file to match the target class:
- `PersonShape.ttl` for `dbo:Person`
- `FilmShape.ttl` for `dbo:Film`

Use suffixes for variants:
- `PersonShape_dp.ttl` - Datatype properties only
- `PersonShape_op.ttl` - Object properties only
- `PersonShape_op_and_dp.ttl` - Both types

### 3. Consider Data Availability

Only include properties that are commonly present in your source data (DBpedia). Check property coverage before adding to shape.

### 4. Balance Specificity

- Too few properties: Model may not learn enough patterns
- Too many properties: Data sparsity, longer training, harder evaluation

Recommended: 5-15 properties per shape.

### 5. Separate Datatype and Object Properties

For experimentation, create separate shape files:

```
PersonShape_dp.ttl     # Only sh:datatype properties
PersonShape_op.ttl     # Only sh:class properties
PersonShape_op_and_dp.ttl  # Combined
```

### 6. Document Property Choices

Add comments to explain non-obvious property selections:

```turtle
# Core identification
sh:property [ sh:path rdfs:label ; sh:datatype xsd:string ; ] ;

# Temporal properties (commonly found in Wikipedia abstracts)
sh:property [ sh:path dbo:birthDate ; sh:datatype xsd:date ; ] ;
sh:property [ sh:path dbo:deathDate ; sh:datatype xsd:date ; ] ;

# Geographic properties (require Wikipedia markdown for validation)
sh:property [ sh:path dbo:birthPlace ; sh:class dbo:Place ; ] ;
```

---

## Validation

### Check Shape Syntax

Use rdflib to validate your shape file:

```python
from rdflib import Graph

shape = Graph()
shape.parse("YourShape.ttl")

# Check target class exists
from kstor.src.triple_shapes import getShapeType, getShapeProp

target_class = getShapeType(shape)
properties = getShapeProp(shape)

print(f"Target class: {target_class}")
print(f"Properties: {properties}")
```

### Common Errors

1. **Missing target class**: Shape must have exactly one `sh:targetClass`
2. **Invalid URIs**: Ensure all URIs are properly formatted
3. **Mixed syntax**: Don't mix `sh:datatype` and `sh:class` on the same property
4. **Missing semicolons**: Turtle syntax requires `;` between properties

### Test with Pipeline

After creating your shape, test it with the initialization script:

```bash
cd kstor
python 1_KD-1_initializeKastorFromShape.py -s ../shapes/YourShape.ttl
```

---

## Shape File Naming Convention

| Pattern | Description |
|---------|-------------|
| `{Class}Shape.ttl` | Base shape for a class |
| `{Class}Shape_dp.ttl` | Datatype properties only |
| `{Class}Shape_op.ttl` | Object properties only |
| `{Class}Shape_op_and_dp.ttl` | Both property types |
| `{Class}ShapeFromOnto.ttl` | Auto-generated from ontology |
| `{Class}ShapeInWild.ttl` | Properties found in actual data |
| `{Class}ShapeTXT2KG.ttl` | Compatible with Text2KG benchmark |
| `{Class}ShapeTXT2KG_clean.ttl` | Cleaned Text2KG shape |

---

## Quick Reference

```turtle
# Minimal valid shape
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dbo: <http://dbpedia.org/ontology/> .

<http://shaclshapes.org/MyShape> a sh:NodeShape ;
    sh:targetClass dbo:MyClass ;
    sh:property [
        sh:path dbo:someProperty ;
        sh:datatype xsd:string ;
    ] .
```

```turtle
# Full property definition
sh:property [
    sh:path dbo:propertyName ;      # Required: the RDF predicate
    sh:datatype xsd:string ;        # For literals (OR sh:class for URIs)
    sh:minCount 0 ;                 # Optional: 0 = optional, 1+ = required
    sh:maxCount 1 ;                 # Optional: limits multiple values
    sh:nodeKind sh:Literal ;        # Optional: explicit node type
] ;
```
