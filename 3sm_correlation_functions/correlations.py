import numpy as np
import matplotlib.pyplot as plt


def compute_spatial_correlation_function(lattice, max_distance, target1, target2):
    # Initialize array to store correlation values for each distance
    correlation_by_distance = [[] for _ in range(max_distance + 1)]
    
    # Find all sites with target1
    target1_sites = np.argwhere(lattice == target1)
    
    if len(target1_sites) == 0:
        return np.zeros(max_distance + 1)
    
    # For each target1 site, compute correlations with target2 at all distances
    for site in target1_sites:
        print(site)
        for distance in range(max_distance + 1):
            # Find all sites at this distance from current site
            for other_site in np.argwhere(lattice == target2):
                manhattan_dist = np.sum(np.abs(site - other_site))
                if manhattan_dist == distance:
                    correlation_by_distance[distance].append(1)
                elif distance > 0 and manhattan_dist < distance + 1:
                    correlation_by_distance[distance].append(0)
    
    # Compute average correlation for each distance
    avg_correlation = np.array([
        np.mean(values) if len(values) > 0 else 0 
        for values in correlation_by_distance
    ])
    
    return avg_correlation


def densities_along_axis(lattice, axis):
    if axis == 0:
        num_cols = lattice.shape[1]
        densities = []
        for col in range(num_cols):
            column = lattice[:, col]
            total = len(column)
            counts = {0: np.sum(column == 0), 1: np.sum(column == 1), 2: np.sum(column == 2)}
            densities.append({k: v / total for k, v in counts.items()})
        return densities
    elif axis == 1:
        num_rows = lattice.shape[0]
        densities = []
        for row in range(num_rows):
            row_data = lattice[row, :]
            total = len(row_data)
            counts = {0: np.sum(row_data == 0), 1: np.sum(row_data == 1), 2: np.sum(row_data == 2)}
            densities.append({k: v / total for k, v in counts.items()})
        return densities


if __name__ == "__main__":
    lattice = np.load('final_state.npy')
    # plt.imshow(lattice, cmap='viridis')
    # plt.colorbar()
    # plt.show()


    overall_counts = {0: np.sum(lattice == 0), 1: np.sum(lattice == 1), 2: np.sum(lattice == 2)}


    densities_along_y = densities_along_axis(lattice, axis=1)

    for species in [0, 1, 2]:
        densities = [d[species] for d in densities_along_y]
        densities = [d / overall_counts[species] for d in densities]
        plt.plot(densities, marker='o', label=f'Species {species}')
    plt.xlabel('Position along y-axis')
    plt.ylabel('Density')
    plt.legend()
    plt.grid()
    plt.show()

    max_distance = 8
    target1 = 1
    target2 = 2




    # correlation_function = compute_spatial_correlation_function(lattice, max_distance, target1, target2)
    # plt.plot(correlation_function, marker='o', label=f'Correlation between {target1} and {target2}')

    # max_distance = 8
    # target1 = 1
    # target2 = 0

    # correlation_function = compute_spatial_correlation_function(lattice, max_distance, target1, target2)
    # plt.plot(correlation_function, marker='o', label=f'Correlation between {target1} and {target2}')

    plt.title('Spatial Correlation Function')
    plt.xlabel('Distance')
    plt.ylabel('Correlation')
    plt.grid()
    plt.show()

