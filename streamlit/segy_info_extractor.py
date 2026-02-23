import pandas as pd
import numpy as np
import segyio
from segysak.segy import get_segy_texthead
from file_handler import FileHandler

NAMES_EN = {
    "Interval": "sampling_rate",
    "Samples": "num_samples",
    "Format": "data_format",
    "MeasurementSystem": "measurement_code",
    "SEGYRevision": "segy_revision",
    "SEGYRevisionMinor": "segy_revision_minor",
    "LineNumber": "line_number",
}

READABLE_NAMES = {
    "sampling_rate": "Sampling Rate (ms)",
    "num_samples": "Samples per Trace",
    "data_format": "Data Format",
    "measurement_code": "Measurement Code",
    "segy_revision": "SEG-Y Revision (Major)",
    "segy_revision_minor": "SEG-Y Revision (Minor)",
    "line_number": "Line Number",
    "data_type": "Data Type",
}

class SegyInfoExtractor:
    def __init__(self, segy_file_path: str, headers_file_name: str):
        self.segy_file_path = segy_file_path
        self.file_handler = FileHandler()
        self.trace_headers = self.file_handler.read_parquet(f"{headers_file_name}.parquet")
        self.is_3d = None
        self.info = None
        self.segyio_file = None
        
    def __enter__(self):
        try:
            self.segyio_file = segyio.open(self.segy_file_path, "r", ignore_geometry=False)
            self.is_3d = True
        except RuntimeError as e:
            if "unable to find sorting" in str(e):
                self.segyio_file = segyio.open(self.segy_file_path, "r", ignore_geometry=True)
                self.is_3d = False
            else:
                raise e
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.segyio_file:
            self.segyio_file.close()

    @staticmethod
    def format_number(value):
        if isinstance(value, (np.floating, float)):
            return f"{float(value):.2f}".rstrip('0').rstrip('.')
        if isinstance(value, (np.integer, int)):
            return int(value)
        return value
    
    def extract_binary_header_info(self):
        """
        Dynamically extracts all available fields from the SEG-Y binary header
        and stores only those that are present and contain valid data.
        """
        extracted_fields = {}

        for field_name in dir(segyio.BinField):
            # Ignore special (__dunder__) and private attributes
            if field_name.startswith("_"):
                continue
            
            try:
                field = getattr(segyio.BinField, field_name)
                value = self.segyio_file.bin[field]
                
                # Convert known field to friendly value if necessary
                if field_name == "Interval":
                    value = self.format_number(value / 1000)  # from µs to ms
                
                # Store if the value is considered valid
                if value not in [None, 0]:
                    name = NAMES_EN.get(field_name, field_name)
                    extracted_fields[name] = value

            except Exception:
                # Field may not exist or be accessible in the binary header
                continue

        # Add additional information
        extracted_fields["data_type"] = "3D" if self.is_3d else "2D"

        return extracted_fields
    
    def get_trace_header_value(self, key):
        """
        Returns the value of the header column if it exists, otherwise returns an array of zeros of the same length.
        """
        if key in self.trace_headers:
            return self.trace_headers[key]
        else:
            return np.zeros(len(self.trace_headers))
        
    def extract_basic_info(self):
        """Extracts basic information using the already loaded headers"""
        info = {
            "recording_time": self.format_number(self.get_trace_header_value('DelayRecordingTime').max() / 1000),
            "shot_point_distance": self.format_number(abs(pd.Series(self.get_trace_header_value('SourceX')).diff().mode()[0])),
            "plot_direction": "LR" if pd.Series(self.get_trace_header_value('SourceX')).diff().mean() > 0 else "RL",
            "min_offset": self.format_number(self.get_trace_header_value('offset').min()),
            "max_offset": self.format_number(self.get_trace_header_value('offset').max()),
            "num_channels": self.format_number(len(pd.Series(self.get_trace_header_value('TraceNumber')).unique())),
            "first_cdp": self.format_number(self.get_trace_header_value('CDP').min()),
            "last_cdp": self.format_number(self.get_trace_header_value('CDP').max()),
        }
        if self.is_3d:
            info.update({
            "first_inline": self.format_number(self.get_trace_header_value('INLINE_3D').min()),
            "last_inline": self.format_number(self.get_trace_header_value('INLINE_3D').max()),
            "first_crossline": self.format_number(self.get_trace_header_value('CROSSLINE_3D').min()),
            "last_crossline": self.format_number(self.get_trace_header_value('CROSSLINE_3D').max()),
            })

        return info
    
    @staticmethod
    def format_binary_header_info(bin_head):
        lines = []
        
        for key, value in bin_head.items():
            name = READABLE_NAMES.get(key, key.replace("_", " ").capitalize())
            lines.append(f"{name}: {value}")

        return "\n".join(lines)
    
    def extract_geometry_info(self):
        """Extracts geometry information using the already loaded headers"""
        geometry_info = {
            "total_traces": self.segyio_file.tracecount,  
            "total_shots": len(np.unique(self.get_trace_header_value('SourceX'))),
            "coordinates": {
                "x_min": self.format_number(self.get_trace_header_value('SourceX').min()),
                "x_max": self.format_number(self.get_trace_header_value('SourceX').max()),
                "y_min": self.format_number(self.get_trace_header_value('SourceY').min()),
                "y_max": self.format_number(self.get_trace_header_value('SourceY').max())
            }
        }

        if self.is_3d:
            geometry_info.update({
                "inline_dimensions": len(np.unique(self.get_trace_header_value('INLINE_3D'))),
                "crossline_dimensions": len(np.unique(self.get_trace_header_value('CROSSLINE_3D')))
            })

        return geometry_info
    
    def extract_acquisition_info(self):
        cdp_values = self.get_trace_header_value('CDP')
        if np.std(cdp_values) != 0:
            fold = pd.Series(cdp_values).groupby(cdp_values).size()
            acq_info = {
                "average_fold": self.format_number(fold.mean()),
                "maximum_fold": self.format_number(fold.max()),
                "minimum_fold": self.format_number(fold.min()),
            }
        else:
            acq_info = {
                "average_fold": "Not applicable",
                "maximum_fold": "Not applicable",
                "minimum_fold": "Not applicable",
            }
        
        if self.is_3d:
            il_spacing = np.diff(np.sort(np.unique(self.get_trace_header_value('INLINE_3D'))))
            xl_spacing = np.diff(np.sort(np.unique(self.get_trace_header_value('CROSSLINE_3D'))))
            
            acq_info.update({
                "inline_spacing": self.format_number(np.median(il_spacing)),
                "crossline_spacing": self.format_number(np.median(xl_spacing))
            })
            
        return acq_info
    
    def extract_all_info(self) -> tuple:
        """
        Extracts all information within the context of the 'with' manager
        """
        with self:
            self.info = {
                "basic_information": self.extract_basic_info(),
                "binary_header": self.extract_binary_header_info(),
                "geometry": self.extract_geometry_info(),
                "acquisition": self.extract_acquisition_info(),
                "ascii_header_text": get_segy_texthead(self.segy_file_path)
            }

        information = self.get_segy_info_text()
        scaling_factor = self.extract_scaling_factor()
            
        return information, scaling_factor
    

    def get_segy_info_text(self):
        basic = self.info["basic_information"]
        bin_head = self.info["binary_header"]
        binary_header_info = self.format_binary_header_info(bin_head)
        geo = self.info["geometry"]
        acq = self.info["acquisition"]
        ASCII_header = self.info["ascii_header_text"]
    
        info = (
            "DETAILED INFORMATION OF THE SEG-Y FILE\n"
            "INFORMATION CONTAINED IN THE ASCII HEADER:\n"
            f"ASCII_header: {ASCII_header}"
            
            "BASIC INFORMATION:\n"
            f"Recording Time: {basic['recording_time']} s\n"
            f"Distance Between Shot Points: {basic['shot_point_distance']} m\n"
            f"Plot Direction: {basic['plot_direction']}\n"
            f"Offset Range: {basic['min_offset']} - {basic['max_offset']} m\n"
            f"Number of Channels: {basic['num_channels']}\n"
            f"CDP Range: {basic['first_cdp']} - {basic['last_cdp']}\n"
            
            "\nBINARY HEADER INFORMATION:\n"
            f"{binary_header_info}"

            "\nGEOMETRY INFORMATION:\n"
            f"Total Traces: {geo['total_traces']}\n"
            f"Total Shots: {geo['total_shots']}\n"
            "Coordinates:\n"
            f"  X: {geo['coordinates']['x_min']} - {geo['coordinates']['x_max']}\n"
            f"  Y: {geo['coordinates']['y_min']} - {geo['coordinates']['y_max']}\n"
            
            "\nACQUISITION INFORMATION:\n"
            f"Average Fold: {acq['average_fold']}\n"
            f"Maximum Fold: {acq['maximum_fold']}\n"
            f"Minimum Fold: {acq['minimum_fold']}\n"
        )
    
        if self.is_3d:
            info = info.replace("CDP Range:", "CDP Range:\n")
            info += (
                f"Inline Range: {basic['first_inline']} - {basic['last_inline']}\n"
                f"Crossline Range: {basic['first_crossline']} - {basic['last_crossline']}\n"
                f"Inline Dimensions: {geo['inline_dimensions']}\n"
                f"Crossline Dimensions: {geo['crossline_dimensions']}\n"
                f"Inline Spacing: {acq['inline_spacing']}\n"
                f"Crossline Spacing: {acq['crossline_spacing']}\n"
            )
    
        return info

    def extract_scaling_factor(self):
        """
        Extracts the source group scalar.
        """
        scalar = self.get_trace_header_value('SourceGroupScalar').mean()
        scalar = self.format_number(scalar)
        return scalar if scalar != 0 else 1
