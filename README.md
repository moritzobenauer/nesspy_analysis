# The Idea


1. Give directory to `iterdir` which returns a `dict` with `{'mu': [], 'file': []}` as well as a dict with all of the important information that do not change within one directory like `{'xsize': int, 'ysize': int, 'df': float, ...}`. Check that these values are consistent throughtout all directories!

2. Iterate through `dict` to get `m, m2, v` etc. from every csv file using `read_csv` returning a `pd.DataFrame`. Calculate `dphi` as a function of `mu`.


3. Use this `pd.DataFrame` with `samples` for a bootstrapping analysis and fitting of `m` and `v` as a function of `dphi`. Return `pd.DataFrame` with `dphi`, `v`, and `m` for later usage. Also have a `np.array` for the continous fitted values!
