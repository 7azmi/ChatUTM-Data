import re
import csv

def extract_lecturer_data(filename="ysag-electrical-faculty.md"):
    """
    Extracts lecturer information from the given Markdown file and returns it as a list of dictionaries.
    """
    lecturers = []
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split the content into individual lecturer sections
    lecturer_sections = re.split(r'## Lecturer Information\n', content)[1:]  # Split and remove the first empty element

    for section in lecturer_sections:
        lecturer = {}

        # Extract Name
        name_match = re.search(r'- \*\*Name\*\*: (.*)', section)
        lecturer['Name'] = name_match.group(1).strip() if name_match else ""

        # Extract Courses (if available)
        courses_match = re.search(r'- \*\*Courses\*\*: (.*)', section)
        lecturer['Courses'] = courses_match.group(1).strip() if courses_match else ""

        # Extract Review Summary
        review_match = re.search(r'### Review Summary\n(.*?)(?=\n###|\n##)', section, re.DOTALL)
        lecturer['Review Summary'] = review_match.group(1).strip() if review_match else ""

        # Extract Key Points
        key_points_match = re.search(r'### Key Points\n(.*?)(?=\n###|\n##)', section, re.DOTALL)
        key_points_text = key_points_match.group(1).strip() if key_points_match else ""
        # Split key points into individual lines, removing leading dashes and whitespace
        lecturer['Key Points'] = [point.strip().lstrip('-').strip() for point in key_points_text.splitlines() if point.strip()]


        # Extract Date
        date_match = re.search(r'### Date\n(.*)', section)
        lecturer['Date'] = date_match.group(1).strip() if date_match else ""

        # Extract Context (if available)
        context_match = re.search(r'### Context\n(.*?)(?=\n###|\n##)', section, re.DOTALL)
        lecturer['Context'] = context_match.group(1).strip() if context_match else ""

        lecturers.append(lecturer)

    return lecturers


def write_to_csv(data, filename="lecturers.csv"):
    """
    Writes the extracted lecturer data to a CSV file.
    """
    if not data:
        print("No data to write to CSV.")
        return

    # Determine all possible keys to use as headers
    all_keys = set()
    for lecturer in data:
        all_keys.update(lecturer.keys())
    fieldnames = sorted(list(all_keys))  # Sort for consistency

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for lecturer in data:
             # Convert list of key points to a string for CSV writing.
            lecturer_copy = lecturer.copy() # Avoid modifying the original data
            if 'Key Points' in lecturer_copy:
                lecturer_copy['Key Points'] = "; ".join(lecturer_copy['Key Points'])

            writer.writerow(lecturer_copy)



if __name__ == "__main__":
    lecturer_data = extract_lecturer_data()
    write_to_csv(lecturer_data)
    print("Data extracted and saved to lecturers.csv")