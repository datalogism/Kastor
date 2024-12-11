from argparse import ArgumentParser
import logging

from rdflib import Graph
import src.class_signatures as cs
import src.triple_shapes as ts

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--shape_file_path", default=None)
    args = parser.parse_args()

    sparql_ep = 'http://localhost:8080/sparql'
    if args.shape_file_path:
        shape = Graph()
        shape.parse(args.shape_file_path)
        type_triples = ts.getShapeType(shape)
        logging.info("START uuid creation process")
        res = cs.CreateUUIDClassEntities(type_triples, sparql_ep)
        logging.info("END uuid creation process")
    else:
        logging.error("Shape file path not provided")
