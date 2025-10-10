from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from pathlib import Path
from surquest.utils.scrappers.tesco import Scraper, DataHandler, FacetCZ, FacetUK, FacetSK, FacetHU
from surquest.fastapi.utils.route import Route  # custom routes for documentation and FavIcon
from surquest.fastapi.utils.GCP.catcher import (
    catch_validation_exceptions,
    catch_http_exceptions,
)
PATH_PREFIX = ""

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# custom routes to documentation and favicon
# app.add_api_route(path=F"{PATH_PREFIX}/", endpoint=Route.get_documentation, include_in_schema=False)
app.add_api_route(path=PATH_PREFIX, endpoint=Route.get_favicon, include_in_schema=False)

@app.get("/")
def get_ui() -> str:
    
    with open("./app/static/ui.html", "r") as f:
        return HTMLResponse(content=f.read())




@app.post("/products:scrape")
def count_strings(
    items: List[str],
    country: Optional[str] = Query("cz", description="Country code (e.g. 'cz', 'hu', 'sk', 'uk')")
) -> dict:
    """
    This endpoint scrapes product details for given item codes.
    Optional query parameter 'country' defines the region for the scraper.
    """

    tesco_scrapper = Scraper(
        api_key="TvOSZJHlEk0pjniDGQFAc9Q59WGAR4dA",
        region=country
    )

    out = []
    errors = []

    for item in items:
        try:
            response = tesco_scrapper.fetch_product(code=item)
            product = DataHandler.extract_product(response)

            product_details = {
                "id": product.get("id"),
                "tpnb": product.get("tpnb"),
                "title": product.get("title"),
                "description": product.get("description"),
                "brandName": product.get("brandName"),
                "defaultImageUrl": product.get("defaultImageUrl"),
                "superDepartmentName": product.get("superDepartmentName"),
                "departmentName": product.get("departmentName"),
                "shelfName": product.get("shelfName"),
                "price": product.get("price", {}).get("actual"),
            }

            out.append(product_details)

        except BaseException:
            errors.append(item)
            continue

    return {
        "country": country,
        "products": out,
        "errors": errors,
    }