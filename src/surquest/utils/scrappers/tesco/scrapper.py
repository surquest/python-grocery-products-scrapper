import requests
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List


class TescoScraper:
    """
    A scraper for Tesco's GraphQL API.
    Provides methods to fetch taxonomy and product listings.
    """

    URL = "https://xapi.tesco.com/"
    HEADERS = {
        "accept": "application/json",
        "accept-language": "en-GB",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "language": "en-GB",
    }

    def __init__(
        self,
        api_key: str = "TvOSZJHlEk0pjniDGQFAc9Q59WGAR4dA",
        base_dir: Optional[Path] = None
    ):
        self.base_dir = base_dir or Path(__file__).resolve().parent
        self.api_key = api_key

        # Merge base headers with API key
        self.headers = {**self.HEADERS, "x-apikey": self.api_key}

        # Preload GraphQL queries
        self.graphql = {
            "products": self.load_graphql_query_from_file(self.base_dir / "graphql.products.gql"),
            "taxonomy": self.load_graphql_query_from_file(self.base_dir / "graphql.taxonomy.gql")
        }

        # Default variables for API requests
        self.variables = {
            "taxonomy": {
                "includeChildren": True,
                "usePageType": True,
                "includeInspirationEvents": True,
                "configs": []
            },
            "products": {
                "page": 1,
                "includeRestrictions": True,
                "includeVariations": True,
                # "showDepositReturnCharge": False,
                "count": 100,
                "facet": "b;RnJlc2glMjBGb29k",
                # "configs": [
                #     {
                #         "featureKey": "dynamic_filter",
                #         "params": [
                #             {"name": "enable", "value": "true"}
                #         ],
                #     },
                # ],
                # "filterCriteria": [
                #     {"name": "0", "values": ["groceries"]}
                # ],
                "appliedFacetArgs": [],
                # "sortBy": "relevance",
            }
        }

    @staticmethod
    def load_graphql_query_from_file(file_path: Path) -> str:
        """
        Load a GraphQL query from a file.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"GraphQL query file not found: {file_path}")
        return file_path.read_text(encoding="utf-8")

    def _post_request(self, payload: List[Dict[str, Any]]) -> Any:
        """
        Internal helper to send POST requests to the Tesco API.
        """
        try:
            response = requests.post(self.URL, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}") from e

    def fetch_taxonomy(self, variables: Optional[Dict[str, Any]] = None) -> Any:
        """
        Fetch category taxonomy from Tesco API.
        """
        payload_variables = self.variables["taxonomy"].copy()
        if variables:
            payload_variables.update(variables)

        payload = [{
            "operationName": "Taxonomy",
            "variables": payload_variables,
            "extensions": {"mfeName": "mfe-header"},
            "query": self.graphql["taxonomy"],
        }]
        return self._post_request(payload)

    def fetch_products(self, ) -> Any:
        """
        Fetch product listings from Tesco API.
        """
        payload_variables = self.variables["products"].copy()
        if variables:
            payload_variables.update(variables)

        print(f"payload_variables: {payload_variables}")

        payload = [{
            "operationName": "GetCategoryProducts",
            "variables": payload_variables,
            "extensions": {"mfeName": "mfe-plp"},
            "query": self.graphql["products"],
        }]
        return self._post_request(payload)