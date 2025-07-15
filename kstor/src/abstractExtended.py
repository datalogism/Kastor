
import requests
import bs4
import src.rdf_synthax_fct as rdf_f
from markdownify import markdownify
import re
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo

@on_exception(expo, RateLimitException, max_tries=1)
@limits(calls=150, period=1)
def getAbstractMD(entity, usr_agent_data):
    url_wikiapi = "https://en.wikipedia.org/api/rest_v1/page/html/"
    data = {"redirect": "true", "User-Agent": usr_agent_data}
    res = requests.get(url_wikiapi + entity, data)

    res_all = ""

    if (res.status_code == 200):
        content = res.text
        bs_html = bs4.BeautifulSoup(content, 'html.parser')
        disamb = bs_html.find("div", {"id": "_disambigbox"})
        if (disamb is None):
            sections = bs_html.select("section")
            abstract = sections[0]
            links = abstract.findAll("a")
            for link in links:
                del link["title"]
            paragraphs = abstract.select("p")
            res_all = ""
            for para in paragraphs:
                # found_ipa0 = para.findAll("span[class*='IPA']")
                class_to_delete = ["ext-phonos", "IPA", "IPA-label", "Inline-Template", "reference"]
                para_str = str(para)
                for class_ in class_to_delete:
                    found_ipa_content = para.findAll(["span", "sup"], {"class": class_})
                    if (found_ipa_content):
                        for ipa_content in found_ipa_content:
                            para_str = para_str.replace(str(ipa_content), "")
                para_str = para_str.replace("(  ;", "(")

                md_p = markdownify(str(para_str))
                #replaced = md_p.replace("*", "")  ### DELETE *
                replaced = md_p.replace("](./", "](:")  #### TO ttl light
                res_all += replaced

            markdown_link_rgx = r'\[(.*?)\]\(.*?\)?\)'
            markdown_links = [x.group() for x in re.finditer(markdown_link_rgx, res_all)]
            delete_list = []
            for links in markdown_links:
                label = re.findall(r'\[(.*?)\]', links)
                link = re.findall(r'\(\:(.*?\)?)?\)', links)
                if ("redlink=1" in links):
                    delete_list.append([links, label[0]])
            for delete in delete_list:
                res_all = res_all.replace(delete[0], delete[1])
            res_all=res_all.replace("\n","")

    if (res.status_code == 404):
        res_all = ""
    return res_all
@on_exception(expo, RateLimitException, max_tries=1)
@limits(calls=150, period=1)
def getAbstractMD2(entity,revision_id, usr_agent_data):
    print("here")
    url_wikiapi = "https://en.wikipedia.org/api/rest_v1/page/html/"
    data = {"redirect": "true", "User-Agent": usr_agent_data}
    res = requests.get(url_wikiapi + entity+"/"+str(revision_id), data)
    print("end request")
    res_all = ""

    if (res.status_code == 200):
        content = res.text
        bs_html = bs4.BeautifulSoup(content, 'html.parser')
        disamb = bs_html.find("div", {"id": "_disambigbox"})
        if (disamb is None):
            sections = bs_html.select("section")
            abstract = sections[0]
            links = abstract.findAll("a")
            for link in links:
                del link["title"]
            paragraphs = abstract.select("p")
            res_all = ""
            for para in paragraphs:
                # found_ipa0 = para.findAll("span[class*='IPA']")
                class_to_delete = ["ext-phonos", "IPA", "IPA-label", "Inline-Template", "reference"]
                para_str = str(para)
                for class_ in class_to_delete:
                    found_ipa_content = para.findAll(["span", "sup"], {"class": class_})
                    if (found_ipa_content):
                        for ipa_content in found_ipa_content:
                            para_str = para_str.replace(str(ipa_content), "")
                para_str = para_str.replace("(  ;", "(")

                md_p = markdownify(str(para_str))
                #replaced = md_p.replace("*", "")  ### DELETE *
                replaced = md_p.replace("](./", "](:")  #### TO ttl light
                res_all += replaced

            markdown_link_rgx = r'\[(.*?)\]\(.*?\)?\)'
            markdown_links = [x.group() for x in re.finditer(markdown_link_rgx, res_all)]
            delete_list = []
            print("--------------")
            for links in markdown_links:
                label = re.findall(r'\[(.*?)\]', links)
                link = re.findall(r'\(\:(.*?\)?)?\)', links)
                if ("redlink=1" in links):
                    delete_list.append([links, label[0]])
                elif(len(link)>0):
                    encoded=rdf_f.cleanURL(link[0])
                    res_all=res_all.replace("(:"+link[0]+")", "(:"+encoded+")")



            for delete in delete_list:
                res_all = res_all.replace(delete[0], delete[1])
            res_all=res_all.replace("\n","")

    if (res.status_code == 404):
        res_all = ""
    return res_all

