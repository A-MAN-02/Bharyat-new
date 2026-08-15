import time
import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from config import NEXAR_CLIENT_ID, NEXAR_CLIENT_SECRET, SERPER_API_KEY

router = APIRouter()

NEXAR_TOKEN_URL = "https://identity.nexar.com/connect/token"
NEXAR_GRAPHQL_URL = "https://api.nexar.com/graphql"
SERPER_URL = "https://google.serper.dev/search"

IN_HOUSE_STOCK_PCT = 0.08
IN_HOUSE_PRICE_DISCOUNT = 0.20


class PartRequest(BaseModel):
    part_number: str


# ============================================================
# Nexar auth — token cached in memory across requests (module-level)
# ============================================================
_nexar_token = None
_nexar_token_expiry = 0


async def get_nexar_token(client: httpx.AsyncClient) -> str:
    global _nexar_token, _nexar_token_expiry
    if _nexar_token and time.time() < _nexar_token_expiry:
        return _nexar_token
    
    resp = await client.post(
        NEXAR_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": NEXAR_CLIENT_ID,
            "client_secret": NEXAR_CLIENT_SECRET,
            "scope": "supply.domain",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    data = resp.json()
    _nexar_token = data["access_token"]
    _nexar_token_expiry = time.time() + data["expires_in"] - 60  # refresh 60s early
    return _nexar_token


NEXAR_QUERY = """
query PartSearch($q: String!) {
    supSearchMpn(q: $q, limit: 1) {
        results {
            part {
                mpn

                manufacturer {
                    name
                }

                shortDescription

                bestDatasheet {
                    name
                    url
                    mimeType
                }

                authorizedSellers: sellers(authorizedOnly: true) {
                    company {
                        name
                    }
                    offers {
                        inventoryLevel
                        prices {
                            price
                            quantity
                        }
                    }
                }

                allSellers: sellers {
                    company {
                        name
                    }
                    offers {
                        inventoryLevel
                        prices {
                            price
                            quantity
                        }
                    }
                }
            }
        }
    }
}
"""
def normalize_nexar_part(part: dict):
    """Same logic as the frontend's normalizeNexarRows, in Python."""

    if not part:
        return {
            "rows": [],
            "datasheet_url": None,
            "description": None
        }

    def to_row(seller, is_authorised):
        offers = seller.get("offers") or []

        stock = sum(
            o.get("inventoryLevel") or 0
            for o in offers
        )

        all_prices = [
            p.get("price")
            for o in offers
            for p in (o.get("prices") or [])
            if p.get("price") is not None
        ]

        price = min(all_prices) if all_prices else None

        return {
            "distributor": (seller.get("company") or {}).get("name") or "Unknown",
            "sku": None,
            "stock": stock,
            "price_10k": price,
            "is_authorised": is_authorised,
        }

    # -----------------------------
    # Authorized sellers
    # -----------------------------

    authorized_sellers = part.get("authorizedSellers") or []

    # -----------------------------
    # All sellers
    # -----------------------------

    all_sellers = part.get("allSellers") or []

    authorized_names = {
        (s.get("company") or {}).get("name")
        for s in authorized_sellers
    }

    ad_rows = [
        to_row(s, True)
        for s in authorized_sellers
    ]

    ib_rows = [
        to_row(s, False)
        for s in all_sellers
        if (s.get("company") or {}).get("name")
        not in authorized_names
    ]

    # -----------------------------
    # Datasheet
    # -----------------------------

    best_datasheet = part.get("bestDatasheet") or {}

    datasheet_url = best_datasheet.get("url")

    # -----------------------------
    # Description
    # -----------------------------

    manufacturer = (part.get("manufacturer") or {}).get("name")
    short_desc = part.get("shortDescription")

    description = (
        f"{manufacturer} — {short_desc}"
        if manufacturer and short_desc
        else (short_desc or manufacturer)
    )

    return {
        "rows": ad_rows + ib_rows,
        "datasheet_url": datasheet_url,
        "description": description
    }


@router.post("/nexar/search")
async def nexar_search(req: PartRequest):
    """
    Cache-miss fallback: queries Nexar (Octopart's official API) for a part,
    returns normalized rows + datasheet + description in one call.
    Frontend never sees the Nexar client secret.
    """
    part = req.part_number.strip().upper()

    async with httpx.AsyncClient(timeout=30) as client:
        token = await get_nexar_token(client)
        resp = await client.post(
            NEXAR_GRAPHQL_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            json={
                "query": NEXAR_QUERY,
                "variables": {"q": part},
            },
        )

        print("=" * 80)
        print("PART:", part)
        print("NEXAR STATUS:", resp.status_code)
        print("NEXAR RESPONSE:")
        print(resp.text)
        print("=" * 80)

        if resp.status_code != 200:
            return {
                "rows": [],
                "datasheet_url": None,
                "description": None,
                "error": resp.text,
            }

        data = resp.json()

        if data.get("errors"):
            print("GRAPHQL ERRORS:", data["errors"])
            return {
                "rows": [],
                "datasheet_url": None,
                "description": None,
                "error": data["errors"],
            }

    if data.get("errors"):
        print(f"[nexar] GraphQL errors for {part}: {data['errors']}")
        return {"rows": [], "datasheet_url": None, "description": None}

    results = (data.get("data") or {}).get("supSearchMpn", {}).get("results") or []
    part_data = results[0]["part"] if results else None
    return normalize_nexar_part(part_data)


# ============================================================
# Serper — cheap datasheet lookup for cache-hit parts, so we don't
# spend Nexar's limited free quota just to fetch a PDF link.
# ============================================================
@router.post("/datasheet/serper")
async def datasheet_via_serper(req: PartRequest):
    part = req.part_number.strip()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                SERPER_URL,
                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": f"{part} datasheet filetype:pdf"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[serper] datasheet lookup failed for {part}: {e}")
        return {"datasheet_url": None}

    organic = data.get("organic") or []
    return {"datasheet_url": organic[0]["link"] if organic else None}