from scholarly import scholarly
from bs4 import BeautifulSoup
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from argparse import ArgumentParser
import pandas as pd
import itertools


def year_type(string):
    """
    Parses '1,3' into [1,3]
    Parses 2-4' into [2,3,4]
    Parses '2' into [2]
    """
    if "," in string:
        years = string.split(",")
    elif "-" in string:
        start, end = map(int, string.split("-"))
        years = list(range(start, end + 1))
    else:
        years = string.split()
    return years


def get_html(url):
    """Returns the raw html for the given url"""
    return urlopen(url)


def get_url(conference: str, year: int):
    """Returns the DBLP url for the given conference and year"""
    base_url = "https://dblp.org/db/conf/{}/{}.html"
    conference = conference.lower()
    if conference in {"neurips", "nips"}:
        conference = "nips"
        # name changed in dblp starting 2020
        if year > 2019:
            conference_id = f"neurips{year}"
        else:
            conference_id = f"nips{year}"
    else:
        conference_id = f"{conference}{year}"
    dblp_url = base_url.format(conference, conference_id)
    return dblp_url


def get_papers(dblp_html):
    soup = soup = BeautifulSoup(dblp_html, "html.parser")
    cites = soup.body.find_all("cite")
    cites = cites[1:]  # skip the first entry which is the proceeding itself
    papers = []
    for cite in cites:
        authors_and_titles = cite.find_all(itemprop="name")
        # title is the last sibling. rest are authors
        author_tags = authors_and_titles[:-1]
        authors = [a.contents[0] for a in author_tags]
        title = authors_and_titles[-1]
        # sometimes titles have additional html tags within them, like italicization
        # so we must expand them and then join

        def expand(tag):
            while hasattr(tag, "contents"):
                tag = tag.contents[0]
            return tag

        title = "".join([expand(c) for c in title.children])
        title = title.rstrip(".")  # DBLP ends titles with a period, so we remove

        papers.append({"title": title, "authors": authors})
    return papers


def get_paper_data(papers, fields=("abstract", "num_citations")):
    papers = dict(papers)  # make a copy
    for paper in papers:
        title = papers["title"]
        gs_result = scholarly.search_single_pub(title)
        for field in fields:
            papers[field] = gs_result[field]
    return papers


if __name__ == "__main__":

    # parse command line args
    """
    Example command:
    python get_statistics_allyears.py --year 2019 2020 --conference NeurIPS ICML
    """
    parser = ArgumentParser()
    parser.add_argument(
        "--year", help="Conference year", type=year_type,
    )
    parser.add_argument(
        "--conference", help="Conference name", default="NeurIPS", nargs="+", type=str,
    )
    parser.add_argument(
        "--get-data", action="store_true", help="Get paper data from Google Scholar"
    )
    args = parser.parse_args()

    year_confs = itertools.product(args.year, args.conference)

    data_dir = Path("./data/")
    if not data_dir.exists():
        data_dir.mkdir()

    def get(year_conference):
        year, conference = year_conference

        url = get_url(conference, year)
        html = get_html(url)
        papers = get_papers(html)
        # df_papers = pd.DataFrame(papers).explode("authors").set_index("title")
        df_papers = pd.DataFrame(papers).set_index("title")
        df_papers = df_papers.rename(columns={"authors": "author"})
        df_papers.to_csv(data_dir / f"papers-{conference}-{year}.csv")

        if args.get_data:
            paper_data = get_paper_data(papers)
            df_paper_data = pd.DataFrame(paper_data)
            df_paper_data.to_csv(data_dir / f"paper_data-{conference}-{year}.csv")

    with ThreadPoolExecutor(max_workers=10) as pool:
        elevations = list(pool.map(get, year_confs))
