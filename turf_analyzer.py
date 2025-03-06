import pandas as pd
import numpy as np
from itertools import combinations

class TURFAnalyzer:
    def __init__(self, data):
        """
        Initialize the TURF Analyzer with respondent-level data

        Parameters:
        data (pd.DataFrame): DataFrame where:
            - Each row is a respondent
            - Each column is a feature
            - Values are binary (0/1 or True/False)
        """
        self.data = data
        self.features = data.columns.tolist()
        self.n_respondents = len(data)

    def calculate_combined_reach(self, feature_combination):
        """
        Calculate the total reach for a combination of features

        Parameters:
        feature_combination (list): List of features to combine

        Returns:
        float: Number of respondents reached by at least one feature
        """
        if not feature_combination:
            return 0

        # Get the subset of data for selected features
        subset = self.data[list(feature_combination)]

        # A respondent is reached if any feature reaches them (any 1/True in the row)
        reached = subset.any(axis=1)

        # Return the count of reached respondents
        return reached.sum()

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
        reach_percentages = []

        # Early optimization - get individual reach values first
        individual_reach = {feature: self.calculate_combined_reach([feature]) 
                          for feature in self.features}

        # Sort features by individual reach for faster convergence
        sorted_features = sorted(self.features, 
                               key=lambda x: individual_reach[x], 
                               reverse=True)

        # Try combinations of different sizes
        for size in range(1, max_combinations + 1):
            # Only try combinations with high-potential features first
            for combo in combinations(sorted_features[:min(len(sorted_features), size + 5)], size):
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
            reach_percentages.append(current_reach / self.n_respondents * 100)

        return {
            'best_combination': best_combination,
            'max_reach': max_reach,
            'incremental_reach': incremental_reach,
            'reach_percentages': reach_percentages,
            'total_respondents': self.n_respondents
        }