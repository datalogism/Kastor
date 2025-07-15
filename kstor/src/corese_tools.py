#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 17:45:41 2024
"""

from SPARQLWrapper import JSON, POST, POSTDIRECTLY, SPARQLWrapper
from SPARQLWrapper import get_sparql_dataframe
import json 
import pandas as pd

def sparql_service_update(service, update_query):
    """
    Helper function to update (DELETE DATA, INSERT DATA, DELETE/INSERT) data.

    """
    sparql = SPARQLWrapper(service)
    sparql.setMethod(POST)
    sparql.setRequestMethod(POSTDIRECTLY)
    sparql.setQuery(update_query)
    sparql.query()

    # SPARQLWrapper is going to throw an exception if result.response.status != 200:

    return 'Done'

def sparql_service_to_int(service, query):
    """
    Helper function to convert SPARQL results into a Pandas DataFrame.

    Credit to Ted Lawless https://lawlesst.github.io/notebook/sparql-dataframe.html
    """
    sparql = SPARQLWrapper(service)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result = sparql.query()

    processed_results = json.load(result.response)
    cols = processed_results['head']['vars']

    out = None
    for row in processed_results['results']['bindings']:
        item = []
        for c in cols:
            out=int(row.get(c, {}).get('value'))

    return out

def sparql_service_to_dataframe(service, query):
    """
    Helper function to convert SPARQL results into a Pandas DataFrame.

    Credit to Ted Lawless https://lawlesst.github.io/notebook/sparql-dataframe.html
    """
    sparql = SPARQLWrapper(service)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result = sparql.query()

    processed_results = json.load(result.response)
    cols = processed_results['head']['vars']

    out = []
    for row in processed_results['results']['bindings']:
        item = []
        for c in cols:
            item.append(row.get(c, {}).get('value'))
        out.append(item)

    return pd.DataFrame(out, columns=cols)
