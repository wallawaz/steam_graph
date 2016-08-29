import os
import requests
import sys
import os
from bs4 import BeautifulSoup

current_dir = os.path.dirname(os.path.realpath(__file__))
current_dir = current_dir.split("/")
parent_dir = "/".join(current_dir[:-1])

data_dir = parent_dir + "/data/"
filename = data_dir + "iso_raw.html"

def grab_page():
    wikipedia_page = "https://en.wikipedia.org/wiki/ISO_3166-1"
    response = requests.get(wikipedia_page)
    if response.status_code != 200:
        sys.exit(1)

    soup = BeautifulSoup(response.text, "html.parser")

    with open(filename, "w") as out:
        out.write(str(soup))

    return soup

def extract(tds):
    iso_codes = {}
    counter = 0
    country = None
    for td in tds:
        counter += 1
        if counter == 1:
            country = td.text
            iso_codes[country] = ""
        elif counter == 2:
            iso_codes[country] = td.text
        elif counter > 2 and counter < 5:
            pass
        else:
            counter = 0
            country = None

    return iso_codes

if __name__ == "__main__":
    if os.path.exists(filename):
        print "reading from " + filename
        lines = open(filename, "r").readlines()
        lines = "".join(lines)
        soup = BeautifulSoup(lines, "html.parser")
    else:
        soup = grab_page()

    tds = soup.find_all("td")
    iso_codes = extract(tds)
    iso_codes = {k: v for k, v in iso_codes.items() if len(v) == 2}
    with open(data_dir + "iso_codes.py", "w") as out:
        out.write("iso_codes = {")
        out.write("\n")
        for country, code in iso_codes.items():
            out.write('    "{country}": "{code}",'.format(country=country.encode("utf-8"), code=code))
            out.write("\n")
        out.write("}")
