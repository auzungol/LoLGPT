import os
import re
import time
import requests
from config import CHAMPION_FOLDER
from regions import detect_region, CHAMPION_REGION_OVERRIDES

DDRAGON_BASE = "https://ddragon.leagueoflegends.com"


def get_latest_version() -> str:
    resp = requests.get(f"{DDRAGON_BASE}/api/versions.json")
    resp.raise_for_status()
    return resp.json()[0]


def get_champion_list(version: str) -> list[str]:
    url = f"{DDRAGON_BASE}/cdn/{version}/data/en_US/champion.json"
    resp = requests.get(url)
    resp.raise_for_status()
    return list(resp.json()["data"].keys())


def get_champion_detail(version: str, champion_id: str) -> dict:
    url = f"{DDRAGON_BASE}/cdn/{version}/data/en_US/champion/{champion_id}.json"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()["data"][champion_id]


def clean_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def format_champion_txt(data: dict, champion_id: str) -> str:
    name = data["name"]
    title = data["title"]
    lore = clean_html(data["lore"])
    tags = ", ".join(data.get("tags", []))
    partype = data.get("partype", "None")

    region = CHAMPION_REGION_OVERRIDES.get(champion_id.lower()) or detect_region(lore)

    lines = [
        f"{name}, the {title}",
        "",
        lore,
        "",
        f"Role: {tags}",
        f"Region: {region}",
        f"Resource: {partype}",
        "",
        f"Passive - {data['passive']['name']}: {clean_html(data['passive']['description'])}",
        "",
    ]

    ability_letters = ["Q", "W", "E", "R"]
    for letter, spell in zip(ability_letters, data["spells"]):
        lines.append(f"{letter} - {spell['name']}: {clean_html(spell['description'])}")
        lines.append("")

    return "\n".join(lines)


def fetch_all_champions():
    os.makedirs(CHAMPION_FOLDER, exist_ok=True)

    version = get_latest_version()
    print(f"Data Dragon sürümü: {version}")

    champion_ids = get_champion_list(version)
    print(f"{len(champion_ids)} şampiyon bulundu.")

    for i, champ_id in enumerate(champion_ids, 1):
        detail = get_champion_detail(version, champ_id)
        text = format_champion_txt(detail, champ_id)

        filepath = os.path.join(CHAMPION_FOLDER, f"{champ_id.lower()}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"  [{i}/{len(champion_ids)}] {champ_id} kaydedildi.")
        time.sleep(0.05)

    print("Tüm şampiyonlar indirildi.")


if __name__ == "__main__":
    fetch_all_champions()