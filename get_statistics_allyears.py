import scholarly
from bs4 import BeautifulSoup
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import pickle
import argparse
import requests
import itertools


# global definition of Google Scholar's author page, sorted by date
_AUTHPAGE = (
    "/citations?hl=en&user={0}&view_op=list_works&sortby=pubdate&cstart=0&pagesize=200"
)


def get_html(url):
    # gets the raw html for the webpage
    return urlopen(url)


def get_name_and_authors(html):
    # takes in html, parses with beautiful soup
    # adds paper name/author names to dataframe
    output = pd.DataFrame(columns=["name", "authors", "citations", "affiliation"])

    soup = BeautifulSoup(html, "html.parser")
    clumped_tags = soup.find_all("div", attrs={"class": "maincard narrower Poster"})
    for t in clumped_tags:
        pname = t.find("div", attrs={"class": "maincardBody"}).text.strip()
        araw = t.find("div", attrs={"class": "maincardFooter"}).text.strip()
        anames = araw.split(" · ")
        output = output.append({"name": pname, "authors": anames}, ignore_index=True)

    return output


def author_paper_citations(df, adata, pname, i):
    # helper function to try and get citations for one paper
    updated = False
    url = _AUTHPAGE.format(requests.utils.quote(adata["scholar_id"]))
    soup = scholarly._navigator.Navigator()._get_soup(url)

    clumped_tags = soup.find_all("tr", attrs={"class": "gsc_a_tr"})
    for t in clumped_tags:
        cname = (
            t.find("a", attrs={"class": "gsc_a_at"})
            .text.strip()
            .lower()
            .replace(" ", "")
        )
        if cname == pname:
            # try to find citations
            try:
                cites = t.find("a", attrs={"class": "gsc_a_ac gs_ibl"}).text.strip()
                if cites == "":
                    cites = 0
                else:
                    cites = int(cites)
                df["citations"][i] = cites
                df["affiliation"][i] = adata["affiliation"]
                updated = True
            except AttributeError:
                if t.find("a", attrs={"class": "gsc_a_ac gs_ibl"}) == None:
                    print("couldn't find citations for, author", adata["name"])
                    print("source paper name, found name", pname, cname)
            break
    return df, updated


def get_citations(df):
    # get paper citations from Google Scholar using paper and author names
    for i in range(len(df)):
        praw = str(df["name"][i])
        pname = praw.lower().replace(" ", "")
        authors = df["authors"][i]
        print("step , paper name, authors", i, praw, authors)

        for author in authors:
            try:
                adata = next(scholarly.scholarly.search_author(author))
                print("Found author data", adata["name"])
                df, updated = author_paper_citations(df, adata, pname, i)
            except StopIteration:
                continue
            if updated:
                print(
                    "Successfully updated df for paper, with author",
                    pname,
                    adata["name"],
                )
                break
        print("")
    return df


if __name__ == "__main__":

    # parse command line args
    """
    Example command:
    python get_statistics_allyears.py --year 2019 2020 --conference NeurIPS ICML
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", help="Conference year", default="2018", nargs="+")
    parser.add_argument(
        "--conference", help="Either ICML or NeurIPS", default="NeurIPS", nargs="+"
    )
    args = parser.parse_args()

    year_confs = itertools.product(args.year, args.conference)

    def get(year_conference):
        year, conference = year_conference
        if conference == "NeurIPS":
            _URL = "https://nips.cc/Conferences/%s/Schedule" % str(year)
        if conference == "ICML":
            _URL = "https://icml.cc/Conferences/%s/Schedule" % str(year)

        html = get_html(_URL)
        df = get_name_and_authors(html)
        df = get_citations(df)

        with open("./results_%s_%s.p" % (conference, year), "wb") as f:
            pickle.dump(df, f)

    with ThreadPoolExecutor(max_workers=10) as pool:
        elevations = list(pool.map(get, year_confs))
