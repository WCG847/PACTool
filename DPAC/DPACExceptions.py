import hashlib
from typing import Final

# Define constants
ERROR_CODE_LENGTH: Final[int] = 8

def generate_error_code(seed: str) -> str:
    """
    Generate a reproducible 8-character error code derived from the provided seed string.

    This function uses the SHA-256 hashing algorithm to generate a unique identifier
    based on the input seed. Only the first 8 characters of the resulting hash (in uppercase)
    are returned as the error code.

    Parameters:
        seed (str): The input seed string used to generate the error code.

    Returns:
        str: An 8-character uppercase error code.

    Raises:
        ValueError: If the seed is not a valid string or is empty.
    """
    if not isinstance(seed, str) or not seed.strip():
        raise ValueError("The seed must be a non-empty string.")

    # Generate the SHA-256 hash of the input seed
    hash_object = hashlib.sha256(seed.encode())

    # Return the first ERROR_CODE_LENGTH characters of the hash, in uppercase
    return hash_object.hexdigest()[:ERROR_CODE_LENGTH].upper()



class DPACException(Exception):
    """Base class for DPAC-specific exceptions."""

    def __init__(self, message, error_identifier=None):
        """
        Initialises the exception with a reproducible error code.

        Args:
            message (str): Error message.
            error_identifier (str): An optional identifier for reproducible error codes. If not provided, uses the class name.
        """
        # Use class name or provided identifier as the seed for the error code
        seed = error_identifier or self.__class__.__name__
        self.error_code = generate_error_code(seed)
        self.message = message
        super().__init__(f"[{self.error_code}] {self.message}")


class InvalidDPACFileError(DPACException):
    """Raised when the DPAC file structure is invalid."""

    pass


class TOCParseError(DPACException):
    """Raised when the Table of Contents (TOC) cannot be parsed."""

    pass


class FileSizeResolutionError(DPACException):
    """Raised when a file size cannot be resolved."""

    pass


class ZeroTOCCountError(DPACException):
    """Raised when TOC returns zero files/folders."""

    pass

class DPACCreationError(DPACException):

    pass
