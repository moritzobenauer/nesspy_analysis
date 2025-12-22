from pathlib import Path

def iterdirs(base_path: Path) -> tuple[list[Path], int]:
    if not base_path.exists():
            raise ValueError(f"Path {base_path} does not exist.")
    
    out_files = list(base_path.rglob("out.csv"))
    if not out_files:
        raise ValueError(f"No out.csv files found in {base_path}.")
    
    return (out_files, len(out_files))


def find_all_final_configs(base_path: Path) -> list[Path]:
    if not base_path.exists():
        raise ValueError(f"Path {base_path} does not exist.")
    
    out_files = list(base_path.rglob("lattice_final.npy"))
    if not out_files:
        raise ValueError(f"No final_config.npy files found in {base_path}.")
    
    return out_files