import json

class DataHandler:

    @staticmethod
    def extract_super_departments(response_data: list) -> dict:
        """
        Extract super department information from response_payload and populate super_departments dictionary.

        Args:
            super_departments (dict): Dictionary to store super departments keyed by super department ID.
            response)
        
        Returns:

            dict: Updated super_departments dictionary.
        """

        out = dict()

        tachonomy = response_data[0].get('data', {}).get('taxonomy')

        for item in tachonomy:
            name = item.get('name')
            id_ = item.get('id')

            # Defensive: Skip if no ID
            if not id_:
                continue

            out[id_] = name

        return out

    @staticmethod
    def extract_total_count_of_products(response_data: list) -> int:
        """
        Extract total count of products from response_data.

        Args:
            response_data (list): API response data containing total count of products.

        Returns:
            int: Total count of products.
        """

        try:
            return response_data[0]['data']['category']['pageInformation']['totalCount']
        except (KeyError, IndexError, AttributeError) as e:
            raise ValueError(f"Invalid response structure: {e}")

    @staticmethod
    def extract_product(response_data: list) -> dict:
        """
        Extract product information from response_data.

        Args:
            response_data (list): API response data containing product details.

        Returns:
            dict: Dictionary containing product information.
        """

        try:
            node = response_data[0]['data']['product']
        except (KeyError, IndexError, AttributeError) as e:
            raise ValueError(f"Invalid response structure: {e}")

        return node
    
    @staticmethod
    def extract_products(response_data: list, products: dict=dict()) -> dict:
        """
        Extract product information from response_data and populate products dictionary.

        Args:
            products (dict): Dictionary to store products keyed by product ID.
            response_data (list): API response data containing product details.

        Returns:
            dict: Updated products dictionary.
        """
        try:
            for item in response_data[0]['data']['category']['results']:
                node = item['node']
                id_ = node.get('id')

                # Defensive: Skip if no ID
                if not id_:
                    continue

                sellers = node.get('sellers', {}).get("results", [])
                price_info = sellers[0].get("price", {}) if sellers else {}
                price = price_info.get("price") if price_info else None
                unit_price = price_info.get("unitPrice") if price_info else None
                unit_of_measure = price_info.get("unitOfMeasure") if price_info else None

                product = {
                    "title": node.get('title'),
                    "brand": node.get('brandName'),
                    "desc": node.get('shortDescription'),
                    "imageUrl": node.get('defaultImageUrl'),
                    "price": {
                        "price": price,
                        "unitPrice": unit_price,
                        "unitOfMeasure": unit_of_measure
                    },
                    "superDepartment": {
                        "id": node.get('superDepartmentId'),
                        "name": node.get('superDepartmentName')
                    },
                    "department": {
                        "id": node.get('departmentId'),
                        "name": node.get('departmentName')
                    },
                    "aisle": {
                        "id": node.get('aisleId'),
                        "name": node.get('aisleName')
                    },
                    "shelf": {
                        "id": node.get('shelfId'),
                        "name": node.get('shelfName')
                    },
                    "ids": {
                        "id": id_,
                        "tpnb": node.get('tpnb'),
                        "tpnc": node.get('tpnc'),
                        "gtin": node.get('gtin')
                    }
                }

                products[id_] = product

        except (KeyError, IndexError, AttributeError) as e:
            print("-"*100)
            print(json.dumps(item))
            print("-"*100)
            raise ValueError(f"Invalid response structure: {e}")

        return products

    @staticmethod
    def save_as_jsonlines(data, file_path):
        """
        Save data to a JSON Lines file.

        Args:
            data (list): Data to be saved.
            file_path (str): Path to the JSON Lines file.
        """

        out = list()
        if isinstance(data, list):
            out = data

        else:
            for key, value in data.items():
                out.append(value)
            
        with open(file_path, 'w') as file:
            for item in out:
                json_line = json.dumps(item) + '\n'
                file.write(json_line)

        