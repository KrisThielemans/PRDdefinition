#  Copyright (C) 2024 University College London
#
#  SPDX-License-Identifier: Apache-2.0

# basic plotting of the scanner geometry
# preliminary code!

import sys
import numpy
import numpy.typing as npt
import prd

import matplotlib.pyplot as plt

# from mpl_toolkits.mplot3d import Axes3D
# import mpl_toolkits


def transform_to_mat44(
    transform: prd.RigidTransformation,
) -> npt.NDArray[numpy.float32]:
    return numpy.vstack([transform.matrix, [0, 0, 0, 1]])


def mat44_to_transform(mat: npt.NDArray[numpy.float32]) -> prd.RigidTransformation:
    return prd.RigidTransformation(matrix=mat[0:3, :])


def coordinate_to_homogeneous(coord: prd.Coordinate) -> npt.NDArray[numpy.float32]:
    return numpy.hstack([coord.c, 1])


def homogeneous_to_coordinate(hom_coord: npt.NDArray[numpy.float32]) -> prd.Coordinate:
    return prd.Coordinate(c=hom_coord[0:3])


def mult_transforms(
    transforms: list[prd.RigidTransformation],
) -> prd.RigidTransformation:
    """multiply rigid transformations"""
    mat = numpy.array(
        ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)),
        dtype="float32",
    )

    for t in reversed(transforms):
        mat = numpy.matmul(transform_to_mat44(t), mat)
    return mat44_to_transform(mat)


def mult_transforms_coord(
    transforms: list[prd.RigidTransformation], coord: prd.Coordinate
) -> prd.Coordinate:
    """apply list of transformations to coordinate"""
    # TODO better to multiply with coordinates in sequence, as first multiplying the matrices
    hom = numpy.matmul(
        transform_to_mat44(mult_transforms(transforms)),
        coordinate_to_homogeneous(coord),
    )
    return homogeneous_to_coordinate(hom)


def transform_BoxShape(
    transform: prd.RigidTransformation, box_shape: prd.BoxShape
) -> prd.BoxShape:
    return prd.BoxShape(
        corners=[mult_transforms_coord([transform], c) for c in box_shape.corners]
    )


def draw_BoxShape(ax, box: prd.BoxShape) -> None:
    coords = numpy.array([c.c for c in box.corners])
    # mpl_toolkits.mplot3d.art3d.Line3D(coords[:, 0], coords[:, 1], coords[:, 2])
    ax.plot3D(coords[:, 0], coords[:, 1], coords[:, 2])


if __name__ == "__main__":
    with prd.BinaryPrdExperimentReader(sys.stdin.buffer) as reader:
        header = reader.read_header()
        # TODO somehow say we won't read the time blocks to avoid a ProtocolError

        # Create a new figure
        fig = plt.figure()

        # Add a 3D subplot
        ax = fig.add_subplot(111, projection="3d")

        # draw all crystals
        for rep_module in header.scanner.scanner_geometry.replicated_modules:
            det_el = rep_module.object.detecting_elements
            for mod_transform in rep_module.transforms:
                for rep_volume in det_el:
                    for transform in rep_volume.transforms:
                        draw_BoxShape(
                            ax,
                            transform_BoxShape(
                                mult_transforms([mod_transform, transform]),
                                rep_volume.object.shape,
                            ),
                        )
        plt.show()
