import os

import pandas as pd

from constants import ORDERED_DF_COLUMNS
from parsers import clean_string


def save_df_to_csv(league_matches_data: list[dict], league_name: str) -> None:
    df = pd.DataFrame(league_matches_data)

    # df.columns = df.columns.str.strip()
    df = df[[column for column in ORDERED_DF_COLUMNS if column in df.columns]]

    csv_file_path = f"data/{clean_string(league_name)}.csv"

    if os.path.exists(csv_file_path):
        old_df = pd.read_csv(csv_file_path)

        old_df_rows_len = len(old_df)
        old_df_columns_len = len(old_df.columns)

        new_df_rows_len = len(df)
        new_df_columns_len = len(df.columns)

        # is_overwrite_allowed = (
        #     new_df_rows_len > old_df_rows_len
        #     and new_df_columns_len == old_df_columns_len
        #     or new_df_rows_len >= old_df_rows_len
        #     and new_df_columns_len > old_df_columns_len
        # )
        is_overwrite_allowed = True  # TODO: change after testing

        if is_overwrite_allowed:
            print(f"Successfully overwritten {csv_file_path} with more rows.")
            df.to_csv(csv_file_path, index=False)
        else:
            print(f"CSV {csv_file_path} will be NOT overwritten.")

    else:
        df.to_csv(csv_file_path, index=False)
        print(f"Successfully saved {csv_file_path} .")
