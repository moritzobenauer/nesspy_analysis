from scipy import odr
from scipy.optimize import curve_fit
import numpy as np
import warnings

# def model_tanh(B, x):
#     return -0.5 * (np.tanh(B[0] * (x - B[1])) - 1) + B[2]


# def tanh_curve(x, f1: float, f2: float):
#     return -0.5 * (np.tanh(f1 * (x - f2)) - 1)
    


# def error_fit_2d_logS(x, y, dy, name):

#     # Estimating B[0] and B[1] for the model

#     popt_tanh, pcov_tanh = curve_fit(tanh_curve, x, y, p0=[10, np.mean(x)])
#     b0, b1 = popt_tanh
#     print(b0,b1)
#     model = odr.Model(pseudo_tanh_model)
#     mydata = odr.RealData(x, y, sy=dy)

#     myodr = odr.ODR(mydata, model, beta0=[0.0, 1.0, np.mean(x)])
#     myoutput = myodr.run()
#     myoutput.pprint()

#     return myoutput.beta


# def pseudo_tanh_model(B: list=[0.2, 1.0, 2.0], x=None):

#     L, k, x0 = B
#     t0 = np.tanh(k * x0)
#     g  = (np.tanh(k * (x - x0)) + t0) / (1 + t0)
#     return 1 - (1 - L) * g**2

def polynomial(x, a, b, c, x0):
    return a * (x - x0) + b * (x - x0) ** 2 + c * (x - x0) ** 3

def fit_polynomial(xdata: None, ydata: None):

    if ydata is not None and xdata is not None:

        x_lin = np.array([xdata[0], xdata[1]])
        y_lin = np.array([ydata[0], ydata[1]])
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            m,b = np.polyfit(x_lin, y_lin, 1)
        initial_guess = [1, 1, 1, b/m]

        popt, pcov = curve_fit(polynomial, xdata, ydata, p0=initial_guess)
        return popt

def lorentzian(x, x0, gamma, A):
        return A * gamma**2 / ((x - x0)**2 + gamma**2)

def lorentzian_fit(B: list[float, float, float], x: np.ndarray):
        x0, gamma, A = B
        return A * gamma**2 / ((x - x0)**2 + gamma**2)

def fit_lorentzian(xdata, ydata, yerr=None):
    
    # Find the xvalue where ydata is maximum
    if ydata.size == 0:
        raise ValueError("ydata is empty")
    
    if len(xdata) != len(ydata):
        raise ValueError("xdata and ydata must have the same length")

    max_index = np.argmax(ydata)
    max_val = np.max(ydata)
    x0 = xdata[max_index]
    width = xdata[max_index + 1] - xdata[max_index - 1]
    # print("Initial guess for x0:", x0)

    if yerr is None:
        popt, pcov = curve_fit(lorentzian, xdata, ydata, p0=[x0, width, max_val], maxfev=10000)
        # print(np.mean(xdata))
        params = popt
    else:
        model = odr.Model(lorentzian_fit)
        mydata = odr.RealData(xdata, ydata, sy=yerr)
        myodr = odr.ODR(mydata, model, beta0=[x0, width, max_val])
        myoutput = myodr.run()
        # myoutput.pprint()

        # print(myoutput.beta)
        params = myoutput.beta

    return params