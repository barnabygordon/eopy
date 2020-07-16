import math
import cv2
import numpy as np
from tqdm import tqdm
from scipy.sparse.linalg import svds
from skimage.filters import window
from skimage.restoration import unwrap_phase
from skimage.transform import warp_polar, SimilarityTransform, warp
from sklearn import linear_model
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt


class Coregistration:

    def estimate_translation(self, image_1, image_2, apply_filter=False, svd=True, fringe_filter=False, ransac=False, v=False):

        if apply_filter:
            window_filter = self.get_filter(image_1.shape)
            image_1 = window_filter * image_1
            image_2 = window_filter * image_2

        F1 = np.fft.fftshift(np.fft.fft2(image_1))
        F2 = np.fft.fftshift(np.fft.fft2(image_2))

        Q = self.phase_correlation(F1, F2)

        if v:
            f, axes = plt.subplots(1, 2)
            for ax, im in zip(axes, [image_1, image_2]):
                ax.imshow(im, cmap='gray')
                ax.axvline(image_1.shape[1] // 2, c='red')
                ax.axhline(image_1.shape[0] // 2, c='red')
            plt.show()

            plt.title('Q')
            plt.imshow(np.angle(Q))
            plt.show()

        if fringe_filter:
            Q = self.phase_fringe_filter(Q, filter_size=3)

        if svd:
            U, _, V = svds(Q, k=1)
            uU, uV = unwrap_phase(np.angle(U[:, 0])), unwrap_phase(np.angle(V[0, :]))

        else:
            uQ = unwrap_phase(np.angle(Q))
            half_width, half_height = uQ.shape[1] // 2, uQ.shape[0] // 2
            uU, uV = uQ[:, half_width], uQ[half_height]

            if v:
                f, axes = plt.subplots(1, 2)
                for ax, im, title in zip(axes, [np.angle(Q), uQ], ['Fringe Filtered', 'Unwrapped']):
                    ax.set_title(title)
                    ax.imshow(im)

        mU, cU, scoreY = self.get_gradient(uU, ransac=ransac)
        mV, cV, scoreX = self.get_gradient(uV, ransac=ransac)

        if v:
            f, axes = plt.subplots(1, 2)
            for line, ax, m, c, title in zip([uU, uV], axes, [mU, mV], [cU, cV], ['Y', 'X']):
                ax.set_title(title)
                ax.plot(line)
                x = np.arange(0, len(line))
                ax.plot(x, x * m + c, c='red')

        x, y = [self.calculate_shift(m, len(line)) for (m, line) in zip([mV, mU], [uV, uU])]

        return x, y, scoreX, scoreY, Q

    def calculate_shift(self, gradient, length):

        return gradient * length / (2 * math.pi)

    def estimate_rotation(self, image_1, image_2, apply_filter=False, ransac=False, v=False):

        (h, w) = image_1.shape
        (cX, cY) = (w // 2, h // 2)

        if apply_filter:
            window_filter = self.get_filter(image_1.shape)
            image_1 = window_filter * image_1
            image_2 = window_filter * image_2

        F1 = np.fft.fft2(image_1)
        F2 = np.fft.fft2(image_2)

        warped_1 = warp_polar(self.get_magnitude(F1), radius=min(cX, cY), scaling='log')
        warped_2 = warp_polar(self.get_magnitude(F2), radius=min(cX, cY), scaling='log')

        F1 = np.fft.fft2(warped_1)
        F2 = np.fft.fft2(warped_2)

        Q = self.phase_correlation(F1, F2)

        if v:
            f, axes = plt.subplots(1, 2)
            for ax, im in zip(axes, [image_1, image_2]):
                ax.imshow(im, cmap='gray')
                ax.axvline(image_1.shape[1] // 2, c='red')
                ax.axhline(image_1.shape[0] // 2, c='red')
            plt.show()

            plt.title('Q')
            plt.imshow(np.angle(Q))
            plt.show()

        U, _, __ = svds(Q, k=1)
        uU = unwrap_phase(np.angle(U))

        m, c, score = self.get_gradient(uU, ransac)

        if v:
            plt.plot(uU)
            x = np.arange(0, len(uU))
            plt.plot(x, x * m + c, c='red')
            plt.show()

        return (m * len(uU)) / (2 * math.pi), score

    def scan_pairs(self, image_1, image_2, kernel_size=64, apply_filter=True, svd=False, fringe_filter=True, ransac=False):

        half_kernel = kernel_size // 2

        padded_1 = np.pad(image_1, pad_width=half_kernel, mode='reflect')
        padded_2 = np.pad(image_2, pad_width=half_kernel, mode='reflect')

        x_shift, y_shift = np.zeros(image_1.shape), np.zeros(image_1.shape)
        x_score, y_score = np.zeros(image_1.shape), np.zeros(image_1.shape)

        for x in tqdm(range(image_1.shape[1]), total=image_1.shape[1]):
            for y in range(image_1.shape[0]):

                window_1 = padded_1[y:y + kernel_size, x:x + kernel_size]
                window_2 = padded_2[y:y + kernel_size, x:x + kernel_size]

                x_offset, y_offset, x_error, y_error, _ = Coregistration().estimate_translation(window_1, window_2,
                                                                                                apply_filter=apply_filter,
                                                                                                svd=svd,
                                                                                                fringe_filter=fringe_filter,
                                                                                                ransac=ransac
                                                                                                )
                x_shift[y, x] = x_offset
                y_shift[y, x] = y_offset
                x_score[y, x] = x_error
                y_score[y, x] = y_error

        return x_shift, y_shift, x_score, y_score

    def phase_correlation(self, F1, F2):

        G = F1 * F2.conjugate()
        return G / abs(G)

    def get_gradient(self, line, ransac=False):

        if len(line) < 100:
            if ransac:
                return self.ransac_fit(line[20:50])
            return self.least_squares_fit(line[20:50])

        if ransac:
            return self.ransac_fit(line)
        return self.least_squares_fit(line)

    def least_squares_fit(self, line):

        x = np.arange(0, len(line))
        A = np.vstack([x, np.ones(len(line))]).T

        fit = np.linalg.lstsq(A, line, rcond=None)
        m, c = fit[0]
        residues = fit[1]

        R2 = 1 - residues / sum((line - line.mean())**2)

        return m, c, R2

    def ransac_fit(self, line):

        x = np.arange(0, len(line)).reshape(-1, 1)
        y = line.reshape(-1, 1)

        ransac = linear_model.RANSACRegressor(residual_threshold=0.02)
        ransac.fit(x, y)

        m, c = float(ransac.estimator_.coef_), float(ransac.estimator_.intercept_)

        inlier_mask = ransac.inlier_mask_
        x_accpt, y_accpt = x[inlier_mask], y[inlier_mask]
        y_predict = m * x_accpt + c
        R2 = r2_score(y_accpt, y_predict)

        return m, c, R2

    def reconstruct_vectors(self, U, s, V):

        num_components = 2
        reconst_img = np.matrix(U[:, :num_components]) * np.diag(s[:num_components]) * np.matrix(V[:num_components, :])

        return unwrap_phase(np.angle(reconst_img))

    def get_magnitude(self, F):
        fshift = np.fft.fftshift(F)
        return 20 * np.log(np.abs(fshift))

    def warp(self, image, x=0, y=0, rotation=0, scale=1):

        transform = SimilarityTransform(scale=scale, rotation=rotation, translation=(x, y))

        return warp(image, transform)

    def warp_by_optical_flow(self, image, horizontal, vertical):

        row_coords, col_coords = np.meshgrid(np.arange(image.shape[0]), np.arange(image.shape[1]), indexing='ij')
        optical_flow = np.array([row_coords + horizontal, col_coords + vertical])

        return image.apply(lambda x: warp(x, optical_flow))

    def phase_fringe_filter(self, Q, filter_size=3):

        cos_Q, sin_Q = Q.real, Q.imag

        kernel = np.ones((filter_size, filter_size), np.float64) / filter_size**2

        cos_Q_filtered = cv2.filter2D(cos_Q, -1, kernel)
        sin_Q_filtered = cv2.filter2D(sin_Q, -1, kernel)

        return sin_Q_filtered + (cos_Q_filtered * 1j)

    def get_filter(self, shape):

        return window('blackman', shape)

    def get_hamming(self, shape, r=20):
        rows = np.hamming(shape[0])[:, None]
        columns = np.hamming(shape[1])[:, None]

        return np.sqrt(np.dot(rows, columns.T)) ** r
