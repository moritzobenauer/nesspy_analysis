# Analyzing `nesspy` data


## Dynamical Order Disorder Transitions

The class `DynamicalOrderDisorder` expects a parent folder with `out.csv` files in subfolders. Every `out.csv` file corresponds to measurements of an order parameter $m$ at a given $\beta \mu$. 

```python
DynamicalOrderDisorder.analysis(bootstrap=True, n_bootstrap, type, n_samples)
```

`type` can be `"growth_speed"` or `"mu"`. Thermodynamic parameters need to be consistent for all simulations within one instance of `DynamicalOrderDisorder` and can be extracted as a `Thermos` object using `DynamicalOrderDisorder.extract_thermos_from_file()`. 