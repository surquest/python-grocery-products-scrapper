from enum import Enum
import time
import requests
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from .handler import DataHandler
import logging


class Scraper:
    """
    A scraper for Ocado API v6 products.
    Provides methods to fetch taxonomy and product listings.
    """

    URL = "https://www.ocado.com/api/v6/products"

    ENDPOINTS = [
        "GET: https://www.ocado.com/api/webproductpagews//v6/product-pages?maxPageSize=500",
        "GET: https://www.ocado.com/api/v6/products?category=513db630-94bc-4ed0-9b62-fe038f108bb7&pageToken=2d294789-9f41-4e01-b6ef-b097d5875d66",
        "PUT: https://www.ocado.com/api/webproductpagews/v6/products"
    ]


    def __init__(self, visitor_id, endpoint=None, logger: Optional[logging.Logger] = None):
        """
        Initializes the Scraper.
        Args:
            endpoint (str, optional): The API endpoint to use. 
                                     Defaults to the class-level URL.
            logger (logging.Logger, optional): The logger to use for logging messages.
                                               If not provided, a default logger will be used.
        """

        self.visitor_id = visitor_id
        if endpoint is not None:
            self.URL = endpoint
        
        self.logger = logger or logging.getLogger(__name__)

    def _get_request(self, url: str, query_params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Internal helper to send GET requests to the Ocado API.
        Args:
            url (str): The URL to send the request to.
            query_params (Optional[Dict[str, Any]], optional): 
                A dictionary of query parameters to include in the request. 
                Defaults to None.
        Returns:
            Any: The JSON response from the API.
        Raises:
            Exception: If the API request fails.
        """

        try:
            self.logger.debug(f"Requesting to {url} with {query_params}")
            cookies = {'VISITORID': self.visitor_id}
            response = requests.get(
                url, 
                timeout=10, 
                params=query_params, 
                cookies=cookies
                )
            print(f"API response status: {response.status_code}")
            response.raise_for_status()
            self.logger.debug(f"Request to {url} succeed")
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise Exception(f"API request failed: {e}") from e

    @classmethod
    def get_visitor_id(cls):
        """
        Returns value of visitor ID Cookies
        Returns:
            str: The visitor ID.
        """

        response = requests.get(
            url = cls.URL
        )
        return response.cookies.get("VISITORID")


    def fetch_taxonomy(self):
        """
        Fetches the taxonomy from the Ocado API.
        Returns:
            list: A list of categories from the API response.
        """
        self.logger.info(f"Fetching taxonomy from {self.URL}")
        response = self._get_request(
            url = self.URL
        )

        return response.get("result").get("categories")

    def fetch_category_products(self, category_id):
        """
        Fetches all products for a given category ID.
        Handles pagination to retrieve all products.
        Args:
            category_id (str): The ID of the category to fetch products for.
        Returns:
            list: A list of all products in the specified category.
        """

        self.logger.info(f"Fetching products for category '{category_id}'")
        products = list()
        iteration = 0
        ids = set([])
        has_next_page = True
        next_page_token = None

        while has_next_page:
            print(f"Iteration: {iteration}")
            self.logger.info(f"Fetching page with token: {next_page_token}")
            loop_products, next_page_token, loop_ids = self._fetch_products(
                category_id=category_id,
                next_page_token=next_page_token
                )
            
            if len(loop_products) == 0:
                has_next_page = False
                break

            products.extend(loop_products)
            ids.union(loop_ids)
            print(f" - next page token: {next_page_token}")
            print(f" - count of loop products: {len(loop_ids)} - {loop_ids}")
            print(f" - total count of products: {len(products)}")
            print(ids)
            
            if next_page_token is None:
                has_next_page = False
            
            iteration += 1
            time.sleep(1)
        
        self.logger.info(f"Found {len(products)} products for category '{category_id}'")
        return products

    def _fetch_products(self, category_id=None, next_page_token=None):
        """
        Fetches a single page of products from the Ocado API.
        Args:
            category_id (str, optional): The ID of the category to fetch. 
                                         Defaults to None.
            next_page_token (str, optional): The token for the next page 
                                             of results. Defaults to None.
        Returns:
            tuple: A tuple containing:
                - A list of products from the API response.
                - The token for the next page of results, 
                  or None if there are no more pages.
        """

        query_params = dict()

        if category_id:
            query_params["category"] = category_id
        
        if next_page_token:
            query_params["pageToken"] = next_page_token

        response = self._get_request(
            url=self.URL,
            query_params=query_params
        )

        products = list()
        ids = set()
        
        for key, value in response.get("entities").get("product").items():
            products.append(value)
            ids.add(key)
        
        self.logger.info(f"Found {len(products)} products")

        next_page_token = response.get("result").get("nextPageToken")
        return products, next_page_token, ids
        

    @staticmethod
    def retry(
        func, *args, retries=5, delay=1, backoff=3, exceptions=(Exception,), **kwargs
    ):
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
        logger = logging.getLogger(__name__)

        while attempt <= retries:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                logger.error(e)
                attempt += 1
                if attempt > retries:
                    raise
                time.sleep(current_delay)
                current_delay *= backoff