import nesspy_analysis as npa
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pickle

base_path = Path("/Volumes/2025/research_nov_2025_data/ML_F0_D8_K1_SCHEME_6_BJ")

analysis_2 = npa.DynamicalOrderDisorder("mu8", base_path)



class MyUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        # Redirect the old class to the new one
        # if module == "nesspy.src" and name == "Thermos":
        return npa.Thermos
        # return super().find_class(module, name)

with open(base_path / "Thermos", "rb") as f:
    obj = MyUnpickler(f).load()

print(obj)