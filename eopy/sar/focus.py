import numpy as np
import math


class Focus:
    def __init__(self, multilook: bool = True, multilook_factor: int = 5):

        self.multilook = multilook
        self.multilook_factor = multilook_factor

        self.range_sampling_frequency = 18.962468 * 10 ** 6
        self.chirp_rate = 4.18989015 * 10 ** 11
        self.chirp_length = 37.12 * 10 ** (-6)
        self.velocity = 7098.0194
        self.wavelength = 0.05656
        self.range_to_target = 852358.15
        self.aperture_time = 0.6
        self.pulse_repetition_frequency = 1679.902

    def focus(self, image):
        size_azimuth = image.shape[0]
        size_range = image.shape[1]

        con_range_chirp = self.calculate_chirp_range(size_range)
        con_azimuth_chirp = self.calculate_chirp_azimuth(size_azimuth)

        processed = np.zeros((size_azimuth, size_range), 'complex')

        for k1 in range(0, size_azimuth, 1):
            vek = image[k1, :]  # Select row in range
            vek = np.fft.fft(vek)  # Fourier Transform
            corr = vek * con_range_chirp  # Multiply vectors
            if_vek = np.fft.ifft(corr)  # Inverse Fourier Transform
            if_vek_sort = np.fft.ifftshift(if_vek)  # Sorting after FFT
            processed[k1, :] = if_vek_sort  # Store row in matrix

        # F.2) Azimuth compression
        # conducted in azimuth frequency - range time domain

        for k2 in range(0, size_range, 1):
            vek = processed[:, k2]  # Select row in azimuth
            vek = np.fft.fft(vek)
            corr = vek * con_azimuth_chirp
            if_vek = np.fft.ifft(corr)
            if_vek_sort = np.fft.ifftshift(if_vek)
            processed[:, k2] = if_vek_sort

        if self.multilook is True:
            processed = self.spatial_multilook(processed, size_azimuth, size_range)

        return processed

    def calculate_chirp_range(self, size_range):
        range_chirp = np.zeros((1, size_range), 'complex')  # empty vector to be filled with chirp values
        tau = np.arange(-self.chirp_length / 2, self.chirp_length / 2, 1 / self.range_sampling_frequency)

        # Define chirp in range
        phase = 1j * math.pi * self.chirp_rate * tau ** 2
        ra_chirp_temp = np.exp(phase)

        # Get size of chirp
        size_chirp_r = len(tau)

        index_start = math.ceil((size_range - size_chirp_r) / 2) - 1
        index_end = size_chirp_r + math.ceil((size_range - size_chirp_r) / 2) - 2
        range_chirp[0, index_start:index_end + 1] = ra_chirp_temp

        range_chirp = np.fft.fft(range_chirp)

        return np.conjugate(range_chirp)

    def calculate_chirp_azimuth(self, size_azimuth):
        azimuth_chirp = np.zeros((1, size_azimuth), 'complex')  # empty vector to be filled with chirp values
        t = np.arange(-self.aperture_time / 2, self.aperture_time / 2, 1 / self.pulse_repetition_frequency)

        K_a = (-2 * self.velocity ** 2) / (self.wavelength * self.range_to_target)

        phase2 = 1j * math.pi * K_a * t ** 2
        az_chirp_temp = np.exp(phase2)

        size_chirp_a = len(t)

        index_start = math.ceil((size_azimuth - size_chirp_a) / 2) - 1
        index_end = size_chirp_a + math.ceil((size_azimuth - size_chirp_a) / 2) - 2
        azimuth_chirp[0, index_start:index_end + 1] = az_chirp_temp

        azimuth_chirp = np.fft.fft(azimuth_chirp)

        return np.conjugate(azimuth_chirp)

    def spatial_multilook(self, image, size_azimuth, size_range):
        output_image = np.zeros((math.ceil(size_azimuth / self.multilook_factor), size_range), 'complex')

        for i, value in enumerate(range(0, size_azimuth - self.multilook_factor, self.multilook_factor)):
            vek = image[value:value + (self.multilook_factor - 1), ]  # select azimuth bins
            m_vek = np.mean(vek, axis=0)  # average value of azimuth bins
            output_image[i, :] = m_vek

        return output_image
