# Analyzing `nesspy` output data

## Static Classes

### Thermodynamic Properties of a System

Thermodynamic properties of a system that can be used in FLEX calculations or analysis can be saved in the `Thermos` class. 

### Lattice Properties

The `Lattice` class saves the dimensions as well as details about the periodic boundary conditions of a given simulation.



## Analysis Classes
### Dynamical Order Disorder Transitions

The class `DynamicalOrderDisorder` expects a parent folder with `out.csv` files in subfolders. Every `out.csv` file corresponds to measurements of an order parameter $m$ at a given $\beta \mu$. 

```python
DynamicalOrderDisorder.analysis(bootstrap=True, n_bootstrap, type, n_samples)
```

`type` can be `"growth_speed"` or `"mu"`. Thermodynamic parameters need to be consistent for all simulations within one instance of `DynamicalOrderDisorder` and can be extracted as a `Thermos` object using `DynamicalOrderDisorder.extract_thermos_from_file()`. 

### Multiple Simulations
To easily get the raw output data from multiple simulations an instance of the class `MultipleSimulations` can be initiated and the `get_raw_data()` method returns the a combined data frame.