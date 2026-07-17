from importlib.metadata import version, PackageNotFoundError

def print_verbose_startup():
    try:
        pkg_version = version("nesspy_analysis")
    except PackageNotFoundError:
        pkg_version = "unknown"
    
    print(
        f"""
    _ __   ___  ___ ___ _ __  _   _  
| '_ | / _ |/ __/ __| '_ || | | | 
| | | |  __/|__ |__ | |_) | |_| | 
|_| |_||___||___/___/ .__/ |__, | 
                    |_|    |___/  

\033[1m MLO @ Princeton University, 2024-2026 \033[0m
\033[1m https://github.com/moritzobenauer/nesspy \033[0m
            
v{pkg_version}
            
-------------------------------------------------------------------------------------
| Kinetic Monte Carlo Lattice Gas Simulation for the 2x2 + 1 State Model            |
| Including Chemical Drive Δμ with spatially heterogeneous reaction networks        |
------------------------------------------------------------------------------------- 
-------------------------------------------------------------------------------------
ANALYSIS MODULE  \n
"""
    )