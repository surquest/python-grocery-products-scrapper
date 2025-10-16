# Import necessary libraries
import time
import requests
import re
import logging
from typing import Optional, Any, Dict


class Scraper:
    """
    Scraper for Ocado API v6 products.
    Provides methods to fetch taxonomy and product listings.
    """

    # Define constants for the scraper
    BASE_URL = "https://www.ocado.com"
    ATTRIBUTES = ("productId", "retailerProductId", "name", "price", "unitPrice", "brand", "size", "categoryPath", "alcohol")
    ENDPOINTS = {
        "base": BASE_URL,
        "products": {"method": "GET", "url": f"{BASE_URL}/api/v6/products"},
        "product_details": {
            "method": "PUT",
            "url": f"{BASE_URL}/api/webproductpagews/v6/products",
        },
    }
    BATCH_SIZE = 100 # Max 100 product IDs per request

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the Scraper.
        Args:
            logger (logging.Logger, optional): Custom logger.
                                               Defaults to module logger.
        """
        self.logger = logger or logging.getLogger(__name__)
        # Fetch tokens on initialization
        self.tokens = self._get_tokens(self.ENDPOINTS["base"])


    def fetch_categories(self) -> list:
        """
        Fetch all categories from the Ocado API.
        Returns:
            list: A list of category objects from the API.
        """
        # Make a request to the products endpoint
        response = requests.request(
            method=self.ENDPOINTS["products"]["method"],
            url=self.ENDPOINTS["products"]["url"],
            headers=self._get_headers(),
            cookies=self._get_cookies(),
        )
        # Raise an exception for bad status codes
        response.raise_for_status()
        # Return the categories from the JSON response
        return response.json().get("result", {}).get("categories", [])
    
    def get_products(self, category_id=None) -> tuple:
        """
        Public method to fetch all products for a given category, handling pagination.
        Args:
            category_id (str, optional): The category ID to filter products. Defaults to None.

        Returns:
            tuple: (list of product ids, product details)
        """

        # Initialize lists and variables
        all_product_ids = list()
        all_product_details = dict()
        next_page_token = None
        i = 0
        # Loop until there are no more pages
        while True:

            # Retry fetching products in case of failures
            product_ids, product_details, next_page_token = self.retry(
                self._get_products,
                category_id=category_id,
                next_page_token=next_page_token,
                retries=5,
                delay=1,
                backoff=2,
                exceptions=(requests.RequestException,),
            )

            # Extend the list of all product IDs
            all_product_ids.extend(product_ids)

            # Add product details to the dictionary
            for key, value in product_details.items():

                all_product_details[key] = {x: value.get(x) for x in self.ATTRIBUTES if x in value}

            # Log the progress
            self.logger.info(f"Fetched {len(set(product_ids))} products, total so far: {len(set(all_product_ids))}, next page token: {next_page_token}")
            
            # Break the loop if there is no next page token
            if not next_page_token:
                break

            i += 1

        return all_product_ids, all_product_details
    
    def get_product_details(self, product_ids: list) -> dict:
        """
        Public method to fetch detailed product information for a list of product IDs.
        Args:
            product_ids (list): List of product IDs to fetch details for.

        Returns:
            dict: Product details keyed by product ID.
        """

        # Retry fetching product details in case of failures
        return self.retry(
            self._get_product_details,
            product_ids=product_ids,
            retries=5,
            delay=1,
            backoff=2,
            exceptions=(requests.RequestException,),
        )
    
    def _get_product_details(self, product_ids: list) -> dict:
        """
        Fetch detailed product information for a list of product IDs.
        Args:
            product_ids (list): List of product IDs to fetch details for.
        Returns:
            dict: Product details keyed by product ID.
        """
        
        products = dict()
        product_ids = list(product_ids)  # Ensure uniqueness
        if not product_ids:
            return {}

        # Prepare batches with max 100 product IDs each and loop through them
        payloads = [product_ids[i:i + self.BATCH_SIZE] for i in range(0, len(product_ids), self.BATCH_SIZE)]

        self.logger.info(f"Fetching details for {len(product_ids)} products in {len(payloads)} batches.")

        for i, payload in enumerate(payloads):

            self.logger.info(f"Fetching details for batch {i + 1} of {len(payloads)}.")

            # Make a request to the product details endpoint
            response = requests.request(
                method=self.ENDPOINTS["product_details"]["method"],
                url=self.ENDPOINTS["product_details"]["url"],
                headers=self._get_headers(),
                cookies=self._get_cookies(),
                json=payload,
            )
            response.raise_for_status()

            data = response.json()

            # Log a warning if the number of requested and received products do not match
            if len(payload) != len(data.get("products", [])):
                self.logger.warning(f"Requested {len(payload)} products, but received {len(data.get('products', []))}")

            # Extract and store product details
            for product in data.get("products", []):
                products[product.get("productId")] = {x: product.get(x) for x in self.ATTRIBUTES if x in product}

        return products

    def _get_products(self, category_id=None, next_page_token=None) -> tuple:
        """
        Fetch products for a given category, handling pagination.
        Args:
            category_id (str, optional): The category ID to filter products. Defaults to None.
            next_page_token (str, optional): Token for the next page. Defaults to None.
        Returns:
            tuple: (list of product ids, product details, next page token)
        """

        params = dict()
        if category_id:
            params["category"] = category_id
        if next_page_token:
            params["pageToken"] = next_page_token

        # Make a request to the products endpoint
        response = requests.request(
            method=self.ENDPOINTS["products"]["method"],
            url=self.ENDPOINTS["products"]["url"],
            headers=self._get_headers(),
            cookies=self._get_cookies(),
            params=params,
        )
        response.raise_for_status()

        data = response.json()
        product_ids = list()
        product_details = data.get("entities", {}).get("product", {})

        # Extract product IDs from the response
        for group in data.get("result", {}).get("productGroups", []):

            products = group.get("products", [])

            product_ids.extend(list(set(products)))
            
        next_page_token = data.get("result", {}).get("nextPageToken", None)

        return product_ids, product_details, next_page_token

    @staticmethod
    def retry(
        func,
        *args,
        retries: int = 5,
        delay: float = 1,
        backoff: float = 3,
        exceptions: tuple = (Exception,),
        **kwargs,
    ) -> Any:
        """
        Retry wrapper with exponential backoff.
        """
        attempt = 0
        current_delay = delay
        logger = logging.getLogger(__name__)

        while attempt <= retries:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                # Log the error and increment the attempt counter
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                attempt += 1
                if attempt > retries:
                    raise
                # Wait before the next retry
                time.sleep(current_delay)
                current_delay *= backoff

    @classmethod
    def _get_tokens(cls, url: str, timeout: float = 10.0) -> Dict[str, Optional[str]]:
        """
        Perform GET request to retrieve session cookies and CSRF token.
        Returns:
            dict: { "global_sid": str, "visitor_id": str, "csrf_token": str }
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; python-requests)",
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
        }

        with requests.Session() as session:
            # Make a GET request to the base URL
            response = session.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            # Get session cookies
            global_sid = session.cookies.get("global_sid")
            visitor_id = session.cookies.get("VISITORID")

            # Extract CSRF token from HTML/JSON snippet in the response text
            match = re.search(r'"csrf"\s*:\s*\{\s*"token"\s*:\s*"([^"]+)"', response.text)

            csrf_token = match.group(1) if match else None

            return {
                "global_sid": global_sid,
                "visitor_id": visitor_id,
                "csrf_token": csrf_token,
            }

    def _get_cookies(self) -> Dict[str, str]:
        """Return cookie dictionary for requests."""
        return {
            "global_sid": self.tokens.get("global_sid"),
            "VISITORID": self.tokens.get("visitor_id"),
        }

    def _get_headers(self) -> Dict[str, str]:
        """Return header dictionary for requests."""
        return {
            "User-Agent": "Mozilla/5.0 (compatible; python-requests)",
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            "X-CSRF-TOKEN": self.tokens.get("csrf_token"),
        }
