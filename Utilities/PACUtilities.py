from decimal import Decimal, getcontext, ROUND_HALF_UP
import os
import re


def sanitize_folder_name(folder_name):
    """
    Sanitizes folder names by removing or replacing invalid characters.
    """
    # Replace invalid characters with underscores
    sanitized_name = re.sub(r'[<>:"/\\|?*]', "_", folder_name)
    return sanitized_name.strip()  # Strip leading/trailing spaces


def mass_extract(dpac, output_dir):
    """Mass extract PAC file content to a folder hierarchy."""
    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        for folder in dpac.toc:
            # Sanitize folder name for compatibility
            sanitized_folder_name = sanitize_folder_name(folder["folder_name"])
            folder_path = os.path.join(output_dir, sanitized_folder_name)

            # Create the folder if it doesn't exist
            os.makedirs(folder_path, exist_ok=True)

            for file in folder["files"]:
                file_name = file["file_name"].strip()
                pointer = file["file_pointer"]
                size = file["file_size"]

                # Skip invalid entries
                if not file_name or pointer <= 0 or size <= 0:
                    print(f"Skipping invalid file: {file}")
                    continue

                try:
                    # Construct full output path for the file
                    output_path = os.path.join(folder_path, file_name)

                    # Read the file content
                    with open(dpac.file_path, "rb") as dpac_file:
                        dpac_file.seek(pointer)
                        data = dpac_file.read(size)

                    # Write to the output file
                    with open(output_path, "wb") as output_file:
                        output_file.write(data)

                    print(f"Extracted {file_name} to {output_path}")
                except Exception as file_error:
                    print(f"Failed to extract file {file_name}: {file_error}")
    except Exception as e:
        print(f"Error in mass_extract: {e}")
        raise
def format_size(size, decimal_places=2, use_binary=False):
    """
    Formats file size into human-readable units with high precision using the decimal module.

    Args:
        size (int | float): File size in bytes.
        decimal_places (int): Number of decimal places for precision. Default is 2.
        use_binary (bool): Whether to use binary (IEC) units (KiB, MiB) or decimal (SI) units. Default is False.

    Returns:
        str: Human-readable size string.

    Raises:
        ValueError: If size is negative or not a number.
    """
    if not isinstance(size, (int, float)):
        raise ValueError("Size must be an integer or float representing bytes.")
    if size < 0:
        raise ValueError("Size cannot be negative.")

    # Set decimal precision and rounding
    getcontext().prec = (
        decimal_places + 5
    )  # Set higher precision to minimize rounding errors
    getcontext().rounding = ROUND_HALF_UP

    size = Decimal(size)  # Convert to Decimal for precise arithmetic

    # Choose the appropriate unit system
    units = (
        ["B", "KB", "MB", "GB", "TB", "PB", "EB"]
        if not use_binary
        else ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"]
    )
    unit_step = Decimal(1024) if use_binary else Decimal(1000)

    # Iteratively divide size to determine the appropriate unit
    for unit in units:
        if size < unit_step:
            break
        size /= unit_step

    # Format the result to the specified number of decimal places
    size = size.quantize(Decimal(f"1.{'0' * decimal_places}"))  # Precise rounding

    return f"{size} {unit}"