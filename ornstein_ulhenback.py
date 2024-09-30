
from vol_utils import get_volatility_array
import numpy as np
from functools import lru_cache

@lru_cache(128)
def estimate_OU_parameters(ticker):
    vol = get_volatility_array(ticker) * np.sqrt(252) # Annualize the volatility
    dt = 1/252
    X = vol[:-1] # All but the last element
    Y = vol[1:] # All but the first element
    N = len(vol)
    Sx = np.sum(X)
    Sy = np.sum(Y)
    Sxx = X @ X
    Sxy = X @ Y
    Syy = Y @ Y
    theta_mle = (Sy * Sxx - Sx * Sxy) / (N * (Sxx - Sxy) - (Sx**2 - Sx * Sy))
    kappa_mle = -(1 / dt) * np.log(
        (Sxy - theta_mle * Sx - theta_mle * Sy + N * theta_mle**2) / (Sxx - 2 * theta_mle * Sx + N * theta_mle**2)
    )
    sigma2_hat = (
        Syy
        - 2 * np.exp(-kappa_mle * dt) * Sxy
        + np.exp(-2 * kappa_mle * dt) * Sxx
        - 2 * theta_mle * (1 - np.exp(-kappa_mle * dt)) * (Sy - np.exp(-kappa_mle * dt) * Sx)
        + N * theta_mle**2 * (1 - np.exp(-kappa_mle * dt)) ** 2
    ) / N
    sigma_mle = np.sqrt(sigma2_hat * 2 * kappa_mle / (1 - np.exp(-2 * kappa_mle * dt)))
    results  = {
                "ticker":ticker,
                "kappa":kappa_mle,
                "theta":theta_mle,
                "sigma":sigma_mle,
                "vol0":vol[-1]
            }
    return results