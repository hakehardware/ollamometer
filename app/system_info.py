"""
System information utilities for hardware comparison
"""


def get_compute_mode(ram_mb: float, vram_mb: float) -> str:
    """
    Determine compute mode based on RAM/VRAM usage

    Args:
        ram_mb: Total RAM usage in MB
        vram_mb: VRAM usage in MB

    Returns:
        'CPU-only', 'Full GPU', or 'Hybrid (GPU+CPU)'
    """
    if vram_mb == 0:
        return 'CPU-only'
    elif vram_mb >= ram_mb * 0.95:  # Within 5% tolerance
        return 'Full GPU'
    else:
        return 'Hybrid (GPU+CPU)'
