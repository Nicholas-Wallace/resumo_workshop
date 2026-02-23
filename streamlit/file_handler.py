import os
import pandas as pd
from pandas import DataFrame
import json


class FileHandler:
    def __init__(self, data_directory: str = "./data"):
        """Initialize with the directory containing CSV files."""
        self.data_directory = data_directory
        self.json_directory = os.path.join(data_directory, "metadata")
        os.makedirs(self.json_directory, exist_ok=True)

    def read_csv(self, file_name: str) -> DataFrame:
        """Read a CSV file and return its contents as a DataFrame."""
        try:
            file_path = os.path.join(self.data_directory, f"{file_name}.csv")
            return pd.read_csv(file_path)
        except FileNotFoundError:
            raise Exception(f"File {file_name} not found.")
        except Exception as e:
            raise Exception(f"Error reading CSV file: {str(e)}")

    def to_csv(self, df: DataFrame, file_name: str) -> None:
        """Write a DataFrame to a CSV file."""
        try:
            file_path = os.path.join(self.data_directory, f"{file_name}.csv")
            df.to_csv(file_path, index=False)
        except Exception as e:
            raise Exception(f"Error writing DataFrame to CSV file: {str(e)}")

    def read_parquet(self, file_name: str) -> DataFrame:
        """Read a Parquet file and return its contents as a DataFrame."""
        try:
            file_path = os.path.join(self.data_directory, file_name)
            return pd.read_parquet(file_path)
        except FileNotFoundError:
            raise Exception(f"File {file_path} not found.")
        except Exception as e:
            raise Exception(f"Error reading Parquet file: {str(e)}")

    def to_parquet(self, df: DataFrame, file_name: str) -> None:
        """Write a DataFrame to a Parquet file."""
        try:
            file_path = os.path.join(self.data_directory, file_name)
            df.to_parquet(file_path, index=False)
        except Exception as e:
            raise Exception(
                f"Error writing DataFrame to Parquet file: {str(e)}")

    def get_columns_from_parquet(self, file_name: str) -> list:
        """Get the column names from a Parquet file."""
        try:
            df = self.read_parquet(file_name)
            return df.columns.tolist()
        except Exception as e:
            raise Exception(
                f"Error getting columns from Parquet file: {str(e)}")

    def get_segy_file_path(self, file_name: str) -> str:
        """
        Returns the full path to a SEG-Y file with either .sgy or .segy extension.

        Parameters:
          file_name (str): The base name of the SEG-Y file (without extension).

        Returns:
          str: The full file path if the file exists.

        Raises:
          FileNotFoundError: If neither .sgy nor .segy file exists.
        """
        possible_extensions = [".sgy", ".segy"]
        for ext in possible_extensions:
            file_path = os.path.join(self.data_directory, f"{file_name}{ext}")
            if os.path.isfile(file_path):
                return file_path
        raise FileNotFoundError(
            f"No SEG-Y file found for '{file_name}' with .sgy or .segy extension in {self.data_directory}.")

    def file_exists(self, file_name: str) -> bool:
        """
        Check if a file exists in the data directory.

        Parameters:
          file_name (str): The name of the file to check with extension.

        Returns:
          bool: True if the file exists, False otherwise.
        """
        if os.path.isfile(os.path.join(self.data_directory, file_name)):
            return True
        return False

    def remove_file(self, file_name: str) -> None:
        """
        Remove a file from the data directory.

        Parameters:
          file_name (str): The name of the file to remove (with extension).

        Raises:
          FileNotFoundError: If the file does not exist.
          Exception: If there is an error during file removal.
        """
        file_path = os.path.join(self.data_directory, file_name)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(
                f"File {file_name} not found in {self.data_directory}.")
        try:
            os.remove(file_path)
        except Exception as e:
            raise Exception(f"Error removing file {file_name}: {str(e)}")

    def get_json_filepath(self, file_name: str) -> str:
        """
        Generate the JSON file path based on the original SEGY file name.

        Parameters:
            file_name (str): The name of the JSON file.

        Returns:
            str: The complete path to the JSON file.
        """
        return os.path.join(self.json_directory, file_name)

    def save_segy_information_to_json(self, file_name: str, json_data: dict) -> None:
        """
        Save extracted information into a JSON file.

        Parameters:
            file_name (str): The name of the new JSON file.
            json_data (dict): Dictionary containing the extracted SEGY file information to be saved.

        Raises:
            Exception: If the JSON file could not be saved.

        """
        json_filepath = self.get_json_filepath(file_name)

        try:
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2,
                          ensure_ascii=False, default=str)
        except Exception as e:
            raise Exception(f"Error saving JSON: {e}")

    def load_segy_from_json(self, file_name: str) -> tuple | None:
        """
        Load information from a JSON file if it exists.

        Parameters:
            file_name (str): The name of the JSON file.

        Returns:
            tuple | None: A tuple containing (information, scaling_factor) if the JSON exists, otherwise None.

        Raises:
            Exception: If there is an error while reading or parsing the JSON file.
        """
        json_filepath = self.get_json_filepath(file_name)

        if os.path.exists(json_filepath):
            try:
                with open(json_filepath, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                return json_data

            except Exception as e:
                raise Exception(f"Error loading JSON: {e}")

        return None
