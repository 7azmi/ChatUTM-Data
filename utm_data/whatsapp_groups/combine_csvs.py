import os
import pandas as pd


def merge_csv_files(input_directory, output_file):
    all_files = []

    # Recursively find all CSV files
    for root, _, files in os.walk(input_directory):
        for file in files:
            if file.endswith(".csv"):
                all_files.append(os.path.join(root, file))

    if not all_files:
        print("No CSV files found in the directory.")
        return

    print(f"Found {len(all_files)} CSV files. Merging...")

    # Read and merge all CSV files
    dataframes = []
    for file in all_files:
        try:
            df = pd.read_csv(file)
            dataframes.append(df)
        except Exception as e:
            print(f"Error reading {file}: {e}")

    if not dataframes:
        print("No valid CSV data to merge.")
        return

    # Concatenate all dataframes
    merged_df = pd.concat(dataframes, ignore_index=True)

    # Save merged CSV
    merged_df.to_csv(output_file, index=False)
    print(f"Merged CSV saved to {output_file}")


if __name__ == "__main__":
    input_directory = "."  # Change this
    output_file = "issyemen.csv"
    merge_csv_files(input_directory, output_file)
