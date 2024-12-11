# CORESE KB 

Our framework is based on [Corese](https://github.com/Wimmics/corese), a Software platform for the Semantic Web of Linked Data. 
The software could be deployed locally via a  [JAR software](https://github.com/Wimmics/corese/releases/download/release-4.5.0/corese-server-4.5.0.jar) and the persistancy of the KB is allowed by the tdbloader of Jena (available in this directory).

## Starting from scratch: Data base initialization
1- First download CORESE jar file and the tdbloader script

2- Download the datadump gathering all the interesting data: [https://databus.dbpedia.org/cringwald/collections/kstor](https://databus.dbpedia.org/cringwald/collections/kstor)

3- Load the data via the **tdbloader** as :
```
bash tdbloader --loc TDBLOADER_DIR FILES_DIR
```
4- configure the config.properties path in consequence

5- run the Corese server via :
```
java -Xmx10g -jar corese-server-4.5.0.jar -init "config.properties"
```
6- The KB endpoint is now accesible via  'http://localhost:8080/sparql'

## Loading the distilled KB of the experiments

To load the KB resulting from our experiment, please first load the [Kastor datadump available on Zenodo](https://zenodo.org/records/14382674): 
```
tdbloader --loc /path/for/database ...input files ... 
```
And then run the CORESE datastore with 
```
 java -Xmx10g -jar corese-server-4.5.0.jar -init "config.properties"
```
## Named Graphs
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

## Querying the KB

A set of basics SPARQL queries are given in [sparql_queries](./sparql_queries/) dir
