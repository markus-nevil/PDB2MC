import pandas as pd
import numpy as np
import pdb_manipulation as pdbm


def create_sphere(radius, center, num_points):
    theta = np.linspace(0, np.pi, num_points)
    phi = np.linspace(0, 2 * np.pi, num_points)
    theta, phi = np.meshgrid(theta, phi)

    x = center[0] + (radius * np.sin(theta) * np.cos(phi)).astype(int)
    y = center[1] + (radius * np.sin(theta) * np.sin(phi)).astype(int)
    z = center[2] + (radius * np.cos(theta)).astype(int)

    data = {'X': x.ravel(), 'Y': y.ravel(), 'Z': z.ravel()}
    df = pd.DataFrame(data)
    return df

# Set numpy print options to display all elements
np.set_printoptions(threshold=np.inf)

# Create a sphere DataFrame
sphere_radius = 4
sphere_center = (8, 8, 8)
num_points = 16
sphere_df = create_sphere(sphere_radius, sphere_center, num_points)

coord = pdbm.rasterized_sphere(3)
# print(coord)
center = pdbm.sphere_center(3)
shortened = {'X': [50, 60], 'Y': [50, 60], 'Z': [50, 60]}

sphere_df = pdbm.add_sphere_coordinates(coord, center, shortened)

surface_array = pdbm.construct_surface_array(sphere_df)
print(surface_array)

print("and now filled:\n")
surface_array = pdbm.paint_bucket_fill(surface_array, fill_value=111)
print(surface_array)