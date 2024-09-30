from math import log, sqrt
from scipy.stats import norm
def get_delta (S, K, r, T, sigma, option_type):
    numerator = log(S/K) + (r + 0.5 * sigma ** 2) * T 
    denominator = sigma * sqrt(T)
    if option_type == 'call':
        delta = norm.cdf(numerator / denominator) 
    elif option_type == 'put':
        delta = norm.cdf(-numerator / denominator)-1
    else:
        raise ValueError(f'Option type {option_type} not supported')
    return delta

import pui