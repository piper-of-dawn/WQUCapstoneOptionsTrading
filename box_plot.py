import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from format import format_chart

@format_chart
def plot_multi_boxplot(data_list, category_dict, xlabel, ylabel, title, figsize=(12, 8)):
    """
    Create a multi-box plot from a list of (name, array) tuples, sorted by mean values,
    with colors based on categories.
    
    Args:
    data_list (list of tuples): List of (name, array) tuples.
    category_dict (dict): Dictionary mapping tickers to categories.
    xlabel (str): Label for x-axis.
    ylabel (str): Label for y-axis.
    title (str): Title of the plot.
    figsize (tuple): Figure size (width, height) in inches.
    
    Returns:
    matplotlib.axes.Axes: The axes object containing the plot.
    """
    # Predefined color palette
    
    # Create a DataFrame from the data list
    df = pd.DataFrame({name: pd.Series(array) for name, array in data_list})
    
    # Calculate means and sort columns by mean
    means = df.median().sort_values()
    df_sorted = df[means.index]
    
    # Melt the DataFrame to long format
    df_melted = df_sorted.melt(var_name='Distribution', value_name='Value')
    

    

    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create the box plot
    sns.boxplot(x='Distribution', y='Value', data=df_melted, ax=ax, 
                order=means.index, 
                palette=[category_dict[category] for ticker in means.index])
    
    # Customize the plot
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    
    # Rotate x-axis labels if there are many distributions
    if len(data_list) > 4:
        plt.xticks(rotation=45, ha='right')
    
    # Add a legend
    handles = [plt.Rectangle((0,0),1,1, color=color) for category, color in category_color_dict.items()]
    plt.legend(handles, category_color_dict.keys(), title="Category", loc="upper left", bbox_to_anchor=(1, 1))
    
    # Adjust layout to prevent clipping of labels and legend
    plt.tight_layout()
    
    return ax

# Example usage:
# import numpy as np
# import pandas as pd
#
# # Read the CSV file
# tickers_df = pd.read_csv('tickers.csv')
# category_dict = dict(zip(tickers_df['ticker'], tickers_df['category']))
#
# # Generate some example data
# data_list = [(ticker, np.random.normal(i, 1, 1000)) for i, ticker in enumerate(category_dict.keys())]
#
# # Plot the multi-box plot
# plot_multi_boxplot(data_list, category_dict, "Ticker", "Value", "Multi-Box Plot by Category")
# plt.show()