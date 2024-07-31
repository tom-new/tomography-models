import numpy
from numpy.typing import ArrayLike, NDArray

def cart2sph(cartesian_coord_array: NDArray, degrees: bool=False) -> NDArray:
    ''' Take shape (N,3) or (3,) cartesian coord_array and return an array of the same shape in spherical polar form (r,theta,phi). Based on StackOverflow response: http://stackoverflow.com/a/4116899.

    Use radians for angles by default, degrees if ``degrees == True``.'''

    # cast input sequence to numpy.ndarray with dtype numpy.float64
    cartesian_coord_array = numpy.array(cartesian_coord_array, dtype='float64')

    # create new array to hold spherical coordinates
    spherical_coord_array = numpy.empty(cartesian_coord_array.shape)

    # convert to spherical coordinates
    spherical_coord_array[...,0] = numpy.linalg.norm(cartesian_coord_array, axis=-1)
    spherical_coord_array[...,1] = numpy.arctan2(cartesian_coord_array[...,1], cartesian_coord_array[...,0])
    spherical_coord_array[...,2] = numpy.arccos(cartesian_coord_array[...,2] / spherical_coord_array[...,0])

    # convert from radians to degrees if required, otherwise skip
    if degrees:
        spherical_coord_array[...,1:] = numpy.rad2deg(spherical_coord_array[...,1:])

    return spherical_coord_array


def sph2cart(spherical_coord_array: NDArray, degrees=False) -> NDArray:
    '''Take shape (N,3) or (3,) spherical_coord_array (radius, azimuth, pole) and return an array of the same shape in cartesian coordinate form (x, y, z). Based on the equations provided at: http://en.wikipedia.org/wiki/List_of_common_coordinate_transformations#From_spherical_coordinates.

    Use radians for angles by default, degrees if ``degrees == True``.'''

    # cast input sequence to numpy.ndarray with dtype numpy.float64
    spherical_coord_array = numpy.array(spherical_coord_array, dtype='float64')

    # create new array to hold Cartesian coordinates
    cartesian_coord_array = numpy.empty(spherical_coord_array.shape)

    # convert from degrees to radians if required, otherwise skip
    if degrees:
        spherical_coord_array[...,1:] = numpy.deg2rad(spherical_coord_array[...,1:])

    # now the conversion to Cartesian coords
    cartesian_coord_array[...,0] = spherical_coord_array[...,0] * numpy.cos(spherical_coord_array[...,1]) * numpy.sin(spherical_coord_array[...,2])
    cartesian_coord_array[...,1] = spherical_coord_array[...,0] * numpy.sin(spherical_coord_array[...,1]) * numpy.sin(spherical_coord_array[...,2])
    cartesian_coord_array[...,2] = spherical_coord_array[...,0] * numpy.cos(spherical_coord_array[...,2])

    return cartesian_coord_array


def geo2sph(geographical_coord_array: NDArray, degrees=False) -> NDArray:
    '''Take shape (N,2), (N,3), (2,), or (3,) geographical_coord_array ([radius], lon, lat) and return an array of the same shape in spherical coordinate form ([radius], azimuth, pole).'''

    # cast to numpy.ndarray with type ``numpy.float64`` since this function is likely to be passed integer degrees of lon or lat
    geographical_coord_array = numpy.array(geographical_coord_array, dtype='float64')

    # create new array to hold spherical coordinates
    spherical_coord_array = geographical_coord_array.copy()

    # reverse orientation of polar angle
    spherical_coord_array[...,-1] = 90 - spherical_coord_array[...,-1]
    # assume that outgoing spherical coordinates should be in radians, so convert from degrees by default
    if not degrees:
        spherical_coord_array[...,-2:] = numpy.deg2rad(spherical_coord_array[...,-2:])

    return spherical_coord_array


def sph2geo(spherical_coord_array: NDArray, degrees=False) -> NDArray:
    '''Take shape (N,2), (N,3), (2,), or (3,) spherical_coord_array ([radius], azimuth, pole) and return an array of the same shape in geographical coordinate form ([radius], lon, lat).'''

    # cast to numpy.ndarray with type ``numpy.float64`` just in case some loon decides to pass an integer amount of radians
    spherical_coord_array = numpy.array(spherical_coord_array, dtype='float64')

    # create a new array to hold the geographical coordinates
    geographical_coord_array = spherical_coord_array.copy()

    # incoming spherical coordinates are assumed to be in radians, so convert to degrees by default
    if not degrees:
        geographical_coord_array[...,-2:] = numpy.rad2deg(geographical_coord_array[...,-2:])
    # reverse orientation of polar angle
    geographical_coord_array[...,-1] = 90 - geographical_coord_array[...,-1]

    return geographical_coord_array


def cart2polar(cartesian_coord_array: NDArray, degrees=False) -> NDArray:
    '''Take shape (N,2) cartesian_coord_array and return an array of the same shape in polar coordinates (radius, azimuth).

    Use radians for angles by default, degrees if ``degrees == True``.'''

    # cast input sequence to numpy.ndarray with dtype numpy.float64
    cartesian_coord_array = numpy.array(cartesian_coord_array, dtype='float64')

    # create new array to hold spherical coordinates
    polar_coord_array = numpy.empty(cartesian_coord_array.shape)

    # convert to spherical coordinates
    polar_coord_array[...,0] = numpy.linalg.norm(cartesian_coord_array, axis=-1)
    polar_coord_array[...,1] = numpy.arctan2(cartesian_coord_array[...,1], cartesian_coord_array[...,0])

    # convert from radians to degrees if required, otherwise skip
    if degrees:
        polar_coord_array[...,1] = numpy.rad2deg(polar_coord_array[...,1])

    return polar_coord_array


def great_circle_distance(array_1: NDArray, array_2: NDArray, coordinate_system: str='spherical', sphere_radius: bool | float=False) -> float:
    '''Calculate the haversine-based distance between two arrays of points on the surface of a sphere (array shape must be (N,3) or (3,)). Should be more accurate than the arc cosine strategy. See, for example: http://en.wikipedia.org/wiki/Haversine_formula.
    
    This function assumes that all your coordinate pairs have the same radius. If they don't, why!? It doesn't make sense to calculate the great circle distance between coordinates that don't lie on the same spherical shell. If you're a complete psychopath though, you can override the radius (or radii) with custom values---either a single value to use for everything or an array-like of values of length N.'''
    
    assert coordinate_system in ['spherical', 'cartesian']
    array_1, array_2 = numpy.array(array_1), numpy.array(array_2)
    if coordinate_system == 'cartesian':
        array_1 = cart2sph(array_1)
        array_2 = cart2sph(array_2)
    if not sphere_radius:
        sphere_radius = array_1[...,0] # get the radius (or radii) if the user has not overridden the radius
    phi_1 = array_1[...,1]
    phi_2 = array_2[...,1]
    theta_1 = array_1[...,2]
    theta_2 = array_2[...,2]

    spherical_distance = 2.0 * sphere_radius * numpy.arcsin(numpy.sqrt( ((1 - numpy.cos(theta_2-theta_1))/2.) + numpy.sin(theta_1) * numpy.sin(theta_2) * ( (1 - numpy.cos(phi_2-phi_1))/2.)  ))

    return spherical_distance