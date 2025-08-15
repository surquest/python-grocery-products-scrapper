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

                product = {
                    "title": node.get('title'),
                    "brand": node.get('brandName'),
                    "desc": node.get('shortDescription'),
                    "imageUrl": node.get('defaultImageUrl'),
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
                    },
                    "price": {
                        "price": price_info.get("price"),
                        "unitPrice": price_info.get("unitPrice"),
                        "unitOfMeasure": price_info.get("unitOfMeasure")
                    },
                    "promotion": {
                        "unitOfMeasure": node.get('unitOfMeasure')
                    }
                }

                products[id_] = product

        except (KeyError, IndexError, AttributeError) as e:
            raise ValueError(f"Invalid response structure: {e}")

        return products
