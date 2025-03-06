import pandas as pd
import numpy as np

def validate_data(df):
    """
    Validate the input data format

    Parameters:
    df (pd.DataFrame): Input DataFrame where:
        - Each row represents a respondent
        - Each column represents a feature
        - Values are binary (0/1 or True/False)

    Returns:
    bool: True if valid, False otherwise
    """
    # Check if there are any columns (features)
    if len(df.columns) == 0:
        return False

    # Check if there are any rows (respondents)
    if len(df) == 0:
        return False

    # Check if all values are binary (0/1 or True/False)
    for col in df.columns:
        unique_vals = df[col].unique()
        valid_values = {0, 1, True, False}
        if not set(unique_vals).issubset(valid_values):
            return False

    return True

def create_sample_data():
    """
    Create sample data for demonstration

    Returns:
    pd.DataFrame: Sample respondent-level data with binary feature indicators
    """
    np.random.seed(42)
    n_respondents = 100
    features = [
        'Email Newsletter',
        'Social Media Ads',
        'Search Engine Marketing',
        'Content Marketing',
        'Display Advertising',
        'Influencer Marketing'
    ]

    # Generate random binary data
    data = np.random.randint(0, 2, size=(n_respondents, len(features)))
    df = pd.DataFrame(data, columns=features)

    return df