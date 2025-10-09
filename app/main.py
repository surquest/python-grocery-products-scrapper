from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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

# custom routes to documentation and favicon
app.add_api_route(path=F"{PATH_PREFIX}/", endpoint=Route.get_documentation, include_in_schema=False)
app.add_api_route(path=PATH_PREFIX, endpoint=Route.get_favicon, include_in_schema=False)

@app.get("/")
def get_ui() -> str:
    
    with open("./app/static/ui.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.post("/products:scrape")
def count_strings(items: List[str]) -> dict:
    """
    This endpoint counts the number of strings in a list.
    """
    REGION = "cz"
    tesco_scrapper = Scraper(
        api_key="TvOSZJHlEk0pjniDGQFAc9Q59WGAR4dA",
        region=REGION
    )

    out = list()
    errors = list()
    for item in items:

        try:
            
            response = tesco_scrapper.fetch_product(
                code=item
            )

            product = DataHandler.extract_product(response)
            product_details = {
                "id": product.get('id'),
                "tpnb": product.get('tpnb'),
                "title": product.get('title'),
                "description": product.get('description'),
                "brandName": product.get('brandName'),
                "defaultImageUrl": product.get('defaultImageUrl'),
                "superDepartmentName": product.get('superDepartmentName'),
                "departmentName": product.get('departmentName'),
                "shelfName": product.get('shelfName'),
                "price": product.get('price', {}).get('actual')
            }

        except BaseException as e:

            errors.append(item)
            continue

        out.append(product_details)

  
    return {
        "products": out,
        "errors": errors
    }
