# CORESE KB 

Our framework is based on [Corese](https://github.com/Wimmics/corese), a Software platform for the Semantic Web of Linked Data. 
The software could be deployed locally via a  [JAR software](https://github.com/Wimmics/corese/releases/download/release-4.5.0/corese-server-4.5.0.jar) and the persistancy of the KB is allowed by the tdbloader of Jena.

## Data base initialization
1- First download CORESE jar file and the tdbloader script

2- Download the datadump gathering all the interesting data: [https://databus.dbpedia.org/cringwald/collections/kstor](https://databus.dbpedia.org/cringwald/collections/kstor)

3- Load the data via the **tdbloader** as :
> bash tdbloader --loc TDBLOADER_DIR FILES_DIR

4- configure the config.properties path in consequence

5- run the Corese server via :
>   java -Xmx10g -jar corese-server-4.5.0.jar -init "config.properties"

