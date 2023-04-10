import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def plot_3d_coordinates(df, n=30):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(df['X'][:n], df['Y'][:n], df['Z'][:n])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    # autoscale
    ax.axis('equal')
    plt.show()


def plot_cube(df, n):
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')
    for i in range(n):
        x = df.iloc[i]['X']
        y = df.iloc[i]['Y']
        z = df.iloc[i]['Z']
        ax.add_collection3d(Poly3DCollection([[(x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z)],
                                              [(x, y, z), (x, y + 1, z), (x, y + 1, z + 1), (x, y, z + 1)],
                                              [(x, y, z), (x, y, z + 1), (x + 1, y, z + 1), (x + 1, y, z)],
                                              [(x + 1, y, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1),
                                               (x + 1, y, z + 1)],
                                              [(x, y + 1, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1),
                                               (x, y + 1, z + 1)],
                                              [(x, y, z + 1), (x + 1, y, z + 1), (x + 1, y + 1, z + 1),
                                               (x, y + 1, z + 1)]
                                              ], alpha=0.1, facecolor='blue', edgecolor='black'))
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_xlim([0, df['X'].max() + 1])
    ax.set_ylim([0, df['Y'].max() + 1])
    ax.set_zlim([0, df['Z'].max() + 1])
    plt.show()
