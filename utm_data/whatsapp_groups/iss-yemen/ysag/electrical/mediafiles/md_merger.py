import os


def merge_markdown_files(input_dir, output_file):
    """
    Simple merge of all .md files in directory and subdirectories into one file.
    """
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(input_dir):
            for filename in sorted(files):
                if filename.endswith('.md'):
                    filepath = os.path.join(root, filename)
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                        outfile.write('\n')  # Add newline between files


if __name__ == "__main__":
    input_directory = "."
    output_file = "ysag-electrical-faculty.md"

    merge_markdown_files(input_directory, output_file)
    print(f"All .md files from {input_directory} merged into {output_file}")