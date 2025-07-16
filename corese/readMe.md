# CORESE KB 

Our framework is based on [Corese](https://github.com/Wimmics/corese), a Software platform for the Semantic Web of Linked Data. 
The software could be deployed locally via a  [JAR software](https://github.com/Wimmics/corese/releases/download/release-4.5.0/corese-server-4.5.0.jar) and the persistancy of the KB is allowed by the tdbloader of Jena (available in this directory).

## Starting from scratch: Data base initialization
1- First download CORESE jar file 
2- Download the last version of [Jena](https://jena.apache.org/download/index.cgi) and locate the tdbloader script module
3- Download the datadump gathering all the interesting data: [https://databus.dbpedia.org/](https://databus.dbpedia.org/)
4- Load the data in CORESE using the **tdbloader** script as :
```
bash tdbloader --loc TDBLOADER_DIR FILES_DIR
```
4- configure the config.properties path in consequence

5- run the Corese server via :
```
java -Xmx10g -jar corese-server-4.5.0.jar -init "config.properties"
```
6- The KB endpoint is now accesible via  'http://localhost:8080/sparql'

## Loading a distilled KB 

To load a KB resulting from our experiment, as for example the [Kastor datadump available on Zenodo](https://zenodo.org/records/14382674): 
```
tdbloader --loc /path/for/database ...input files ... 
```
And then run the CORESE datastore with 
```
 java -Xmx10g -jar corese-server-4.5.0.jar -init "config.properties"
```
## Named Graphs

### First version 
In the [Kastor datadump available on Zenodo](https://zenodo.org/records/14382674) the data were organised as follow :
* The default named graph is the Jena default one :  <urn:x-arq:DefaultGraph>
   -> $\mathcal{K}_{\mathbb{P}(s^*)}$ graphs are tagged with a uuid (see [related SPARQL query](./sparql_queries/get_sample_K_P_s_star.sparql))
* The graphs related to the distillation process are:
    * http://ns.inria.fr/kstor/#dates_inferenced > corresponding to $\mathcal{G}^{\mathcal{R}\models}_{\mathbb{P}(s^*)}$
    * http://ns.inria.fr/kstor/#found_in_abtract > corresponding to $\mathcal{K}^{\mathcal{WR}\models}_{\mathbb{P}(s^*)}$

* The graphs related to the sample created during the experiments are 

   * http://ns.inria.fr/kstor/samples/sample_0 > corresponding to $RD^0$
   * http://ns.inria.fr/kstor/samples/sample_1 > corresponding to $RD^1$
   * http://ns.inria.fr/kstor/samples/sample_2 > corresponding to $RD^2$
   * http://ns.inria.fr/kstor/samples/sample_3 > corresponding to $RD^-$
* The datasets corrected during the light active process are stored in

    * http://ns.inria.fr/kstor/annotated_samples/sample_1 > corresponding to $RD^1+$
    * http://ns.inria.fr/kstor/annotated_samples/sample_2 > corresponding to $RD^2+$
  
### UPDATES and current structure

The default graph remains the Jena default one :  <urn:x-arq:DefaultGraph> this is where the datadump are initially loaded in the KB <br>
http://ns.inria.fr/kstor/ <br>
├── http://ns.inria.fr/kstor/shapes/$shape_name$ : contains the shapes loaded in Kastor as defined by their filename in the ~/shapes/ directory <br>
├── http://ns.inria.fr/kstor/class_randoms_id/$dbo_class$ : contains random id associated to a class focused by a shape generated during the loading of a shape in Kastor, these data are used for random sampling <br>
├── http://ns.inria.fr/kstor/inferences/$shape_name$ : contains the data infered by a rule that is associated to a given shape <br>
├── http://ns.inria.fr/kstor/wiki_md/$shape_name$ : contains the Markdown version of the Wikipedia page retrieved during the process <br>
└── http://ns.inria.fr/kstor/wikichecked/$shape_name$/abtract_md : contains the data Wikichecked based on the Markdown version of the Wikipedia page <br>

## Querying the KB

A set of basics SPARQL queries are given in [sparql_queries](./sparql_queries/) dir
