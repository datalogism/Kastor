import re 
import json
from rdflib import Graph


def reOrderNtriples(t):
    list_orig = t.split(".\n")
    type_t = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    label_t = "http://www.w3.org/2000/01/rdf-schema#label"
    new_list = []
    for elem in list_orig:
        if(type_t in elem):
            new_list.append(elem)
            break
    for elem in list_orig:
         if(label_t in elem):
             new_list.append(elem)
             break
    
    for elem in list_orig:
         if(elem not in new_list):
             new_list.append(elem)
    new_triples=".\n".join( new_list)
    return new_triples
             
def simplifyTutle(t,datatype=False, inLine=False, facto=True):
    g1 = Graph()
    g1.parse(data=t, format="turtle")
    if(facto==False):
        t=g1.serialize(format="ntriples") 
        for ns_prefix, namespace in g1.namespaces():
           t=t.replace(namespace,"")
        t=t.replace("<",":")
    for ns_prefix, namespace in g1.namespaces():
       t=t.replace(namespace,"")
      
    test=t 
    test=test.replace("https://dbpedia.org/resource/","dbr:").replace("http://dbpedia.org/resource/","dbr:")
    test=test.replace("\n\n","\n")
    splitted=test.split("\n")
    new_=""
    for split in splitted:
        if("prefix" not in split and len(split.strip())>2):

                if("^^" in split and datatype==False):
                    first=split.split("^^")
                    new_=new_+"\n"+first[0]+" "+first[1].split(" ")[1]
                else:
                    new_=new_+"\n"+split
    #test=re.sub("@prefix .{2,4}: <(?:\"[^\"]*\"['\"]*|'[^']* '['\"]*|[^'\">])+> .\\n","",test)
    
    new2=re.sub(" .{2,4}:"," :",new_).replace("    ","   ").replace("\n:",":").replace("dbr","")
    new2=new2.replace("\n<","").replace("<","").replace(">","").replace(".\n",".").replace("  .:",".:").replace(" .:",". :")
    if(inLine):
        new2=re.sub(r"[\n\t]*", "",new2).replace("   "," ").replace(" ;",";").strip()
    return new2

def TurtleSToList(txt,facto=True):
    list_rel=[]
    if facto == True:
        temp=txt.split(";")
        subj=re.findall("(?<=:).*?(?=\s)",temp[0])[0]
        type_ = None
        for t in ['http://www.w3.org/1999/02/22-rdf-syntax-ns#type',"rdfs:type","type","a"]:
            if(" "+t+" " in  temp[0]):
                splitted=temp[0].split(" "+t+" ")
                type_=splitted[1].replace(":","")
                break
        list_pattern=r"\"\s*,\s*\""
        if(type_):
            list_rel.append([cleanEnt(subj),"type",cleanTxt(type_)])
        for i in range(1,len(temp)): 
            multiples=re.findall(list_pattern,temp[i])
            if(len(multiples)>0):
                rel=re.findall("(?<=:).*?(?=\s)",temp[i])[0]
                
                objs=re.findall("(?<=\")(.*)(?=\")",temp[i])[0]
                obj_list=re.split(list_pattern,objs)
                for obj in obj_list:
                    list_rel.append([cleanEnt(subj),cleanTxt(rel),cleanTxt(obj)])
            else:
                rel=re.findall("(?<=:).*?(?=\s)",temp[i])[0]
                obj=re.findall("(?<=\")(.*)(?=\")",temp[i])[0]
                list_rel.append([cleanEnt(subj),cleanTxt(rel),cleanTxt(obj)])
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
                        flat_list.append([subj,rel,t3])
                else:
                    flat_list.append([subj,rel,pred_list[1]])
        else:
            print(t)
            flat_list.append([t[0],t[1],t[2]])
    return flat_list

def FactorisedTagTOTag(tags): 
    flat_list=""
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
                    flat_list+="<subj>"+subj+"<rel>"+relation+"<obj>"+obj+"<et>"
                else:
                    for obj in rel_list2[1:]:
                        flat_list+="<subj>"+subj+"<rel>"+relation+"<obj>"+obj+"<et>"
                        
        
    return flat_list
    
def TurtleToTag(t, facto=True):
    to_list=TurtleToList(t, facto)
    list_=""
    if(facto==False):
        for t in to_list:
            list_=list_+"<subj>"+t[0]+"<rel>"+t[1]+"<obj>"+t[2]+"<et>"
    else:
        for t in to_list:
            if(type(t[1])==list):
                print("TRIPLE LIST")
                list_=list_+"<subj>"+t[0]
                
                for pred_list in t[1]:
                    list_ += "<rel>"+pred_list[0]
                    if(type(pred_list[1])==list):
                        print("PREDLIST")
                        for t3 in pred_list[1]:
                            list_=list_+"<obj>"+t3
                    else:
                        list_=list_+"<obj>"+pred_list[1]
            else:
                print(t)
                list_=list_+"<subj>"+t[0]+"<rel>"+t[1]
                        
                        
            list_=list_+"<et>"
    return list_