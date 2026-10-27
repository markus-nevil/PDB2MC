"""
Fast writer for Minecraft structure (.nbt) files.

Writes the same layout as nbt-structure-utils' NBTStructure.get_nbt(pressurize=False,
align_to_origin=False): a gzipped root compound with size, entities, blocks, palette and
DataVersion. Every block entry has the same fixed size, so the whole block list is built as
one numpy buffer instead of one Python object per block (about 100x faster for large models).
"""
import gzip
import struct

import numpy as np

# Data version nbt-structure-utils writes (Minecraft 1.19.3); newer versions upgrade it on load
DATA_VERSION = 3218
# nbt-structure-utils caps each 'size' axis at the old structure block limit; `place template`
# still places every block, so the cap is kept to write byte-for-byte the same files
MAX_SIZE = 32

TAG_END, TAG_INT, TAG_STRING, TAG_LIST, TAG_COMPOUND = 0, 3, 8, 9, 10


def _name(text):
    raw = text.encode("utf-8")
    return struct.pack(">H", len(raw)) + raw


def _int_list(name, values):
    return (bytes([TAG_LIST]) + _name(name) + bytes([TAG_INT]) + struct.pack(">i", len(values))
            + struct.pack(f">{len(values)}i", *values))


# One block compound: {pos: [x, y, z], state: n}
_BLOCK_DTYPE = np.dtype([
    ("pos_head", "S11"),   # TAG_List 'pos' of 3 TAG_Int
    ("pos", ">i4", (3,)),
    ("state_head", "S8"),  # TAG_Int 'state'
    ("state", ">i4"),
    ("end", "S1"),
])
_POS_HEAD = bytes([TAG_LIST]) + _name("pos") + bytes([TAG_INT]) + struct.pack(">i", 3)
_STATE_HEAD = bytes([TAG_INT]) + _name("state")


def namespaced(block):
    return block if ":" in block else f"minecraft:{block}"


def structure_bytes(coords, blocks):
    """Uncompressed NBT for blocks[i] placed at integer coords[i] (an (n, 3) array)."""
    coords = np.asarray(coords, dtype=np.int64).reshape(-1, 3)
    blocks = np.asarray(blocks, dtype=object)
    if len(coords) != len(blocks):
        raise ValueError("coords and blocks must have the same length")

    # Palette in order of first appearance, as nbt-structure-utils writes it
    names, first, states = np.unique(blocks.astype(str), return_index=True, return_inverse=True)
    order = np.argsort(first)
    remap = np.empty_like(order)
    remap[order] = np.arange(len(order))
    palette = [namespaced(name) for name in names[order]]

    entries = np.zeros(len(coords), dtype=_BLOCK_DTYPE)
    entries["pos_head"] = _POS_HEAD
    entries["pos"] = coords
    entries["state_head"] = _STATE_HEAD
    entries["state"] = remap[states.reshape(-1)] if len(coords) else 0
    entries["end"] = bytes([TAG_END])

    extent = coords.max(axis=0) - coords.min(axis=0) + 1 if len(coords) else np.zeros(3, dtype=int)
    size = np.minimum(extent, MAX_SIZE).tolist()
    out = [bytes([TAG_COMPOUND]) + _name(""),
           _int_list("size", size),
           bytes([TAG_LIST]) + _name("entities") + bytes([TAG_COMPOUND]) + struct.pack(">i", 0),
           bytes([TAG_LIST]) + _name("blocks") + bytes([TAG_COMPOUND]) + struct.pack(">i", len(coords)),
           entries.tobytes(),
           bytes([TAG_LIST]) + _name("palette") + bytes([TAG_COMPOUND]) + struct.pack(">i", len(palette))]
    for name in palette:
        out.append(bytes([TAG_STRING]) + _name("Name") + _name(name) + bytes([TAG_END]))
    out.append(bytes([TAG_INT]) + _name("DataVersion") + struct.pack(">i", DATA_VERSION))
    out.append(bytes([TAG_END]))
    return b"".join(out)


def write_structure(path, coords, blocks):
    """Write a gzipped structure file; returns path."""
    with gzip.open(path, "wb", compresslevel=6) as f:
        f.write(structure_bytes(coords, blocks))
    return path


def read_positions(path):
    """Block positions of an existing structure file as an (n, 3) int array."""
    from nbt import nbt
    blocks = nbt.NBTFile(path)["blocks"]
    return np.array([[int(v.value) for v in block["pos"]] for block in blocks], dtype=np.int64).reshape(-1, 3)
