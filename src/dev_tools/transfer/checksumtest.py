import hashlib
import json
import os


CHECKSUM_STORAGE_FILENAME = "checksums.json"
script_dir = os.path.dirname(os.path.abspath(__file__))


def calculate_checksum(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def save_checksums(checksums, storage_path):
    with open(storage_path, "w") as file:
        json.dump(checksums, file, indent=4)


def load_checksums(storage_path):
    try:
        with open(storage_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def update_checksum(file, esp_name):
    """Update the checksum of a specified file."""   
    checksums_storage_path = os.path.join(script_dir, f"controlpanel-{esp_name}-checksums.json")
    
    # Load existing checksums
    checksums = load_checksums(checksums_storage_path)
    
    # Calculate new checksum
    new_checksum = calculate_checksum(file)
    
    # Update the checksum in the dictionary
    checksums[file] = new_checksum
    
    # Save the updated checksums
    save_checksums(checksums, checksums_storage_path)

    # print(f"Updated checksum for {file}: {new_checksum}")


def file_has_changed(path_to_file, esp_name):
    checksums_storage_path = os.path.join(script_dir, f"controlpanel-{esp_name}-checksums.json")
    
    # Load existing checksums from storage
    checksums = load_checksums(checksums_storage_path)

    # Calculate current checksum of the file
    if os.path.exists(path_to_file):
        current_checksum = calculate_checksum(path_to_file)
    else:
        return True

    # Get stored checksum, if available
    stored_checksum = checksums.get(path_to_file)

    # Determine if the file has changed
    if current_checksum != stored_checksum:
        # if update_checksums:
        #     checksums[path_to_file] = current_checksum
        #     save_checksums(checksums, CHECKSUM_STORAGE_PATH)
        return True
    else:
        return False
