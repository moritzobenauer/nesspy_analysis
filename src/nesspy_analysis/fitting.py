from scipy import odr
from scipy.optimize import curve_fit
import numpy as np

def model_tanh(B, x):
    return -0.5 * (np.tanh(B[0] * (x - B[1])) - 1) + B[2]


def tanh_curve(x, f1: float, f2: float):
    return -0.5 * (np.tanh(f1 * (x - f2)) - 1)
    


def error_fit_2d_logS(x, y, dy, name):

    # Estimating B[0] and B[1] for the model

    popt_tanh, pcov_tanh = curve_fit(tanh_curve, x, y, p0=[10, np.mean(x)])
    b0, b1 = popt_tanh
    print(b0,b1)
    model = odr.Model(pseudo_tanh_model)
    mydata = odr.RealData(x, y, sy=dy)

    myodr = odr.ODR(mydata, model, beta0=[0.0, 1.0, np.mean(x)])
    myoutput = myodr.run()
    myoutput.pprint()

    return myoutput.beta


def pseudo_tanh_model(B: list=[0.2, 1.0, 2.0], x=None):

    L, k, x0 = B
    t0 = np.tanh(k * x0)
    g  = (np.tanh(k * (x - x0)) + t0) / (1 + t0)
    return 1 - (1 - L) * g**2

def lorentzian(x, x0, gamma, A):
        return A * gamma**2 / ((x - x0)**2 + gamma**2)

def fit_lorentzian(xdata, ydata):
    popt, pcov = curve_fit(lorentzian, xdata, ydata, p0=[1, np.mean(xdata), 1])
    return popt, pcov