from pathlib import Path
import src.nesspy_analysis as npa
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__":
    base_path = Path("/Volumes/2025/100x400_EFF_3S_GROWTH")
    data = pd.DataFrame()
    files, csv_file_number = npa.iterdirs(base_path)
    for f in files:
        df, header = npa.read_csv(f)
        data = pd.concat([data, df], ignore_index=True)
    data = data.sort_values(by=["mu"])
    # print(data)
    color = plt.cm.tab10(0)
    speed_cont = np.linspace(data['growth_speed'].min(), data['growth_speed'].max(), 5000)
    mu_cont = np.linspace(data['mu'].min(), data['mu'].max(), 5000)
    # plt.scatter(data['growth_speed'], data['susc'], label='derivative', color='red')
    plt.scatter(data['mu'], data['susc'], label='derivative', color=color)
    popt, pcov = npa.fit_lorentzian(data['mu'], data['susc'])
    x0, gamma, A = popt
    lorentzian_fit = npa.lorentzian(mu_cont, x0, gamma, A)
    plt.plot(mu_cont, lorentzian_fit, label='100', color=color)
    print('Peak Position (x0):', x0)
    print('Width (gamma):', gamma)

    base_path = Path("/Volumes/2025/80x320_EFF_3S_GROWTH")
    data = pd.DataFrame()
    files, csv_file_number = npa.iterdirs(base_path)
    for f in files:
        df, header = npa.read_csv(f)
        data = pd.concat([data, df], ignore_index=True)
    data = data.sort_values(by=["mu"])
    # print(data)
    color = plt.cm.tab10(1)
    speed_cont = np.linspace(data['growth_speed'].min(), data['growth_speed'].max(), 5000)
    mu_cont = np.linspace(data['mu'].min(), data['mu'].max(), 5000)
    # plt.scatter(data['growth_speed'], data['susc'], label='derivative', color='red')
    plt.scatter(data['mu'], data['susc'], label='derivative', color=color)
    popt, pcov = npa.fit_lorentzian(data['mu'], data['susc'])
    x0, gamma, A = popt
    lorentzian_fit = npa.lorentzian(mu_cont, x0, gamma, A)
    plt.plot(mu_cont, lorentzian_fit, label='80', color=color)
    print('Peak Position (x0):', x0)
    print('Width (gamma):', gamma)

    base_path = Path("/Volumes/2025/40x160_EFF_3S_GROWTH")
    data = pd.DataFrame()
    files, csv_file_number = npa.iterdirs(base_path)
    for f in files:
        df, header = npa.read_csv(f)
        data = pd.concat([data, df], ignore_index=True)
    data = data.sort_values(by=["mu"])
    # print(data)
    color = plt.cm.tab10(2)
    speed_cont = np.linspace(data['growth_speed'].min(), data['growth_speed'].max(), 5000)
    mu_cont = np.linspace(data['mu'].min(), data['mu'].max(), 5000)
    # plt.scatter(data['growth_speed'], data['susc'], label='derivative', color='red')
    plt.scatter(data['mu'], data['susc'], label='derivative', color=color)
    popt, pcov = npa.fit_lorentzian(data['mu'], data['susc'])
    x0, gamma, A = popt
    lorentzian_fit = npa.lorentzian(mu_cont, x0, gamma, A)
    plt.plot(mu_cont, lorentzian_fit, label='40', color=color)
    print('Peak Position (x0):', x0)
    print('Width (gamma):', gamma)

    base_path = Path("/Volumes/2025/30x120_EFF_3S_GROWTH")
    data = pd.DataFrame()
    files, csv_file_number = npa.iterdirs(base_path)
    for f in files:
        df, header = npa.read_csv(f)
        data = pd.concat([data, df], ignore_index=True)
    data = data.sort_values(by=["mu"])
    # print(data)
    color = plt.cm.tab10(3)
    speed_cont = np.linspace(data['growth_speed'].min(), data['growth_speed'].max(), 5000)
    mu_cont = np.linspace(data['mu'].min(), data['mu'].max(), 5000)
    # plt.scatter(data['growth_speed'], data['susc'], label='derivative', color='red')
    plt.scatter(data['mu'], data['susc'], label='derivative', color=color)
    popt, pcov = npa.fit_lorentzian(data['mu'], data['susc'])
    x0, gamma, A = popt
    lorentzian_fit = npa.lorentzian(mu_cont, x0, gamma, A)
    plt.plot(mu_cont, lorentzian_fit, label='30', color=color)
    print('Peak Position (x0):', x0)
    print('Width (gamma):', gamma)

    plt.legend()



    # plt.xscale('log')
    plt.show()