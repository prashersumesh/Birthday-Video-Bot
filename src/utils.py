import math
import multiprocessing
import warnings
from pathlib import Path

import pandas as pd
from moviepy.editor import VideoFileClip, concatenate_videoclips

warnings.filterwarnings(action="ignore")


def count_files_in_directory(directory_path):
    path = Path(directory_path)
    file_count = sum(1 for _ in path.glob("*") if _.is_file())
    return file_count


def convert_keys(original_dict):
    """Converts all keys in a dictionary to lowercase and replaces spaces with underscores.

    Args:
      original_dict: The original dictionary.

    Returns:
      A new dictionary with the modified keys.
    """

    new_dict = {}
    for key, value in original_dict.items():
        new_key = key.lower().replace(" ", "_")
        new_dict[new_key] = value
    return new_dict


class ProcessWorkbooks:

    def __init__(self, df: pd.DataFrame) -> None:

        # initialize df
        self.df = df

    def swap_header(self) -> None:
        """Swap the first date row and header if necessary"""

        first_row = self.df.iloc[0].to_dict()
        filtered_dict = {
            k: v
            for k, v in first_row.items()
            if not (isinstance(v, float) and math.isnan(v))
        }
        day_keys = {k: v for k, v in filtered_dict.items() if "day" in v}
        if day_keys != {}:  # if needed to swap, swap
            self.df.iloc[[0, 1]] = self.df.iloc[[1, 0]].values
            # Convert row 0 to header
            self.df.columns = self.df.iloc[0]
            self.df = self.df.drop(0, axis=0)

    @staticmethod
    def clean_party_schedule(df):
        """
        Cleans the party schedule dataframe by:
        1. Keeping rows that contain only a date (case insensitive)
        2. Keeping rows that have complete booking information
        3. Dropping rows that have partial or all null values

        Parameters:
        df (pandas.DataFrame): Input dataframe with party schedule

        Returns:
        pandas.DataFrame: Cleaned dataframe with date headers and complete bookings
        """
        # Create a copy to avoid modifying the original
        cleaned_df = df.copy()

        # Function to check if row is a date header
        def is_date_header(row):
            try:
                first_col_lower = str(row.iloc[0]).lower()
                day_names = [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ]
                return (
                    any(day in first_col_lower for day in day_names)
                    and row.iloc[1:].isna().all()
                )
            except:
                return False

        # Function to check if row has booking information
        def has_booking_info(row):
            # Check if second column (Booking Name) and third column (Birthday Child) have values
            # This indicates it's a booking row rather than an empty row
            try:
                return not pd.isna(row.iloc[1]) and not pd.isna(row.iloc[2])
            except:
                return False

        # Create a mask for rows to keep
        keep_mask = cleaned_df.apply(
            lambda row: is_date_header(row)  # Keep date headers
            or has_booking_info(row),  # Keep rows with booking information
            axis=1,
        )

        # Apply the mask to keep only desired rows
        cleaned_df = cleaned_df[keep_mask]

        return cleaned_df

    def convert_to_dict(self) -> dict:

        # check if header swap necessary
        self.swap_header()

        # clean the dataframe
        df = self.clean_party_schedule(self.df)

        # iterate over the df
        party_dict = {}
        current_date = None

        # Iterate over rows
        for idx, row in df.iterrows():
            if pd.isnull(row[0]) == False and "day," in str(row[0]):
                current_date = row[0]
                party_dict[current_date] = {}
            elif current_date:
                party_dict[current_date][idx] = {
                    "Booking Name": row[1],
                    "Birthday Child": row[2],
                    "Party Time": row[3],
                    "Party Room": row[4],
                    "Package": row[5],
                    "Party Host": row[6],
                    "Party Host Time": row[7],
                }

        return party_dict


def stack_video(file_path, output_path, min_length=30):
    # Load the video clip
    clip = VideoFileClip(file_path)
    original_duration = clip.duration
    repeat_count = int(min_length // original_duration) + 1

    # Duplicate the clip until the duration exceeds the minimum length
    clips = [clip] * repeat_count
    final_clip = concatenate_videoclips(clips)

    # Trim to the exact minimum length required
    final_clip = final_clip.subclip(0, min_length)

    # Write the output video with multiprocessing
    final_clip.write_videofile(
        output_path, threads=multiprocessing.cpu_count(), codec="libx264"
    )
