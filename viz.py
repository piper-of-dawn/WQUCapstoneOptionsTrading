import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from format import format_chart

@format_chart
def plot_multivariate_kernel_density(x, y):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot the 2D kernel density estimate
    sns.kdeplot(
        x=x, 
        y=y, 
        fill=True,
        cmap="rocket_r",
        cbar=True,
        ax=ax
    )

    ax.scatter(x, y,s=3.0, alpha=0.5)
    

    
    # Add colorbar label
    cbar = ax.collections[0].colorbar
    cbar.set_label('Density')
    
    return ax
# plot_multivariate_kernel_density(x, y, xlabel='Realized Volatility', ylabel='Implied Volatility', title='NVDA Implied Volatility vs Realized Volatility')


import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from format import format_chart

@format_chart
def plot_multiple_kde(data_list, category_dict, xlabel="Density", ylabel="Support", title="KDE", figsize=(12, 8)):  
    # Predefined color palette
    colors = ['#0F2573', '#735D0F', '#294F50', '#502A29', '#525266', '#666652', '#04335A', '#5A2B04', '#EEF4CE','#D4CEF4', '#81A1C1', '#4C566A']
    
    fig, ax = plt.subplots(figsize=figsize)
    
    

    # Plot KDE for each array
    for name, array in data_list:
        category = tickers_data.filter(pl.col('ticker') == name).select('category').item()
        color = category_dict.get(category, "#000000")  # Use black if color is not found
        sns.kdeplot(data=array, ax=ax, label=f"{name} ({category})", color=color, fill=True, alpha=0.3)
    
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    
    # Add a legend
    # handles = [plt.Rectangle((0,0),1,1, color=color) for category, color in category_dict.items()]
    ax.legend(title="Category", loc="upper left", bbox_to_anchor=(1, 1))
    
    # Adjust layout to prevent clipping of labels and legend
    plt.tight_layout()
    
    return ax
