import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import re
import sys

def scrape_horse_data(horse_id: str):
    result = {"id": horse_id}
    #! TOPページ
    url = f"https://db.netkeiba.com/horse/{horse_id}"
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')
    result["馬名"] = soup.select_one(".horse_title h1").text
    result["英名"] = soup.select_one(".horse_title .eng_name").text.strip()
    result["現役"], result["性別"], result["毛色"] = soup.select_one(".horse_title .txt_01").text.split()
    # テーブルから情報取得
    _dict = {row.select_one("th").text.strip(): row.select_one("td").text.strip() for row in soup.select(".db_prof_table tr")}
    result["生年月日"] = datetime.datetime.strptime(_dict["生年月日"], "%Y年%m月%d日")
    result["調教師"] = re.sub(r"\(.+\)", "", _dict["調教師"]).strip()
    result["馬主"] = _dict["馬主"]
    result["生産者"] = _dict["生産者"]
    result["産地"] = _dict["産地"]

    #! 戦績ページ
    url = f"https://db.netkeiba.com/horse/result/{horse_id}"
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')
    s = str(soup.select_one(".db_h_race_results"))
    df = pd.read_html(s)[0]
    df = df.set_axis([l.replace(" ", "") for l in df.columns], axis="columns")
    # 後処理
    df.drop(["映像", "馬場指数", "ﾀｲﾑ指数", "厩舎ｺﾒﾝﾄ", "備考"], axis="columns", inplace=True)
    # 数値変換
    for col in ["頭数", "枠番", "馬番", "オッズ", "人気", "斤量", "着順", "着差", "上り", "賞金"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    result["戦績"] = df

    #! 血統ページ
    url = f"https://db.netkeiba.com/horse/ped/{horse_id}"
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')
    blood_table_html = soup.select_one(".blood_table.detail")
    peds = {}
    for i in range(1,6):
        rels = [f"{n:05b}"[-i:].replace("0","父").replace("1","母") for n in range(2**i)]
        if i == 5:
            horse_htmls = blood_table_html.select(f"[height='20']")
        else:
            horse_htmls = blood_table_html.select(f"[rowspan='{32//(2**i)}']")
        for rel, horse_html in zip(rels, horse_htmls):
            peds[rel] = horse_html.select_one("a").text.strip().split("\n")[0]
    result["血統"] = peds.copy()
    
    return result


if __name__ == "__main__":
    horse_id = sys.argv[1]
    result = scrape_horse_data(horse_id)