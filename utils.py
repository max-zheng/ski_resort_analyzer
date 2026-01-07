"""Shared utility functions for ski resort analysis."""


def calc_averages(ratings: list[dict]) -> dict:
    """Calculate average scores from a list of rating dictionaries.

    Args:
        ratings: List of rating dicts with numeric fields

    Returns:
        Dict with averaged values for each field plus a 'composite' score
    """
    if not ratings:
        return {}

    # Collect all numeric values by field name
    field_values: dict[str, list[float]] = {}
    for r in ratings:
        for field, value in r.items():
            if isinstance(value, (int, float)) and value is not None:
                if field not in field_values:
                    field_values[field] = []
                field_values[field].append(value)

    # Calculate averages
    avg = {field: sum(vals) / len(vals) for field, vals in field_values.items()}

    # Composite is average of all category scores (excluding snow_depth_inches)
    category_scores = [v for k, v in avg.items() if k != "snow_depth_inches"]
    avg["composite"] = sum(category_scores) / len(category_scores) if category_scores else 0

    return avg
