# MLcites

## Repository Overview
This repository contains code to find authors, rough affiliations and the number of citations of 
papers in NeurIPS (2014 to 2018) and ICML (2017 and 2018).

It also contains the results of collecting this data (run on March 31st, 2019), and a [jupyter notebook](https://github.com/rubai5/MLcites/blob/master/Paper_Statistics_Analysis.ipynb) showing how to use the data, as well as some of the simple analyses that can be done (number of accepted papers, top cited papers, academia/industry split). 

### Example Results: Accepted Papers, Papers with Citation Data Successfully Scraped, Top Cited Papers
The [jupyter notebook](https://github.com/rubai5/MLcites/blob/master/Paper_Statistics_Analysis.ipynb) contains more of these, but some of the first statistics one can compute is trends in total accepted papers and how many papers we can find citation data for:

![alt text](https://github.com/rubai5/MLcites/blob/master/Accepted_Paper_Statistics.png "NeurIPS Accepted Papers and Papers with Citations Data")

We can also take a look at what some of the top cited papers are to get some sense of ideas the community has found especially exciting. Remember however that this comes from our data, so it's possible that there are a few papers missing (ones for which we didn't find citation data) from the list.

![alt text](https://github.com/rubai5/MLcites/blob/master/Most_Cited_Papers.png "The top cited papers from NeurIPS 2014, 2015, 2016.")


## The Data
**Disclaimer:** The results of the scraping process are **noisy** with some papers are missing citation data, and author affiliations being computed in an efficient (but noisy) way. The method used for scraping the data, and some of the approximations made, is described in detail below.

The data (from running the scraper on March 31st 2019) is in files of form `results_<conference name>_<year>.p` -- these correspond to papers from that conference in that year. 

### Scraping Method Overview
The citations are scraped from Google Scholar, which only allows _authors_ to be searched automatically. Therefore, after extracting all of the paper and author names from the conference accepted paper list, the script searches up each paper author in order, and, going through their Google Scholar publication list, tries to see if they have a publication matching the conference paper, via a simple strings being equal heuristic. (The number of papers to search also has to be specificed manually, and to trade off between accuracy and speed, the script looks through the 200 most recent papers of the author.) 

If a match is found, the script updates the paper with the citation count and the found author's affiliation. To save time, the script does not look up all the authors of a paper, only the minimum number needed to find a citation. Note that the affiliation of the author is their _current_ affiliation, not necessarily the affiliation they had when they wrote the paper. The jupyter notebook (and generated plots) offer some preliminary breakdowns of the academia/industry split, using this (noisy) affiliation. 

## How to Scrape the Data
The code to scrape the data is written for Python 3, and besides standard packages such as pandas, relies on the [scholarly](https://github.com/OrganicIrradiation/scholarly) package. **Note:** unfortunately, several functions in scholarly don't seem to be working anymore, due to changes in Google Scholar. We will make some edits to the installation to ensure it can retrieve author information. 

Instructions for Scraping the Data:
1. Install [scholarly](https://github.com/OrganicIrradiation/scholarly) and its dependencies.
2. In the `Author` class in `/usr/local/lib/python3.5/dist-packages/scholarly.py`, edit all occurences of `gsc_oai_<text>` to `gs_ai_<text>`.
3. Run the scraping script: e.g. `python3 get_statistics_allyears.py --conference=NeurIPS --year=2016`


## Extensions
It should be relatively easy to adapt this script to also look up papers from other conferences, e.g. ICLR, CVPR, ACL and others: the code is split into functions for dealing with the page of accepted papers listed on the conference website, and functions to seach for matching author information on Google Scholar and retrive affiliations and citations.

Google Scholar is pretty thorough in keeping track of citations, but [Semantic scholar](https://api.semanticscholar.org/) has an easy to use API, which could also potentially be used for extensions of this kind of analysis.
