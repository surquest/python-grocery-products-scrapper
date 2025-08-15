from enum import Enum
import time
import requests
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from .handler import DataHandler


class Facet(str, Enum):
    MARKETPLACE = 'b;TWFya2V0cGxhY2U='
    CLOTHING_ACCESSORIES = 'b;Q2xvdGhpbmclMjAmJTIwQWNjZXNzb3JpZXM='
    SUMMER = 'b;U3VtbWVy'
    BACK_TO_SCHOOL = 'b;QmFjayUyMFRvJTIwU2Nob29s'
    FRESH_FOOD = 'b;RnJlc2glMjBGb29k'
    BAKERY = 'b;QmFrZXJ5'
    FROZEN_FOOD = 'b;RnJvemVuJTIwRm9vZA=='
    TREATS_SNACKS = 'b;VHJlYXRzJTIwJiUyMFNuYWNrcw=='
    FOOD_CUPBOARD = 'b;Rm9vZCUyMEN1cGJvYXJk'
    DRINKS = 'b;RHJpbmtz'
    BABY_TODDLER = 'b;QmFieSUyMCYlMjBUb2RkbGVy'
    HEALTH_BEAUTY = 'b;SGVhbHRoJTIwJiUyMEJlYXV0eQ=='
    PETS = 'b;UGV0cw=='
    HOUSEHOLD = 'b;SG91c2Vob2xk'
    HOME_ENTS = 'b;SG9tZSUyMCYlMjBFbnRz'
    ELECTRONICS_GAMING = 'b;RWxlY3Ryb25pY3MlMjAmJTIwR2FtaW5n'
    TOYS_GAMES = 'b;VG95cyUyMCYlMjBHYW1lcw=='
    PARTIES_SEASONAL = 'b;UGFydGllcyUyMCYlMjBTZWFzb25hbA=='
    KIOSK = 'b;S2lvc2s='
    INSPIRATION_EVENTS = 'b;SW5zcGlyYXRpb24lMjAmJTIwRXZlbnRz'


class Scraper:
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
            response_data = response.json()

            if "errors" in response_data[0].keys():
                
                error = esponse_data[0].get('errors')[0].get('message')

                raise Exception(f"API request failed: {error}")

            return response_data

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}") from e

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

    def fetch_products(self, facet:str, page: int = 1, size: int = 999) -> Any:
        """
        Fetch product listings from Tesco API.
        """

        variables = {
                "page": page,
                "includeRestrictions": True,
                "includeVariations": True,
                "count": size,
                "facet": facet.value,
                "appliedFacetArgs": [],
            }

        payload = [{
            "operationName": "GetCategoryProducts",
            "variables": variables,
            "extensions": {"mfeName": "mfe-plp"},
            "query": self.graphql["products"],
        }]

        return self._post_request(payload)

    def fetch_facet_products(self, facet: Facet, size: int = 500, page: int = 1):
        """
        Fetch all products from all pages of the category

        Args:
            facet (Facet): Facet to fetch products for
            size (int): Number of products to fetch per page
        
        Returns:
            dict: Dictionary containing all products from all pages
        """

        products = dict()
        fetch_next = True
        while fetch_next:

            print(f"-> Fetching page: {page}")

            response_data = self.retry(
                self.fetch_products,
                facet=facet,
                page=page,
                size=size
            )

            products = DataHandler.extract_products(response_data, products)
            total_count = DataHandler.extract_total_count_of_products(response_data)
            current_count = len(products.keys())

            print(f"Current Count: {current_count} of {total_count} (progress: {current_count/total_count})") 
            if page*size >= total_count:
                fetch_next = False

            page += 1

        return products


    @staticmethod
    def retry(func, *args, retries=5, delay=1, backoff=3, exceptions=(Exception,), **kwargs):
        """
        Generic retry function with exponentially increasing sleep time between tries.

        Args:
            func (callable): The function to retry.
            *args: Positional arguments for func.
            retries (int): Number of retry attempts before failing.
            delay (float): Initial delay between retries in seconds.
            backoff (float): Factor by which the delay increases after each retry.
            exceptions (tuple): Exception classes to catch and retry on.
            **kwargs: Keyword arguments for func.

        Returns:
            Any: The return value of the function, if successful.

        Raises:
            Exception: The last exception if all retries fail.
        """
        attempt = 0
        current_delay = delay

        while attempt <= retries:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                attempt += 1
                if attempt > retries:
                    raise
                time.sleep(current_delay)
                current_delay *= backoff