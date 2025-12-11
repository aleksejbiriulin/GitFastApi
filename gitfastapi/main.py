from fastapi import FastAPI, Query
import csv
import math
import os
import requests

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "Hello, world!"}


@app.get("/repos/save")
def save_repositories(
    limit: int = Query(..., gt=0),
    offset: int = Query(0, ge=0),
    lang: str = Query(..., alias="lang"),
    stars_min: int = 0,
    stars_max: int | None = None,
    forks_min: int = 0,
    forks_max: int | None = None,
):
    stars_part = f"{stars_min}..{stars_max}" if stars_max is not None else f">={stars_min}"
    forks_part = f"{forks_min}..{forks_max}" if forks_max is not None else f">={forks_min}"
    q = f"language:{lang} stars:{stars_part} forks:{forks_part}"

    page_size = 100
    first_page = offset // page_size + 1
    first_page_offset = offset % page_size
    pages_needed = math.ceil((first_page_offset + limit) / page_size)

    items: list[dict] = []
    fetched = 0

    for page in range(first_page, first_page + pages_needed):
        params = {
            "q": q,
            "sort": "stars",
            "order": "desc",
            "per_page": page_size,
            "page": page,
        }
        resp = requests.get(GITHUB_SEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        page_items = data.get("items", [])
        if page == first_page and first_page_offset:
            page_items = page_items[first_page_offset:]

        for repo in page_items:
            if fetched >= limit:
                break
            items.append(repo)
            fetched += 1

        if fetched >= limit or not page_items:
            break

    os.makedirs("static", exist_ok=True)
    csv_path = os.path.join("static", "repos.csv")

    fieldnames = [
        "id",
        "name",
        "full_name",
        "html_url",
        "description",
        "language",
        "stargazers_count",
        "forks_count",
        "created_at",
        "updated_at",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for repo in items:
            writer.writerow(
                {
                    "id": repo.get("id"),
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "html_url": repo.get("html_url"),
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "stargazers_count": repo.get("stargazers_count"),
                    "forks_count": repo.get("forks_count"),
                    "created_at": repo.get("created_at"),
                    "updated_at": repo.get("updated_at"),
                }
            )

    return {
        "saved": len(items),
        "file": csv_path,
        "limit": limit,
        "offset": offset,
        "lang": lang,
    }