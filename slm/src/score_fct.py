import json 
import ast
import re 
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, URIRef
import urllib.parse
from unidecode import unidecode
import datefinder
from urllib.parse import unquote



def find_in_abstract(abstract,prop,value,type_prop):
    if("gYear" in type_prop):
        if(value in abstract):
            return True
        else:
            return False
        # matches = datefinder.find_dates(abstract)
        # dates=[]
        # try:
        #     for match in matches:
        #         if(match!=''):
        #             dates.append(match.strftime('%Y'))
        # except Exception as error:
        #     print(error)
        #     pass
        # if(len(dates)>0):
        #     if(value in dates):
        #         return True
        #     else: 
        #         return False
    if("date" in type_prop):
        matches = datefinder.find_dates(abstract)
        dates=[]
        try:
            for match in matches:
                if(match!=''):
                    dates.append(match.strftime('%Y-%m-%d'))
        except Exception as error:
            print(error)
            pass
        if(len(dates)>0):
            if(value in dates):
                return True
            else: 
                return False
    elif("string" in type_prop):
        if(prop=="label"):
            ok=False
            parts=value.split(" ")
            for part in parts:
                if(part.lower() in abstract.lower()):
                    ok=True 
                else:
                    ok=False
            if(ok):
                return True

        elif(value.lower() in abstract.lower()):
            return True
        else :
           if(unidecode(value.lower()) in unidecode(abstract.lower())):
               return True 
    return False

def cleanTxt(txt):
    try:
        if(txt[0]==" "):
            txt=txt[1:]
    except:
        print(txt)
    if(txt[-1]==" "):
        txt=txt[:-1]
    return txt.strip()

def cleanDecoded3(labels):
    clean=labels.replace("<s>","").replace("</s>","").replace(":"," :")
    clean=clean.replace('=" ','="').replace(": ",":").replace(' #','#').replace("< ","<").replace("</ ","</").replace("= ","=").replace('<? ','<?').replace('# ','#').replace(' >','>').replace(" <","<").replace(' =','=').replace('/ ','/').replace('/ ','/')
    # xml
    clean=clean.replace(' "/>','"/>').replace(' ">','">')
    # turtle
    #.replace(' "','"')
    #json
    clean=clean.replace(' ":"','":"')
    clean=clean.replace(":<",": <").replace(" ^","^").replace("^ ","^")
    # ntriples
    clean=clean.replace("><","> <")
    
    # date break
    clean=clean.replace(' " ',' "')
    # can break uri
    clean=clean.replace(". ",".").replace(" .",".")
    clean_last=cleanTxt(clean).strip()
    return clean_last

def cleanDecoded2(labels):
    clean=labels.replace("<s>","").replace("</s>","")
    clean=clean.replace('=" ','="').replace(" : ",":").replace(" :",":").replace(": ",":").replace(' #','#').replace("< ","<").replace("</ ","</").replace("= ","=").replace('<? ','<?').replace('# ','#').replace(' >','>').replace(" <","<").replace(' =','=').replace('/ ','/').replace('/ ','/')
    # xml
    clean=clean.replace(' "/>','"/>').replace(' ">','">')
    # turtle
    #.replace(' "','"')
    #json
    clean=clean.replace(' ":"','":"')
    clean=clean.replace(":<",": <").replace(" ^","^").replace("^ ","^")
    # ntriples
    clean=clean.replace("><","> <")
    # date break
    clean=clean.replace(' " ',' "')
    # can break uri

    clean=clean.replace(". ",".").replace(" .",".")
    clean_last=cleanTxt(clean)
    return clean_last

def cleanDecoded(list_labels):
    decoded_labels_clean = []
    for label in list_labels:
        clean=label.replace("<s>","").replace("</s>","")
        clean=label.replace('=" ','="').replace(" : ",":").replace(" :",":").replace(": ",":").replace(' #','#').replace("< ","<").replace("</ ","</").replace("= ","=").replace('<? ','<?').replace('# ','#').replace(' >','>').replace(" <","<").replace(' =','=').replace('/ ','/').replace('/ ','/')
        # xml
        clean=clean.replace(' "/>','"/>').replace(' ">','">')
        # turtle
        #.replace(' "','"')
        # date break
        clean=clean.replace(' " ',' "')
        #json
        clean=clean.replace(' ":"','":"')
        clean=clean.replace(":<",": <").replace(" ^","^").replace("^ ","^")
        # ntriples
        clean=clean.replace("><","> <")
        # can break uri
        clean=clean.replace(". ",".").replace(" .",".")


        ## ADDED TO SOLVE PARSING ERRORS
        #clean=clean.replace(" a:"," a :")
        ### ADDED BECAUSE OF MULTIPLE ESCAPE CAR
        clean=clean.replace("\\\\'", "\'")
        clean=clean.replace("\\\'", "\'")
        clean=clean.replace("\\'", "\'")
        clean=clean.replace('\\\\"', '\"')
        clean=clean.replace('\\\"', '\"')
        clean=clean.replace('\\"', '\"')
        #clean=label.strip().replace("<s>","").replace("</s>","")
        decoded_labels_clean.append(clean)        
    return decoded_labels_clean



def cleanTxtAndPrefixes(txt,prefixes):
    txt=cleanTxt(txt)
    for p in prefixes:
        txt=txt.replace(p+":","")
    return txt

def cleanEnt(txt):
    clean_t=cleanTxt(txt).replace("<","").replace(">","").replace(" ","_").replace("http://dbpedia.org/resource/","").replace("https://dbpedia.org/resource/","")
    if("%" not in clean_t):
        clean_t2=urllib.parse.quote(clean_t).replace(".","%2E")
    else:
        clean_t2=clean_t
    return cleanTxt(clean_t2)     


def validateTriple(triples,shacl_g):
    r = validate(triples, shacl_graph=shacl_g ,inference="rdfs")
    conforms, results_graph, results_text = r

    return conforms, results_text

def listToRDF(list_relations):############### MUST BE EDITED
    dbo = Namespace("http://dbpedia.org/ontology/")
    dbr = Namespace("http://dbpedia.org/resource/")
    rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    xsd=Namespace("http://www.w3.org/2001/XMLSchema#")
    person = URIRef("http://dbpedia.org/ontology/Person")
    g = Graph()
    g.bind("dbo", dbo)
    g.bind("dbr", dbr)
    g.bind("rdf", rdf)
    g.bind("rdfs", rdfs)
    g.bind("xsd", xsd)

    ent_k=list_relations[0][0]
    current_entity = URIRef(ent_k)
    g.add((current_entity,URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),person))
    for rel in list_relations:       
        prop_uri=URIRef(rel[1])
        obj_val=Literal(rel[2])
        g.add((current_entity,prop_uri,obj_val))
    
    return g

def UL_TurtleToList(txt):

    triples=txt
    list_rel=[]
    temp=triples.split(";")
    ent=""
    for l in temp:
        if('"' not in l):
            triples=l.split(" ")
            ent=triples[0]
            triples2=[ent,"type",triples[2]]
        else:
            value=re.findall(r'"(.*?)"', l)[0]
            pred=l.replace('"'+value+'"',"").replace(".","").strip()
            triples2=[ent,pred,value]
        list_rel.append(triples2)
    return list_rel
      
def TurtleSToList(txt,facto=True):
    list_rel=[]
    #print("TurtleSToList")

    if facto == True:
        temp=txt.split(";")
        #print(temp)
        subj=re.findall("(?<=:).*?(?=\s)",temp[0])[0]
        type_ = None
        for t in ['http://www.w3.org/1999/02/22-rdf-syntax-ns#type',"rdfs:type","type","a"]:
            if(" "+t+" " in  temp[0]):
                splitted=temp[0].split(" "+t+" ")
                type_=splitted[1].replace(":","")
                break
        list_pattern = r"\"\s*,\s*\""
        if (type_):
            list_rel.append([cleanEnt(subj), "type", cleanTxt(type_)])
        for i in range(1, len(temp)):
            multiples = re.findall(list_pattern, temp[i])
            if (len(multiples) > 0):
                rel = re.findall("(?<=:).*?(?=\s)", temp[i])[0]

                objs = re.findall("(?<=\")(.*)(?=\")", temp[i])[0]
                obj_list = re.split(list_pattern, objs)
                for obj in obj_list:
                    list_rel.append([cleanEnt(subj), cleanTxt(rel), cleanTxt(obj)])
            else:
                rel = re.findall("(?<=:).*?(?=\s)", temp[i])[0]
                obj = re.findall("(?<=\")(.*)(?=\")", temp[i])[0]
                list_rel.append([cleanEnt(subj), cleanTxt(rel), cleanTxt(obj)])
    else:
        temp=[t for t in txt.split(".") if len(t)>1]
        subj=re.findall("(?<=:).*?(?=\s)",temp[0])[0]
        type_ = None
        for t in ['http://www.w3.org/1999/02/22-rdf-syntax-ns#type',"rdfs:type",":type","type","a"]:
            if(t in  temp[0]):
                splitted=temp[0].split(" "+t+" ")
                type_=splitted[1].replace(":","").strip()
                break
        if(type_):
            list_rel.append([cleanEnt(subj),"type",cleanTxt(type_)])
        for i in range(1,len(temp)): 
            temp_replaced= temp[i].replace(":"+subj,"").replace(subj,"")
            rel=re.findall("(?<=:).*?(?=\s)",temp_replaced)[0].strip()
            obj=re.findall("(?<=\")(.*)(?=\")",temp_replaced)[0].strip()
            list_rel.append([cleanEnt(subj),cleanTxt(rel),cleanTxt(obj)])

    return list_rel

def FactorisedListTOList(list_):
    flat_list=[]
    for t in list_:
        if(type(t[1])==list):
            subj=t[0]
            
            for pred_list in t[1]:
                rel=pred_list[0]
                if(type(pred_list[1])==list):
                    for t3 in pred_list[1]:
                        flat_list.append([cleanEnt(subj),cleanTxt(rel),cleanTxt(t3)])
                else:
                    flat_list.append([cleanEnt(subj),cleanTxt(rel),cleanTxt(pred_list[1])])
        else:
            flat_list.append([cleanEnt(t[0]),cleanTxt(t[1]),cleanTxt(t[2])])
    return flat_list

###########"" TOCHECK"
def FactorisedTagTOList(tags): 
    flat_list=[]
    list_triples=[token for token in tags.split("<et>") if token !=""]
    for triples in list_triples:
        #triples=list_triples[0]
        subj_list=[token for token in triples.split("<subj>") if token !=""]
        for subj_comp in subj_list:
            #subj_comp=subj_list[0]
            rel_list=[token for token in subj_comp.split("<rel>") if token !=""]
            subj=rel_list[0]
             #flat_list+="<subj>"+subj
            for rel_comp in rel_list[1:]:
                #rel_comp= rel_list[1]
                rel_list2=[token for token in rel_comp.split("<obj>") if token !=""]
                relation=rel_list2[0]
               # flat_list+="<rel>"+relation
                if(len(rel_list2)==2):
                    obj=rel_list2[1]
                    flat_list.append([cleanEnt(subj),cleanTxt(relation),cleanTxt(obj)])
                else:
                    for obj in rel_list2[1:]:
                        #flat_list+="<subj>"+subj+"<rel>"+relation+"<obj>"+obj+"<et>"
                        flat_list.append([cleanEnt(subj),cleanTxt(relation),cleanTxt(obj)])
                        
        
    return flat_list

####" TOCHECK"
def toListRel(txt,format_,facto=False,grammar=None):
    #print("FORMAT >>>", format_)
    list_rel=[]
    txt=str(txt)
    txt=txt.replace("<s>","").replace("</s>","")

    # if("s>" in txt):
    #     print("HEY TRICK")
    #     txt=txt.replace("s>","")
    parsed_ok=False
    parsed=None
    try: 
        #print(format_)
        #print(facto)
        if(format_ in ["json-ld","turtle","xml","ntriples"]):
            #print("json-ld","turtle","xml","ntriples")
            if(format_=="json-ld"):
                # if(txt[0:1]!="["):
                #     txt="["+txt
                if(txt[0:1]=="["):
                    try:    
                        parsed=json.loads(txt)
                        parsed_ok=True
                    except:
                        parsed_ok=False

                parsed=parsed[0]
            else:
                if(format_=="turtle"): 
                    if(txt[0:1]=="@"):
                        parsed_ok=True
                if(format_=="xml"):
                    if(txt[0:2]=="<?"):
                        parsed_ok=True
                if(format_=="ntriples"):
                    if(txt[0:1]=="<"):
                        parsed_ok=True
            
                parsed=txt
            try:
                g1 = Graph()
                g1.parse(data=parsed, format=format_)
                t=g1.serialize(format="turtle") 
                list_rel=TurtleToList(t,False)
                parsed_ok=True
            except:
                parsed_ok=False
            #print(parsed_ok)
        elif(format_ == "list"):
            #print(">>>>>>>>>>>>>>>>>>>><<<list")
            #if(txt[0:2]=="(("):
            if(txt[0:2]=="[["):
                if(facto==True):
             #       print("factolist")
                    try:
                        #t=txt.replace("(","[").replace(")","]").replace("['",'["').replace("']",'"]').replace(",'",',"').replace("',",'",').replace(", '",',"')
                        clean_t=cleanDecoded3(txt)
                        t2=ast.literal_eval(clean_t)
                        list_rel=FactorisedListTOList(t2)
                        parsed_ok=True
                    except:
                        print("PB parsing list")
                        parsed_ok=False
                else:
                    try:
                        clean_t=cleanDecoded3(txt)
                        list_rel=ast.literal_eval(clean_t)
                        parsed_ok=True
                    except:
                        print("PB parsing list")
                        parsed_ok=False

                    # sub_list=txt.replace("')",")").replace("('","(").split('), (')
                    # for i in range(len(sub_list)):
                    #     new=sub_list[i].replace("(","").replace("\n","").replace(")","")
                    #     new=new.replace("((","").replace("))","").split("', '")
                    #     if(len(new) == 3):
                    #       list_rel_temp.append(new)
                    #     elif(len(new) != 3):
                            # parsed_ok=False
                    # if(parsed_ok):
                    #     list_rel = list_rel_temp
            #if(txt[0:2]!="((" and list_rel_temp[0:1]=="("):
            #     txt="("+txt
               
        elif(format_ == "tags"):
          #  print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>tags")
            # if(txt[0:1]!="<"):
            #     txt="<"+txt
            if(txt[0:3]=="<su"):
                #print(facto)
                if(facto==True):
                    #print("factotags")
                    clean_t=cleanDecoded3(txt)
                    list_rel=FactorisedTagTOList(clean_t)
                else:
                    parsed_ok=True
                    list_rel_temp = []

                    clean_t=cleanDecoded3(txt)
                    temp=clean_t.replace("<subj>","").replace("<rel>",";").replace("<obj>",";").split("<et>")[:-1]
                    for t in temp:
                        new=t.split(";")
                        if(len(new) == 3):
                          list_rel_temp.append(new)
                        elif(len(new) != 3):
                            parsed_ok=False
                    if(parsed_ok):
                        list_rel = list_rel_temp
        elif(format_ == "turtleUL"):
            print("turtleUL")
            txt=cleanDecoded3(txt)
            list_rel=UL_TurtleToList(txt)
            print(list_rel)
            print("-----------")
        elif(format_ == "turtleS"):############## MUST BE ADAPTED FOR OBJECTS
            triples=txt.replace("%2529","").replace("%2528","")
            triples = triples.encode('ascii', 'ignore').decode("utf-8")
            is_accepted = grammar._accept_prefix(triples)
            if(is_accepted==False):
                while ("%" in triples):
                    triples = unquote(triples)
                is_accepted = grammar._accept_prefix(triples)
            # if(txt[0:1]!=":"):
            #     txt=":"+txt

            if(is_accepted):
                #print('ACCEPTED!')
                #print(triples)
                parsed_ok = True
                txt=cleanDecoded3(txt)
                list_rel=TurtleSToList(txt,facto)
            else:
                print("NOT ACCEPTED>")
                print(triples)
                print("----")
                print(txt)
                
        
    except:
        print("ERROR DURING PARSING >",format_,facto," :")
        print(txt)
        print("-------------")
        return list_rel, parsed_ok

    if(len(list_rel)>0):
        parsed_ok=True
        for triples in list_rel:
            if(len(triples)!=3):
                parsed_pred=False  
    else:
        parsed_ok=False 
                 
    return list_rel, parsed_ok

def TurtleToList(t, facto=True):
    g1 = Graph()
    g1.parse(data=t, format="turtle")
    prefixes=[]
    for ns_prefix, namespace in g1.namespaces():
        prefixes.append(ns_prefix)
    
    splitted = t.split("\n")
    new_=[]
    for split in splitted:
        if("prefix" not in split and len(split.strip())>2):
                if("^^" in split):
                    first=split.split("^^")
                    txt=first[0]
                    if(split[-1] in [".",";",","]):
                        txt+=" "+split[-1]
                    new_.append(txt)
                else:
                    new_.append(split)
    
    resp= "\n".join(new_).replace(" a "," type ")+"\n".strip()
    
    list_container=[]
    triples_list=resp.split(".\n")
    
    for triples in triples_list:
        if(";\n" in triples):
            prop_list=triples.split(";\n")
            subj=prop_list[0].split(" ")[0]
            
            
            temp1=[]
            for prop in prop_list :
                
                sublist=False
                
                prop2=prop.replace(subj,"")
                subj2=cleanTxtAndPrefixes(cleanEnt(subj),prefixes)
                if(",\n" in prop2):
                    
                    object_list=prop2.strip().split(",\n")
                    
                    if(len(object_list)>0):
                        sublist=True
                        prop_name=object_list[0].split(" ")[0]
                        temp2=[]
                        for obj in object_list :
                            prop_val=obj.replace(prop_name,"").replace('"',"").replace('.',"").strip()
                            if(facto==True):
                                temp2.append(cleanTxtAndPrefixes(prop_val,prefixes))
                            else:
                                list_container.append([subj2,cleanTxtAndPrefixes(prop_name,prefixes),cleanTxtAndPrefixes(prop_val,prefixes)])
                        if(facto==True):
                             temp1.append([cleanTxtAndPrefixes(prop_name,prefixes),temp2])
                    else:
                        sublist=False
                        
                if(sublist==False):
                    object_list=[token for token in prop2.split(" ") if token not in [""," ",",",".",";"]]
                    prop_name=object_list[0]
                    prop_val=prop2.replace(prop_name,"").replace('"',"").replace('.',"").replace('\n',"").strip()
                    
                    if(facto==True):
                        temp1.append([cleanTxtAndPrefixes(prop_name,prefixes),cleanTxtAndPrefixes(prop_val,prefixes)])
                    else:
                        list_container.append([subj2,cleanTxtAndPrefixes(prop_name,prefixes),cleanTxtAndPrefixes(prop_val,prefixes)])
            
            if(facto==True):
                
                subj2=cleanTxtAndPrefixes(cleanEnt(subj),prefixes)
                list_container.append([subj2,temp1])

            
    return list_container


def list_ToRDF2(list_relations,relations_map,shacl_g):
    ent_k=list_relations[0][0]
    typ_ent=list_relations[0][2]
    names_spaces=shacl_g.namespaces()
    
    g = Graph()
    dbr = Namespace("http://dbpedia.org/resource/")
    g.bind("dbr", dbr)
    for ns_prefix, namespace in names_spaces:
        current_ns=Namespace(str(namespace))
        g.bind(ns_prefix, current_ns)
    
    current_entity = URIRef("http://dbpedia.org/resource/"+cleanEnt(ent_k))
        
    triple_type = URIRef("http://dbpedia.org/ontology/"+typ_ent)
        
    
    g.add((current_entity,URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),triple_type))
    
    for rel in list_relations:       
        if(rel[1] != "type" and rel[1] != "a" and rel[1] in relations_map.keys() ):
            
            prop_uri=relations_map[rel[1]]["ns"]
            v=rel[2]
            obj_val=Literal(v, datatype=relations_map[rel[1]]["dt"])
            g.add((current_entity,prop_uri,obj_val))
            
    return g