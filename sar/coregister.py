import numpy as np
import math
import scipy.signal as spsig


class Coregister:
    def __init__(self,
                 pos_mx: int, pox_sx: int,
                 pos_my: int, pox_sy: int,
                 ex_slave: int, ex_master: int,
                 oversampling_factor: int):
        self.pos_mx = pos_mx
        self.pos_sx = pox_sx
        self.pos_my = pos_my
        self.pos_sy = pox_sy
        self.ex_slave = ex_slave
        self.ex_master = ex_master
        self.oversampling_factor = oversampling_factor

    def coregister(self, master, slave):
        master_amp = self.convert_to_amplitude(master)
        slave_amp = self.convert_to_amplitude(slave)

        coarse_shift_x = self.pos_sx - self.pos_mx
        coarse_shift_y = self.pos_sy - self.pos_my

        master_area = master_amp[
                      self.pos_my - self.ex_master // 2: self.pos_my + self.ex_master // 2,
                      self.pos_mx - self.ex_master // 2: self.pos_mx + self.ex_master // 2]
        slave_area = slave_amp[
                     self.pos_sy - self.ex_slave // 2: self.pos_sy + self.ex_slave // 2,
                     self.pos_sx - self.ex_slave // 2: self.pos_sx + self.ex_slave // 2]

        master_area_spec = np.fft.fft2(master_area)
        slave_area_spec = np.fft.fft2(slave_area)

        master_area_spec_zp = self.zeropad2d(master_area_spec, self.oversampling_factor)
        slave_area_spec_zp = self.zeropad2d(slave_area_spec, self.oversampling_factor)

        master_area_oversampled = np.fft.ifft2(master_area_spec_zp)
        slave_area_oversampled = np.fft.ifft2(slave_area_spec_zp)

        master_area_oversampled = np.abs(master_area_oversampled)
        slave_area_oversampled = np.abs(slave_area_oversampled)

        xcorr = spsig.correlate2d(master_area_oversampled, slave_area_oversampled, mode='same')

        maxcorr = xcorr.max()
        pos_max = np.transpose(np.nonzero(np.abs(xcorr - maxcorr < 1e-10)))
        rows, columns = xcorr.shape

        shift = np.array(
            [(pos_max[0, 0] - rows / 2.) / float(self.oversampling_factor),
             (pos_max[0, 1] - columns / 2.) / float(self.oversampling_factor)])
        final_shift = shift + [coarse_shift_y, coarse_shift_x]

        tra_x = final_shift[1]
        tra_y = final_shift[0]

        slave_fine = slave[2:, :]
        master_fine = master[: -2, :]

        return slave_fine, master_fine

    @staticmethod
    def convert_to_amplitude(image):
        return 10 * np.log10(np.absolute(image) ** 2)

    @staticmethod
    def zeropad2d(data, factor):
        rw, cl = data.shape

        # 1st insertion: mid of rows
        data_slice_1 = data[0:math.ceil(rw / 2), :]
        data_slice_2 = data[math.floor(rw / 2):, :]
        zeros_mid = np.zeros(((factor - 1) * rw, cl))
        # insert zeros at center
        data_zp = np.vstack([data_slice_1, zeros_mid, data_slice_2])

        # 2nd insertion: mid of columns
        rw2, cl2 = data_zp.shape
        data_slice_1 = data_zp[:, :math.ceil(cl2 / 2)]
        data_slice_2 = data_zp[:, math.floor(cl / 2):]
        zeros_mid = np.zeros((rw2, (factor - 1) * cl2))
        # insert zeros at center
        data_zp = np.hstack([data_slice_1, zeros_mid, data_slice_2])

        return data_zp
