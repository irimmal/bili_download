#!usr/bin/env python3

import requests
import json
from time import sleep
import random
import pandas as pd
import json

def delay_request():
    delay_seconds = random.uniform(1, 3)
    sleep(delay_seconds)

api = "https://api.vndb.org/kana/vn"
max_page = int(input("please input the max page: "))
query_template = {
    "filters": [],
    "fields": "title, alttitle, aliases, tags.name, released, id, length_minutes, votecount, rating, image.url",
    "sort": "votecount",
    "reverse": True,
    "results": 100,
    "page": 1,
    "user": None,
    "count": False,
    "compact_filters": False,
    "normalized_filters": False
}

columns0 = ["title", "alttitle", "aliases", "tags", "released", "id", "length_minutes", "votecount", "rating", "image"]
columns = ["rank"] + columns0
data_df = pd.DataFrame(columns=columns)

i = 0
for page in range(max_page):
    page = page + 1
    print("now is page: ",page)
    query_template["page"] = page
    delay_request()
    response = requests.post(api, json=query_template)
    try:
      data = response.json()
      results = data["results"]
      for result in results:
        i += 1
        if result["aliases"] != []:
          result["aliases"] = "\n".join([aliase for aliase in result["aliases"]])
        else:
          result["aliases"] = " "
        result["tags"] = ", ".join([tag["name"] for tag in result["tags"] if "name" in tag])
        result["image"] = result["image"]["url"]
        data_df.loc[i] = result
    except:
       continue

df_sorted = data_df.sort_values(by='votecount', ascending=False)
df_sorted['rank'] = df_sorted['votecount'].rank(method='min',ascending=False)

df_sorted.to_excel('data.xlsx', index=False)