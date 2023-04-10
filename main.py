from pdb_manipulation import *
from plotting_functions import *
from minecraft_functions import *

if __name__ == '__main__':
    pdb_file = choose_file()
    pdb_df = read_pdb(pdb_file)

    pdb_name = get_pdb_code(pdb_file)

    scalar = 5.0
    clipped = clip_coords(pdb_df)
    scaled_two = scale_coordinates(clipped, scalar)
    moved = move_coordinates(scaled_two)
    rounded_two = round_df(moved)

    branches = sidechain(rounded_two)

    backbone = atom_subset(rounded_two, ['C', 'N', 'CA'], include=True)

    #sidechain = atom_subset(rounded_two, ['C', 'N', 'CA'], include=False)
    intermediate = find_intermediate_points(backbone)

    coord = rasterized_sphere((2, 2, 2), 1.5, (5, 5, 5))

    shortened = shorten_atom_names(rounded_two)
    spheres = add_sphere_coordinates(coord, (2, 2, 2), shortened)

    mcfunctions = choose_subdir("")

    pdb_backbone = pdb_name+"_backbone"
    create_minecraft_functions(intermediate, pdb_backbone, False, mcfunctions)

    pdb_sidechain = pdb_name+"_sidechain"
    create_minecraft_functions(branches, pdb_sidechain, False, mcfunctions)

    pdb_atoms = pdb_name+"_atoms"
    create_minecraft_functions(spheres, pdb_atoms, False, mcfunctions)

    mcfiles = find_mcfunctions(mcfunctions, pdb_name.lower())
    print(mcfiles)

    create_master_function(mcfiles, pdb_name, mcfunctions)


    #mc_backbone = create_minecraft_functions(intermediate)
    #mc_atoms = create_minecraft_functions(spheres)

    #print(mc_backbone.head(20))
    #print(mc_atoms.head(20))

    #combined = pd.concat([spheres.head(1500), intermediate.head(300), branches.head(500)])
    #combined = combined.reset_index(drop=True)
    #print(combined.head(20))
    #print(combined.tail(20))

    #plot_3d_coordinates(clip_coords(combined), 2300)
    #plot_3d_coordinates(clip_coords(spheres), 1900)
    #plot_cube(spheres, 300)

