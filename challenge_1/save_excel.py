import shutil
from datetime import datetime
import os

def make_backup_with_timestamp(file_path):
    """Creates a backup of the Excel file with a timestamp in the filename."""
    
    # Extract the file directory, name, and extension
    file_dir, file_name = os.path.split(file_path)
    file_name_no_ext, file_ext = os.path.splitext(file_name)

    # Get the current timestamp and format it (e.g., "20241022_152030")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Create the new filename with the timestamp
    backup_file_name = f"{file_name_no_ext}_{timestamp}{file_ext}"
    backup_file_path = os.path.join(file_dir, backup_file_name)

    # Copy the file to the new backup location
    shutil.copyfile(file_path, backup_file_path)

    print(f"Backup created: {backup_file_path}")

# Example usage
file_path = './challenge_1/results.xlsx'
make_backup_with_timestamp(file_path)
