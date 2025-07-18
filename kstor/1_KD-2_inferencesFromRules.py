"""
1_KD-2_inferencesFromRules.py

This script applies rule-based inference to RDF data in a SPARQL endpoint, enabling the
derivation of implicit knowledge from explicit data. It processes inference rules defined
in XML format to either generate new triples or remove previously inferred statements.

Key features:
- Processes rule definitions from XML files following the Corese rule format
- Supports both insert and delete operations for managing inferred triples
- Integrates with SPARQL endpoints for efficient rule execution
- Handles namespace management for consistent rule application

Typical use cases include:
- Materializing inferred properties for improved query performance
- Cleaning up previously inferred data when source data changes
- Applying domain-specific reasoning over RDF datasets

Usage Examples:
1. Apply inference rules to generate new triples:
   python 1_KD-2_inferencesFromRules.py -r path/to/rules.xml -m insert

2. Remove previously inferred triples:
   python 1_KD-2_inferencesFromRules.py -r path/to/rules.xml -m delete

3. Process rules for a specific shape file:
   python 1_KD-2_inferencesFromRules.py -s path/to/shape.ttl -r path/to/rules.xml -m insert

Rule XML Format:
<rule>
    <body>
        ?x rdf:type ex:Person .
        ?x ex:hasParent ?y .
    </body>
    <head>
        ?y rdf:type ex:Parent .
    </head>
</rule>
"""

import re
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
import logging

# Import custom Corese tools for SPARQL operations
import src.corese_tools as ct

if __name__ == '__main__':
    # Set up command line argument parsing
    parser = ArgumentParser(description='Apply inference rules to RDF data in a SPARQL endpoint')
    parser.add_argument("-s", "--shape_file_path", default=None,
                       help="Path to the shape file being processed")
    parser.add_argument("-r", "--rules_file_path", default=None,
                       help="Path to the XML file containing inference rules")
    parser.add_argument("-m", "--mode", default="insert",
                       choices=["insert", "delete"],
                       help="Operation mode: 'insert' to add inferences, 'delete' to remove them")

    args = parser.parse_args()
    
    # Initialize SPARQL endpoint
    sparql_ep = 'http://localhost:8080/sparql'
    
    # Check if rules file is provided
    if args.rules_file_path and args.mode in ["insert", "delete"]:
        # Initialize query string and parse the rules XML file
        query = ""
        
        # Parse the XML rules file
        tree = ET.parse(args.rules_file_path)
        root = tree.getroot()
        
        # Find all rule elements in the XML
        rules = root.findall("{http://ns.inria.fr/corese/rule/}rule/")
        
        # Pattern used for string replacement in queries
        pattern_replace = "$INFERENCE_NS$"
        named_graph_used = None
        
        print(f">>>>>> Number of rules to apply: {len(rules)}")

        # Handle delete mode
        if args.mode == "delete":
            if args.shape_file_path:
                # Extract shape name from file path
                shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")
                print(f"Deleting inferences for shape: {shape_name}")
                
                # Construct named graph URI for inferences
                named_graph_used = f"<http://ns.inria.fr/kstor/inferences/{shape_name}>"
                
                # Drop the entire inference graph
                query_delete = f"DROP GRAPH {named_graph_used}"
                res = ct.sparql_service_update(sparql_ep, query_delete)
        
        # Handle insert mode
        else:
            for rule in rules:
                if args.mode == "insert":
                    # Convert CONSTRUCT query to INSERT for SPARQL update
                    query = rule.text.replace("CONSTRUCT", "INSERT")
                
                print("############# Processing Rule Matches #############")
                print(query)
                
                # Process shape file if provided
                if args.shape_file_path:
                    shape_name = args.shape_file_path.split("/")[-1].replace(".ttl", "")
                    if pattern_replace in query:
                        named_graph_used = f"<http://ns.inria.fr/kstor/inferences/{shape_name}>"
                
                # Determine the regex pattern based on whether we have a placeholder or direct graph name
                if pattern_replace in query:
                    print('Processing with inference namespace placeholder')
                    regex1 = r"GRAPH \$INFERENCE_NS\$"
                else:
                    regex1 = r"GRAPH ks:[\w|\"_\"]+"
                
                # Find all graph patterns in the query
                matches = re.findall(regex1, query, re.MULTILINE)
                
                if matches:
                    # Use the first match as the named graph if not already set
                    if named_graph_used is None:
                        named_graph_used = matches[0].replace("GRAPH", "").strip()
                    
                    # Process the query based on whether it contains the placeholder
                    if pattern_replace in query:
                        # Extract the content inside the GRAPH clause
                        regex2 = r" GRAPH \$INFERENCE_NS\$ {([^}]+)}"
                        added_ = re.findall(regex2, query, re.MULTILINE)
                        added = added_[0].strip()
                        query = query.replace(pattern_replace, named_graph_used)
                    else:
                        # Extract content from explicit graph name
                        regex2 = r" GRAPH " + named_graph_used + " {([^}]+)}"
                        added_ = re.findall(regex2, query, re.MULTILINE)
                        added = added_[0].strip()
                    
                    # Count triples before operation for verification
                    count_query = f"""
                    PREFIX dbo: <http://dbpedia.org/ontology/>
                    PREFIX ks: <http://ns.inria.fr/kstor/#>
                    SELECT (COUNT(*) as ?Triples)
                    FROM {named_graph_used}
                    {{ {added} }}
                    """
                    
                    print(f"Counting triples before {args.mode} operation...")
                    res_count = ct.sparql_service_to_int(sparql_ep, count_query)
                    print(f"Found {res_count} triples before {args.mode} operation")
                    
                    # Execute the update query
                    print("Executing update query...")
                    res = ct.sparql_service_update(sparql_ep, query)
                    
                    # Count triples after operation for verification
                    res_count = ct.sparql_service_to_int(sparql_ep, count_query)
                    print(f"Found {res_count} triples after {args.mode} operation")
    else:
        logging.error("Rules file path not provided or invalid mode. Mode must be 'insert' or 'delete'.")
