import numpy as np

from remotesensing.sar import tools

# phase to height factor
p2h = 167.89/2/np.pi  # [m/cycle]


class Unwrapper:
    def unwrap(self, part):
        ######################################
        ### 2D unwrapping for small area  ####
        ######################################

        phase_2d = np.angle(part)
        rw_all, cl_all = np.shape(part)

        # phase unwrapping line wise
        # 1. do phase unwrapping for first column to get initial values for each line
        phase_1d = phase_2d[:, 0]
        uw_phase_1d_dict = self.phase_unwrap_1d(0, phase_1d)

        cycles_1st_cl = uw_phase_1d_dict['uw_cycles']

        # 2. apply PhU for each line in interferogram, using initial values for each line
        final_phase_2d_rw = np.zeros((rw_all, cl_all))
        for k in range(0, rw_all):
            phase_1d = phase_2d[k, :]
            tmp_dict = self.phase_unwrap_1d(cycles_1st_cl[k], phase_1d)
            final_phase_2d_rw[k, :] = tmp_dict['uw_phase']

        # phase unwrapping column wise
        # 1. do phase unwrapping for first column to get initial values for each line
        phase_1d = phase_2d[0, :]
        uw_phase_1d_dict = self.phase_unwrap_1d(0, phase_1d)

        cycles_1st_rw = uw_phase_1d_dict['uw_cycles']

        # 2. apply PhU for each line in interferogram, using initial values for each line
        final_phase_2d_cl = np.zeros((rw_all, cl_all))
        for k in range(0, cl_all):
            phase_1d = phase_2d[:, k]
            tmp_dict = self.phase_unwrap_1d(cycles_1st_rw[k], phase_1d)
            final_phase_2d_cl[:, k] = tmp_dict['uw_phase']

        # calculate residues

        residues_dict = self.residues(phase_2d)
        return residues_dict['residual_cycles'], final_phase_2d_rw * p2h

    @staticmethod
    def phase_unwrap_1d(initial_cycles, phase_1d):
        dim = phase_1d.ndim

        # check that input is a 1D vector
        if dim > 1:
            raise UserWarning('input must be one vector - no matrices allowed')
        else:
            # calculate the gradients, i.e., phase differences of neighbors
            phase_diff = phase_1d[1:] - phase_1d[0:-1]

            # detect phase jumps (including sign)
            ph_up = np.where(phase_diff > np.pi, -1, 0)
            ph_down = np.where(phase_diff < -np.pi, 1, 0)

            # generate cumulative sum for cycles to be added to whole vector
            cycles_add = np.cumsum(ph_up + ph_down)

            # add zero value for first element
            cycles = np.hstack([0, cycles_add]) + initial_cycles

            # unwrap the phase by adding multiples of 2pi
            uw_phase = phase_1d + cycles * 2 * np.pi

            # return a dictionary with the results
            return {'uw_phase': uw_phase, 'uw_cycles': cycles}

    @staticmethod
    def residues(ifgrm):
        rw, cl = ifgrm.shape

        res_phase = np.zeros((rw, cl), dtype=np.double)

        # code for calculating whole lines at once
        for k in range(0, rw - 1):
            d_ur_ul = tools.wrap(ifgrm[k, 1:] - ifgrm[k, 0:-1])  # diff: (0,1) - (0,0)
            d_lr_ur = tools.wrap(ifgrm[k + 1, 1:] - ifgrm[k, 1:])  # diff: (1,1) - (0,1)
            d_ll_lr = tools.wrap(ifgrm[k + 1, 0:-1] - ifgrm[k + 1, 1:])  # diff: (1,0) - (1,1)
            d_ul_ll = tools.wrap(ifgrm[k, 0:-1] - ifgrm[k + 1, 0:-1])  # diff: (0,0) - (1,0)
            # residual phase: sum up
            res_phase[k, 0:-1] = d_ur_ul + d_lr_ur + d_ll_lr + d_ul_ll

        # residual cycles
        res_cycles = np.round(res_phase / (2 * np.pi))

        return {'residual_phase': res_phase, 'residual_cycles': res_cycles}
