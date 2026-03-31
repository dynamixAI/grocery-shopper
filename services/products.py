import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup


class ProductLookupError(Exception):
    """Raised when product lookup fails in a controlled way."""


HEADERS = {
    "User-Agent": "GroceryShopper/1.0"
}


# Aldi category pages that already expose product lists with prices
ALDI_CATEGORY_URLS = {
    "milk": "https://www.aldi.co.uk/products/chilled-food/milk/k/1588161416978051001",
    "vegetable": "https://www.aldi.co.uk/products/fresh-food/vegetables/k/1588161416978050002",
    "vegetables": "https://www.aldi.co.uk/products/fresh-food/vegetables/k/1588161416978050002",
    "beef": "https://www.aldi.co.uk/products/fresh-food/beef/k/1588161416978050005",
    "fresh food": "https://www.aldi.co.uk/products/fresh-food/k/1588161416978050",
    "food cupboard": "https://www.aldi.co.uk/products/food-cupboard/k/1588161416978053",
    "chilled": "https://www.aldi.co.uk/products/chilled-food/k/1588161416978051",
}


def normalise_text(text: str) -> str:
    return " ".join(text.strip().split())


def infer_aldi_category_url(query: str) -> Optional[str]:
    """
    Map a user query to the most likely Aldi category page.
    """
    q = query.lower().strip()

    if "milk" in q:
        return ALDI_CATEGORY_URLS["milk"]

    if any(word in q for word in ["vegetable", "veg", "carrot", "pepper", "cucumber", "garlic", "onion", "potato"]):
        return ALDI_CATEGORY_URLS["vegetable"]

    if any(word in q for word in ["beef", "steak", "mince"]):
        return ALDI_CATEGORY_URLS["beef"]

    if any(word in q for word in ["egg", "cheese", "yogurt", "yoghurt", "pizza", "pasta", "ready meal"]):
        return ALDI_CATEGORY_URLS["chilled"]

    if any(word in q for word in ["rice", "spaghetti", "pasta", "noodle", "sauce", "beans", "cereal", "biscuit", "sugar"]):
        return ALDI_CATEGORY_URLS["food cupboard"]

    if any(word in q for word in ["chicken", "pork", "meat", "fish", "fruit", "bread"]):
        return ALDI_CATEGORY_URLS["fresh food"]

    return None


def extract_price(text: str) -> Optional[float]:
    """
    Extract the first £ price from a block of text.
    """
    match = re.search(r"£\s?(\d+(?:\.\d{1,2})?)", text)
    if not match:
        return None
    return float(match.group(1))


def search_aldi_products(query: str, max_results: int = 5) -> List[dict]:
    """
    Search Aldi products by scraping likely category pages, then filtering matches.
    """
    category_url = infer_aldi_category_url(query)
    if not category_url:
        return []

    try:
        response = requests.get(category_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ProductLookupError(f"Aldi lookup failed: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text("\n", strip=True)

    # Very simple line-based extraction from Aldi list pages
    lines = [normalise_text(line) for line in page_text.splitlines() if normalise_text(line)]

    query_words = [word for word in query.lower().split() if word]

    candidates = []
    seen = set()

    for i, line in enumerate(lines):
        lower_line = line.lower()

        # Require all query words or at least one strong match for simple MVP
        if query_words and not any(word in lower_line for word in query_words):
            continue

        price = extract_price(line)

        # Try to use the line itself as product text if it contains a price
        if price is not None:
            product_name = line
        else:
            # look ahead a little for price-containing text
            window = " ".join(lines[i:i+3])
            price = extract_price(window)
            if price is None:
                continue
            product_name = window

        key = product_name.lower()
        if key in seen:
            continue
        seen.add(key)

        candidates.append({
            "wanted_item": query,
            "store_brand": "Aldi",
            "branch": "Selected Aldi branch",
            "address": "Branch selected earlier",
            "matched_product": product_name[:180],
            "price": price,
            "pack_size": "",
            "offer": "Check Aldi page",
            "source_url": category_url
        })

    # Rank by simple relevance: count matching words
    def score(item: dict) -> int:
        text = item["matched_product"].lower()
        return sum(1 for word in query_words if word in text)

    ranked = sorted(candidates, key=score, reverse=True)

    return ranked[:max_results]


def build_product_results(items: List[str], confirmed_stores: List[dict]) -> dict:
    """
    Build comparison results. Aldi uses live-ish lookup.
    Other stores remain mock for now.
    """
    results = {}

    for item in items:
        item_results = []

        for store in confirmed_stores:
            if store["store_brand"] == "Aldi":
                aldi_matches = search_aldi_products(item)

                for match in aldi_matches:
                    item_results.append({
                        **match,
                        "branch": store["branch"],
                        "address": store["address"]
                    })
            else:
                # Keep non-Aldi stores mocked for now
                item_results.append({
                    "wanted_item": item,
                    "store_brand": store["store_brand"],
                    "branch": store["branch"],
                    "address": store["address"],
                    "matched_product": f"{item.title()} - {store['store_brand']} Choice",
                    "price": 0.00,
                    "pack_size": "",
                    "offer": "Mock result"
                })

        results[item] = item_results

    return results
