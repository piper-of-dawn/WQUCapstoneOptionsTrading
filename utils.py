import numpy as np
from scipy import stats

def calculate_ks_statistic(array1, array2):
    # Remove null values
    array1 = array1[~np.isnan(array1)]
    array2 = array2[~np.isnan(array2)]
    
    # Ensure arrays are not empty after removing nulls
    if len(array1) == 0 or len(array2) == 0:
        raise ValueError("One or both arrays are empty after removing null values")
    
    # Calculate K-S statistic
    ks_statistic, _ = stats.ks_2samp(array1, array2)
    
    return ks_statistic

# Example usage:
# a1 = np.array([1, 2, 3, np.nan, 5, 6])
# a2 = np.array([2, 3, 4, 5, 6, 7, np.nan, 9])
# result = calculate_ks_statistic(a1, a2)
# print(f"K-S statistic: {result}")