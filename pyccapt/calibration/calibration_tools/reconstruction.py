import numpy as np


def cart2pol(x, y):
    """
    x, y are the detector hit coordinates in mm
    :param x:
    :param y:
    :return rho, phi:
    """
    rho = np.sqrt(x ** 2 + y ** 2)
    phi = np.arctan2(y, x)
    return rho, phi


def pol2cart(rho, phi):
    """
    :param rho:
    :param phi:
    :return x, y:
    """
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y


def atom_probe_recons_from_detector_Gault_et_al(detx, dety, hv, flight_path_length, kf, det_eff, icf, field_evap, avg_dens):
    """
    # atom probe reconstruction after: Gault et al., Ultramicroscopy 111(2011) 448 - 457
    x, y are the detector hit coordinates in mm
    kf is the field factor and ICF is the image compression factor
    :param detx:
    :param dety:
    :param hv:
    :param kf:
    :param icf:
    :param flight_path_length:
    :param ion_volume:
    :param det_eff:
    :param radius_evolution:
    :return:
    """

    ## constants and variable setup
    # specimen parameters
    # avgDens # atomic density in atoms / nm3
    # Fevap  # evaporation field in V / nm

    # detector coordinates in polar form
    rad, ang = cart2pol(detx * 1E-3, dety * 1E-3)
    # calculating effective detector area:
    det_area = (np.max(rad) ** 2) * np.pi
    # f_evap   evaporation field in V / nm
    radius_evolution = hv / (kf * (field_evap / 1E-9))

    # m = (flight_path_length * 1E-3) / (kf * radius_evolution)

    # launch angle relative to specimen axis - a/flight_path_length - a is based on detector hit position
    # theta detector
    theta_p = np.arctan(rad / (flight_path_length * 1E-3))  # mm / mm

    # theta normal
    # m = icf - 1
    theta_a = theta_p + np.arcsin((icf - 1) * np.sin(theta_p))

    icf_2 = theta_a / theta_p

    # distance from axis and z shift of each hit
    z_p, d = pol2cart(radius_evolution, theta_a)  # nm

    # x and y coordinates from the angle on the detector and the distance to
    # the specimen axis.
    x, y = pol2cart(d, ang)  # nm

    ## calculate z coordinate
    # the z shift with respect to the top of the cap is Rspec - zP
    #     z_p = radius_evolution - z_p
    dz_p = radius_evolution * (1 - np.cos(theta_a))
    # accumulative part of z
    omega = 1E-9 ** 3 / avg_dens  # atomic volume in nm ^ 3

    # nm ^ 3 * mm ^ 2 * V ^ 2 / nm ^ 2 / (mm ^ 2 * V ^ 2)
    #     dz = omega * ((flight_path_length * 1E-3) ** 2) * (kf ** 2)  / (det_eff * det_area * (icf ** 2)) * (
    #                 hv ** 2)
    dz = (omega * ((flight_path_length * 1E-3) ** 2) * (kf ** 2) * ((field_evap / 1E-9) ** 2)) / (
                det_area * det_eff * (icf_2 ** 2) * (hv ** 2))
    # wide angle correction
    cum_z = np.cumsum(dz)
    z = cum_z + dz_p

    return x * 1E9, y * 1E9, z * 1E9


def atom_probe_recons_Bas_et_al(detx, dety, hv, flight_path_length, kf, det_eff, icf, field_evap, avg_dens):
    """
    :param detx: Hit position on the detector
    :param dety: Hit position on the detector
    :param hv: High voltage
    :param kf: Field reduction factor
    :param icf: Image compression factor Because sample is not a perfect sphere
    :param flight_path_length: distance between detector and sample
    :param ion_volume: atomic volume in atoms/nm ^ 3
    :param det_eff: Efficiency of the detector
    :return:
    """
    # f_evap   evaporation field in V / nm
    radius_evolution = hv / (icf * (field_evap / 1E-9))

    m = (flight_path_length * 1E-3) / (kf * radius_evolution)

    x = (detx * 1E-3) / m
    y = (dety * 1E-3) / m

    # detector coordinates in polar form
    rad, ang = cart2pol(detx * 1E-3, dety * 1E-3)
    # calculating effective detector area:
    det_area = (np.max(rad) ** 2) * np.pi

    # accumulative part of z
    omega = 1E-9 ** 3 / avg_dens  # atomic volume in nm ^ 3

    #     dz = ((omega * (110 * 1E-3)**2) / (det_area * det_eff * (icf ** 2) * (radius_evolution ** 2))

    dz = (omega * ((flight_path_length * 1E-3) ** 2) * (kf ** 2) * ((field_evap / 1E-9) ** 2)) / (
                det_area * det_eff * (icf ** 2) * (hv ** 2))

    #     dz_p = radius_evolution * (1 - np.sqrt((x**2 + y**2) / (radius_evolution**2)))
    dz_p = radius_evolution * (1 - np.sqrt(1 - ((x ** 2 + y ** 2) / (radius_evolution ** 2))))

    z = np.cumsum(dz) + dz_p

    return x * 1E9, y * 1E9, z * 1E9