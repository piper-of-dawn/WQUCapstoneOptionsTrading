import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN

class DBSCANOutlierDetector:
    def __init__(self, eps=0.3, min_samples=10):
        """
        Initialize the DBSCAN outlier detector
        
        Parameters:
        -----------
        eps : float
            The maximum distance between two samples for them to be considered neighbors
        min_samples : int
            The number of samples in a neighborhood for a point to be considered a core point
        """
        self.eps = eps
        self.min_samples = min_samples
        self.scaler = StandardScaler()
        self.dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        self.is_fitted = False
        
    def fit(self, atm_vol, otm_vol):
        """
        Fit the DBSCAN model on the training data
        
        Parameters:
        -----------
        atm_vol : array-like
            ATM volatility values
        otm_vol : array-like
            OTM volatility values
        
        Returns:
        --------
        self : object
            Returns self
        """
        X = np.column_stack([atm_vol, otm_vol])
        self.X_train = X
        
        # Fit and transform the scaler
        self.X_scaled = self.scaler.fit_transform(X)
        
        # Fit DBSCAN
        self.clusters = self.dbscan.fit_predict(self.X_scaled)
        
        # Store core samples and their labels
        self.core_samples_mask = np.zeros_like(self.dbscan.labels_, dtype=bool)
        self.core_samples_mask[self.dbscan.core_sample_indices_] = True
        
        self.is_fitted = True
        return self
    
    def predict(self, atm_vol, otm_vol):
        """
        Predict if new points are outliers
        
        Parameters:
        -----------
        atm_vol : float or array-like
            ATM volatility value(s)
        otm_vol : float or array-like
            OTM volatility value(s)
            
        Returns:
        --------
        is_outlier : bool or array of bool
            True if point is an outlier, False otherwise
        distance : float or array of float
            Distance to nearest core point
        nearest_cluster : int or array of int
            Nearest cluster label (-1 if outlier)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Convert inputs to 2D array
        if np.isscalar(atm_vol) and np.isscalar(otm_vol):
            X_new = np.array([[atm_vol, otm_vol]])
        else:
            X_new = np.column_stack([atm_vol, otm_vol])
        
        # Scale the new points
        X_new_scaled = self.scaler.transform(X_new)
        
        # Initialize results
        is_outlier = np.ones(len(X_new), dtype=bool)
        min_distances = np.inf * np.ones(len(X_new))
        nearest_clusters = -1 * np.ones(len(X_new), dtype=int)
        
        # For each new point
        for i, point in enumerate(X_new_scaled):
            # Calculate distances to all core points
            core_points = self.X_scaled[self.core_samples_mask]
            core_labels = self.clusters[self.core_samples_mask]
            
            if len(core_points) > 0:
                # Calculate distances to all core points
                distances = np.linalg.norm(core_points - point, axis=1)
                min_dist = np.min(distances)
                min_dist_idx = np.argmin(distances)
                
                # If within eps of a core point, it's not an outlier
                if min_dist <= self.eps:
                    is_outlier[i] = False
                    nearest_clusters[i] = core_labels[min_dist_idx]
                
                min_distances[i] = min_dist
        
        if len(X_new) == 1:
            return bool(is_outlier[0]), float(min_distances[0]), int(nearest_clusters[0])
        return is_outlier, min_distances, nearest_clusters

# Example usage
def demonstrate_usage():
    # Create synthetic data
    np.random.seed(42)
    atm_vol = np.random.normal(0.5, 0.1, 100)
    otm_vol = np.random.normal(0.6, 0.1, 100)
    
    # Add some outliers
    atm_vol = np.append(atm_vol, [0.1, 0.9])
    otm_vol = np.append(otm_vol, [0.2, 1.0])
    
    # Create and fit the detector
    detector = DBSCANOutlierDetector(eps=0.3, min_samples=10)
    detector.fit(atm_vol, otm_vol)
    
    # Check a new point
    new_atm = 0.48
    new_otm = 0.65
    
    is_outlier, distance, cluster = detector.predict(new_atm, new_otm)
    
    print(f"\nResults for point ({new_atm:.2f}, {new_otm:.2f}):")
    print(f"Is outlier: {is_outlier}")
    print(f"Distance to nearest core point: {distance:.3f}")
    print(f"Nearest cluster: {cluster}")
    
if __name__ == "__main__":
    demonstrate_usage()