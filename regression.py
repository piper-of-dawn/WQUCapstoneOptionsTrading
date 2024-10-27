import numpy as np
import matplotlib.pyplot as plt
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.diagnostic import acorr_breusch_godfrey, het_breuschpagan
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import scipy.stats as stats
import format
from importlib import reload
reload(format)
from format import format_chart, despine

class RegressionDiagnostics:
    def __init__(self, model, significance_level=0.05):
        self.model = model
        self.significance_level = significance_level
        self.results = {}

    def run_all_tests(self):
        self.durbin_watson_test()
        self.breusch_godfrey_test()
        self.normality_test()
        self.heteroskedasticity_test()

    def durbin_watson_test(self):
        dw_statistic = durbin_watson(self.model.resid)
        self.results['Durbin-Watson'] = {
            'statistic': dw_statistic,
            'concern': dw_statistic < 1.5 or dw_statistic > 2.5
        }

    def breusch_godfrey_test(self):
        bg_test = acorr_breusch_godfrey(self.model, nlags=5)
        self.results['Breusch-Godfrey'] = {
            'p-value': bg_test[1],
            'concern': bg_test[1] < self.significance_level
        }

    def normality_test(self):
        _, p_value = stats.normaltest(self.model.resid)
        self.results['Normality'] = {
            'p-value': p_value,
            'concern': p_value < self.significance_level
        }

    def heteroskedasticity_test(self):
        bp_test = het_breuschpagan(self.model.resid, self.model.model.exog)
        self.results['Breusch-Pagan'] = {
            'p-value': bp_test[1],
            'concern': bp_test[1] < self.significance_level
        }

 
    def plot_diagnostics(self):
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        # ACF plot
        plot_acf(self.model.resid, ax=ax1, lags=40)
        ax1.set_title('Autocorrelation Function')

        # PACF plot
        plot_pacf(self.model.resid, ax=ax2, lags=40)
        ax2.set_title('Partial Autocorrelation Function')

        # Q-Q plot
        stats.probplot(self.model.resid, dist="norm", plot=ax3)
        ax3.set_title("Q-Q plot of residuals")

        # Residuals vs Fitted plot
        ax4.scatter(self.model.fittedvalues, self.model.resid)
        ax4.set_xlabel("Fitted values")
        ax4.set_ylabel("Residuals")
        ax4.set_title("Residuals vs Fitted")
        [despine(ax) for ax in [ax1, ax2, ax3, ax4]]
        plt.tight_layout()
        return fig

    def present_concerns(self):
        concerns = []
        for test, result in self.results.items():
            if result['concern']:
                if test == 'Durbin-Watson':
                    concerns.append(f"{test} statistic is {result['statistic']:.2f}, indicating potential autocorrelation.")
                elif test in ['Breusch-Godfrey', 'Normality', 'Breusch-Pagan']:
                    concerns.append(f"{test} test p-value is {result['p-value']:.4f}, suggesting potential issues.")
        
        if concerns:
            print("Concerns detected:")
            for concern in concerns:
                print(f"- {concern}")
        else:
            print("No major concerns detected in the regression diagnostics.")

diagnostics = RegressionDiagnostics(m)
diagnostics.run_all_tests()
diagnostics.present_concerns()
diagnostics.plot_diagnostics()