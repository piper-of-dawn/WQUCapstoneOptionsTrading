import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

def despine (ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    return ax

def set_axis_labels (ax, x_label, y_label):
    font= fm.FontProperties(fname='font/GeistMono.ttf')
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font)
    ax.set_xlabel(f"{x_label} →" if x_label else "X-axis", fontproperties=font, labelpad=10.0, loc='center')
    ax.set_ylabel(f"{y_label} →" if x_label else "X-axis", fontproperties=font, labelpad=12.0, loc='top')
    return ax


def set_title (ax, title):
    font_title= fm.FontProperties(fname='font/GeistMonoLight.ttf', size=18)
    ax.set_title(title, fontsize=20,fontproperties=font_title, loc='left', pad=20.0)
    return ax

def customise_x_ticks (ax, custom_labels):
    ax.set_xticklabels(custom_labels)
    return ax

def add_vlines (ax, x_ticks, y_ticks, color):
    ax.vlines(x=x_ticks , ymax=y_ticks.max(), ymin=y_ticks.min(), linewidth=0.75, linestyles='dashed',color="#182e3f", zorder=-1, alpha=0.4)
    return ax

def add_hlines (ax, x_ticks, y_ticks, color):
    ax.hlines(y=y_ticks , xmax=x_ticks.max(), xmin=x_ticks.min(), linewidth=0.75, linestyles='dashed',color="#182e3f", zorder=-1, alpha=0.4)
    return ax

def format_chart(func, *args, **kwargs):
    def wrapper(*args, **kwargs):
        # Set global font

        
        # Retrieve x, y, and color from kwargs
        x = kwargs.get('x')
        y = kwargs.get('y')
        color = kwargs.get('color', 'blue')  # Default color if not passed
        de_spine = kwargs.get('de_spine', True)
        title = kwargs.get('title', "Untitled")
        xlabel = kwargs.get('xlabel', 'xLabel')
        ylabel = kwargs.get('ylabel', 'yLabel')
        vertical_grid = kwargs.get('vertical_grid', False)
        horizontal_grid = kwargs.get('horizontal_grid', False)
        ticks_transform = kwargs.get('ticks_transform', None)
        footnote = kwargs.get('footnote', None)
        # Call the original function
        ax = func(*args, **kwargs)
        
        # Apply the desired formatting functions
        if de_spine:
            ax = despine(ax)
        ax = set_title(ax, title)
        ax = set_axis_labels(ax, f"{xlabel}", f"{ylabel}")
        
        # Customise x ticks and add vertical lines
        x_ticks = ax.get_xticks()
        y_ticks = ax.get_yticks()
        if ticks_transform is not None:
            print("Transforming x ticks")
            ax = customise_x_ticks(ax, ticks_transform(x_ticks))
        if vertical_grid:
            ax = add_vlines(ax, x_ticks, y_ticks, color)
        if horizontal_grid:
            ax = add_hlines(ax, x_ticks, y_ticks, color)
            
        if footnote:
            plt.tight_layout(rect=[0, 0.05, 1, 1])  # Adjust the bottom margin to leave space for the footnote
            ax.text(0.0, -0.15, footnote, transform=ax.transAxes, ha='left', fontsize=8, color='gray')
        
        return ax
    return wrapper

        