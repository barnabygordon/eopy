import numpy as np
import math

from tqdm import tqdm


class Coherence:
    def __init__(self, azimuth_resolution, range_resolution):
        self.azimuth_resolution = azimuth_resolution
        self.range_resolution = range_resolution

    def estimate_coherence(self, master, slave, model_phase):
        # define starting and end point in data for sliding window
        rw_stt = np.int(math.ceil(self.azimuth_resolution / 2.))
        cl_stt = np.int(math.ceil(self.range_resolution / 2.))
        rw_stp = np.int(master.shape[0] - math.floor(self.azimuth_resolution / 2.))
        cl_stp = np.int(master.shape[1] - math.floor(self.range_resolution / 2.))

        # initialize array
        coh_est = np.zeros(master.shape, dtype=np.complex)

        for kk in tqdm(range(rw_stt, rw_stp + 1), total=((rw_stp + 1) - rw_stt)):
            # define extent of window
            from_rw = np.int(kk - math.floor(self.azimuth_resolution / 2.))
            to_rw = np.int(kk + math.floor(self.azimuth_resolution / 2.) + 1)

            for mm in range(cl_stt, cl_stp + 1):
                # define extent of window
                from_cl = np.int(mm - math.floor(self.range_resolution / 2.))
                to_cl = np.int(mm + math.floor(self.range_resolution / 2.) + 1)

                master_subview = master[from_rw:to_rw, from_cl:to_cl]
                slave_subview = slave[from_rw:to_rw, from_cl:to_cl]
                # calculate coherence (estimate)
                numerator = master_subview * np.conj(slave_subview) * np.exp(-complex(0, 1) * model_phase[from_rw:to_rw, from_cl:to_cl])
                denom_p1 = np.abs(master_subview) ** 2
                denom_p2 = np.abs(slave_subview) ** 2
                denominator = np.sqrt(denom_p1.sum() * denom_p2.sum())
                coh_est[kk, mm] = numerator.sum() / denominator

        return coh_est
