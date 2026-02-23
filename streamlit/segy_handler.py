import os
import numpy as np
import segyio
import pandas as pd
import json
from pandas import DataFrame
from segysak.segy import get_segy_texthead
from segysak.segy import segy_header_scan
from segysak.segy import segy_header_scrape
from file_handler import FileHandler
from segy_info_extractor import SegyInfoExtractor

class SegyHandler(FileHandler):
    """
    Refactored SEG-Y handler without AI/LangGraph dependencies.
    """

    def __init__(self, data_directory: str = "./data", available_segy_files: list[str] = []):
        # Pass the directory to the parent FileHandler
        super().__init__(data_directory=data_directory)
        self.available_segy_files = available_segy_files

    def process_segy_file(self, current_file: str) -> dict:
        """
        Refactored replacement for 'read_and_get_segy_information'.
        Takes a filename string directly and returns the statistics dictionary.
        """
        # Find the original SEG-Y file name from the list
        original_segy_file_name = self.get_segy_base_name(current_file)

        # Check if parquet file exists
        parquet_file_path = os.path.join(
            self.data_directory, f"{current_file}.parquet")
        
        if not os.path.exists(parquet_file_path):
            # Extract headers if the parquet doesn't exist yet
            if current_file == original_segy_file_name:
                self.__extract_segy_trace_headers(current_file)
            else:
                raise ValueError(f"Parquet file for {current_file} missing.")

        # Get statistics (this returns columns, info text, and scalars)
        return self.get_seismic_statistics(current_file)

    def get_segy_information(self, current_file: str) -> tuple:
        segy_file_name = self.get_segy_base_name(current_file)
        segy_file_path = self.get_segy_file_path(segy_file_name)
        
        # SegyInfoExtractor already works independently!
        extractor = SegyInfoExtractor(segy_file_path, current_file)
        info, scalar = extractor.extract_all_info()

        return info, scalar

    def __extract_segy_trace_headers(self, file_name: str) -> None:
        try:
            self.__save_segy_text_header_as_txt(file_name)
            self.__read_and_save_segy_headers(file_name)
        except Exception as e:
            raise Exception(f"Error extracting headers: {str(e)}")

    def __read_and_save_segy_headers(self, file_name: str) -> None:
        segy_headers_df = self.read_segy_headers(file_name)
        self.to_parquet(segy_headers_df, f"{file_name}.parquet")

    def read_segy(self, file_name: str) -> DataFrame:
        """
        Reads a SEG-Y file and returns its trace headers and amplitudes as a DataFrame.

        Parameters:
          file_name (str): The base name of the SEG-Y file (without extension) to read from the data directory.

        Returns:
          DataFrame: A DataFrame containing the trace headers for each trace, with an additional "Amplitudes" column
                 containing the amplitude values for each trace.

        Notes:
          - The method expects the SEG-Y file to have a '.sgy' extension and be located in self.data_directory.
          - Uses segy_header_scan and segy_header_scrape to extract and filter trace headers.
          - Amplitudes are extracted for each trace and appended as a new column in the DataFrame.
        """
        try:
            segy_file_path = self.get_segy_file_path(file_name)
            with segyio.open(segy_file_path, "r", ignore_geometry=True) as segyfile:
                # Extract trace headers into a DataFrame
                scan = segy_header_scan(segy_file_path)
                segy_df = segy_header_scrape(segy_file_path, partial_scan=None)
                segy_df = segy_df[scan[scan["mean"] != 0].index]

                # Extract amplitudes for each trace
                amplitudes = [segyfile.trace[i]
                              for i in range(segyfile.tracecount)]

                # Add amplitudes as a new column
                segy_df["Amplitudes"] = amplitudes

                return segy_df
        except FileNotFoundError:
            raise Exception(
                f"File {file_name} not found in {self.data_directory}.")
        except Exception as e:
            raise Exception(f"Error reading SEG-Y file: {str(e)}")

    def read_segy_headers(self, file_name: str) -> DataFrame:
        segy_file_path = self.get_segy_file_path(file_name)
        with segyio.open(segy_file_path, "r", ignore_geometry=True) as segyfile:
            scan = segy_header_scan(segy_file_path)
            trace_headers_df = segy_header_scrape(segy_file_path, partial_scan=None)
            
            # Filter non-zero headers
            trace_headers_df = trace_headers_df[scan[scan["mean"] != 0].index]
            trace_headers_df.reset_index(drop=True, inplace=True)
            trace_headers_df["trace_index"] = trace_headers_df.index

            return trace_headers_df

    def __save_segy_text_header_as_txt(self, file_name: str):
        txt_file_path = os.path.join(self.data_directory, f"{file_name}.txt")
        segy_file_path = self.get_segy_file_path(file_name)
        segy_header = get_segy_texthead(segy_file_path)
        with open(txt_file_path, "w", encoding="utf-8") as file:
            file.write(str(segy_header))

    def get_segy_base_name(self, current_file: str) -> str:
        # Simple string matching to find the base file
        for name in self.available_segy_files:
            if name in current_file:
                return name
        raise ValueError(f"No base SEG-Y file matching '{current_file}' found.")

    def get_seismic_statistics(self, current_file: str) -> dict:
        json_filename = f"{current_file}.json"
        json_data = self.load_segy_from_json(json_filename) 
        
        if json_data is not None:
            return json_data
            
        columns = self.get_columns_from_parquet(f"{current_file}.parquet")
        columns = [col for col in columns if col.lower() not in ("amplitude", "amplitudes", "trace_index")]
        
        info, scalar = self.get_segy_information(current_file)

        json_stats_data = {
            current_file: {
                "columns": columns,
                "infos": info,
                "scalco": scalar
            }
        }
        self.save_segy_information_to_json(json_filename, json_stats_data)
        return json_stats_data

    def add_amplitudes_to_dataframe(self, df: DataFrame, current_file: str) -> DataFrame:
        """
        Adds amplitudes to a DataFrame based on trace indices from the original SEG-Y file.

        Args:
            df (DataFrame): The DataFrame to which amplitudes will be added.
            current_file (str): The name of the current parquet file that system is working with.

        Returns:
            DataFrame: The updated DataFrame with an additional column for amplitudes.
        """
        original_segy_file_name = self.get_segy_base_name(current_file)
        segy_file_path = self.get_segy_file_path(original_segy_file_name)
        with segyio.open(segy_file_path, "r", ignore_geometry=True) as segyfile:
            indices = df["trace_index"].tolist()
            amplitudes = [np.array(segyfile.trace[i]) for i in indices]
        # Reset index to ensure proper alignment when assigning amplitudes
        df_result = df.reset_index(drop=True)
        df_result["Amplitudes"] = amplitudes
        return df_result
