import pandas as pd
import numpy as np

def validate_data(df):
    """
    Validate the input data format
    
    Parameters:
    df (pd.DataFrame): Input DataFrame
    
    Returns:
    bool: True if valid, False otherwise
    """
    required_columns = {'Feature', 'Reach'}
    
    # Check if required columns exist
    if not all(col in df.columns for col in required_columns):
        return False
    
    # Check if there are any null values
    if df[list(required_columns)].isnull().any().any():
        return False
    
    # Check if reach values are numeric and positive
    if not all(df['Reach'].apply(lambda x: isinstance(x, (int, float)) and x > 0)):
        return False
    
    # Check if features are unique
    if len(df['Feature'].unique()) != len(df['Feature']):
        return False
    
    return True

def create_sample_data():
    """
    Create sample data for demonstration
    
    Returns:
    pd.DataFrame: Sample reach data
    """
    sample_data = {
        'Feature': [
            'Email Newsletter',
            'Social Media Ads',
            'Search Engine Marketing',
            'Content Marketing',
            'Display Advertising',
            'Influencer Marketing'
        ],
        'Reach': [
            15000,
            25000,
            20000,
            12000,
            18000,
            22000
        ]
    }
    
    return pd.DataFrame(sample_data)
