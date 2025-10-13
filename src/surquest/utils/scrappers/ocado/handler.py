import json

class DataHandler:

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

        