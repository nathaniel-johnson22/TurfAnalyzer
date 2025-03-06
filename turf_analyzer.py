import pandas as pd
import numpy as np
from itertools import combinations

class TURFAnalyzer:
    def __init__(self, data):
        """
        Initialize the TURF Analyzer with reach data
        
        Parameters:
        data (pd.DataFrame): DataFrame with columns 'Feature' and 'Reach'
        """
        self.data = data
        self.features = data['Feature'].tolist()
        self.reach_values = data['Reach'].tolist()

    def calculate_combined_reach(self, feature_combination):
        """
        Calculate the total reach for a combination of features
        
        Parameters:
        feature_combination (list): List of features to combine
        
        Returns:
        float: Combined reach value
        """
        # In a real implementation, this would use actual overlap data
        # For this implementation, we'll use a simplified approach
        individual_reaches = [
            self.data[self.data['Feature'] == feature]['Reach'].iloc[0]
            for feature in feature_combination
        ]
        
        # Assume some overlap between features (70% of perfect addition)
        combined_reach = sum(individual_reaches) * 0.7
        
        # Ensure the combined reach doesn't exceed the maximum possible
        max_possible = max(individual_reaches) * 1.5
        return min(combined_reach, max_possible)

    def analyze(self, max_combinations):
        """
        Perform TURF analysis to find optimal feature combinations
        
        Parameters:
        max_combinations (int): Maximum number of features to combine
        
        Returns:
        dict: Analysis results including best combination and reach values
        """
        best_combination = []
        max_reach = 0
        incremental_reach = []

        # Try combinations of different sizes
        for size in range(1, max_combinations + 1):
            for combo in combinations(self.features, size):
                reach = self.calculate_combined_reach(combo)
                
                if reach > max_reach:
                    max_reach = reach
                    best_combination = list(combo)

        # Calculate incremental reach
        current_reach = 0
        for i in range(len(best_combination)):
            current_combo = best_combination[:i+1]
            current_reach = self.calculate_combined_reach(current_combo)
            incremental_reach.append(current_reach)

        return {
            'best_combination': best_combination,
            'max_reach': max_reach,
            'incremental_reach': incremental_reach
        }
