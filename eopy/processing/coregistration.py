import math
import cv2
import numpy as np
from tqdm import tqdm
from scipy.sparse.linalg import svds
from skimage.filters import window
from skimage.restoration import unwrap_phase
from skimage.transform import warp_polar, SimilarityTransform, warp, rotate
from sklearn import linear_model
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt


class Coregistration:

    def __init__(self, svd=True, apply_filter=False, fringe_filter=False, ransac=False, ransac_threshold=0.02, line_filter=1., v=False):

        self._svd = svd
        self._apply_filter = apply_filter
        self._fringe_filter = fringe_filter
        self._ransac = ransac
        self._line_filter = line_filter
        self._v = v

        self._ransac_regressor = linear_model.RANSACRegressor(residual_threshold=ransac_threshold)

    def estimate_translation(self, image_1, image_2):

        if self._apply_filter:
            window_filter = self._get_filter(image_1.shape)
            image_1 = window_filter * image_1
            image_2 = window_filter * image_2

        f1 = np.fft.fftshift(np.fft.fft2(image_1))
        f2 = np.fft.fftshift(np.fft.fft2(image_2))

        q = self._phase_correlation(f1, f2)

        x, y, score_x, score_y, q = self._estimate_shift_from_phase_correlation(q, image_1, image_2)

        return x, y, score_x, score_y, q

    def estimate_rotation(self, image_1, image_2):

        (h, w) = image_1.shape
        (cX, cY) = (w // 2, h // 2)

        if self._apply_filter:
            window_filter = self._get_filter(image_1.shape)
            image_1 = window_filter * image_1
            image_2 = window_filter * image_2

        f1 = np.fft.fft2(image_1)
        f2 = np.fft.fft2(image_2)

        warped_1 = warp_polar(self._get_magnitude(f1), radius=min(cX, cY), scaling='log')
        warped_2 = warp_polar(self._get_magnitude(f2), radius=min(cX, cY), scaling='log')

        f1 = np.fft.fft2(warped_1)
        f2 = np.fft.fft2(warped_2)

        q = self._phase_correlation(f1, f2)

        _, rotation, __, score_rotation, q = self._estimate_shift_from_phase_correlation(q, image_1, image_2)

        return rotation, score_rotation, q

    def _estimate_shift_from_phase_correlation(self, q, image_1, image_2):

        if self._fringe_filter:
            q = self._phase_fringe_filter(q)

        if self._v:
            self._plot_inputs(image_1, image_2)
            self._plot_q(q)

        if self._svd:
            left, _, right = svds(q, k=1)
            u_left, u_right = unwrap_phase(np.angle(left[:, 0])), unwrap_phase(np.angle(right[0, :]))
        else:
            uq = unwrap_phase(np.angle(q))
            half_width, half_height = uq.shape[1] // 2, uq.shape[0] // 2
            u_left, u_right = uq[:, half_width], uq[half_height]

            if self._v:
                f, axes = plt.subplots(1, 2)
                for ax, im, title in zip(axes, [np.angle(q), uq], ['Fringe Filtered', 'Unwrapped']):
                    ax.set_title(title)
                    ax.imshow(im)

        mu, cu, score_y = self._get_gradient(u_left)
        mv, cv, score_x = self._get_gradient(u_right)

        if self._v:
            self._plot_svd(u_left, u_right, mu, mv, cu, cv)

        x, y = [self._calculate_shift(m, len(line)) for (m, line) in zip([mv, mu], [u_left, u_right])]

        if self._fringe_filter:
            x, y = -x, -y

        return x, y, score_x, score_y, q

    def _calculate_shift(self, gradient, length):

        return gradient * length / (2 * math.pi)

    def scan_pairs(self, image_1, image_2, kernel_size=64):

        half_kernel = kernel_size // 2

        padded_1 = np.pad(image_1, pad_width=half_kernel, mode='reflect')
        padded_2 = np.pad(image_2, pad_width=half_kernel, mode='reflect')

        x_shift, y_shift = np.zeros(image_1.shape), np.zeros(image_1.shape)
        x_score, y_score = np.zeros(image_1.shape), np.zeros(image_1.shape)

        for x in tqdm(range(image_1.shape[1]), total=image_1.shape[1]):
            for y in range(image_1.shape[0]):

                window_1 = padded_1[y:y + kernel_size, x:x + kernel_size]
                window_2 = padded_2[y:y + kernel_size, x:x + kernel_size]

                x_offset, y_offset, x_error, y_error, _ = self.estimate_translation(window_1, window_2)
                x_shift[y, x] = x_offset
                y_shift[y, x] = y_offset
                x_score[y, x] = x_error
                y_score[y, x] = y_error

        return x_shift, y_shift, x_score, y_score

    def _phase_correlation(self, f1, f2):

        g = f1 * f2.conjugate()
        return g / abs(g)

    def _get_gradient(self, line):

        start, end = self._estimate_line_clip(line)

        if self._ransac:
            return self._ransac_fit(line[start:end])
        return self._least_squares_fit(line[start:end])

    def _estimate_line_clip(self, line):

        window_width = len(line) * self._line_filter
        half_width = window_width // 2
        centre = len(line) // 2
        return int(centre - half_width), int(centre + half_width)

    def _least_squares_fit(self, line):

        x = np.arange(0, len(line))
        a = np.vstack([x, np.ones(len(line))]).T

        fit = np.linalg.lstsq(a, line, rcond=None)
        m, c = fit[0]
        residues = fit[1]

        r2 = 1 - residues / sum((line - line.mean())**2)

        return m, c, r2

    def _ransac_fit(self, line):

        x = np.arange(0, len(line)).reshape(-1, 1)
        y = line.reshape(-1, 1)

        self._ransac_regressor.fit(x, y)
        m, c = float(self._ransac_regressor.estimator_.coef_), float(self._ransac_regressor.estimator_.intercept_)
        inlier_mask = self._ransac_regressor.inlier_mask_
        x_accpt, y_accpt = x[inlier_mask], y[inlier_mask]
        y_predict = m * x_accpt + c
        r2 = r2_score(y_accpt, y_predict)

        return m, c, r2

    def _reconstruct_vectors(self, u, s, v):

        num_components = 2
        reconst_img = np.matrix(u[:, :num_components]) * np.diag(s[:num_components]) * np.matrix(v[:num_components, :])

        return unwrap_phase(np.angle(reconst_img))

    @staticmethod
    def _get_magnitude(f):

        fshift = np.fft.fftshift(f)
        return 20 * np.log(np.abs(fshift))

    @staticmethod
    def warp_image(image, x=0, y=0, scale=1):

        transform = SimilarityTransform(scale=scale, translation=(x, y))

        return warp(image, transform)

    @staticmethod
    def rotate_image(image, rotation=0):

        return rotate(image, angle=rotation, preserve_range=True)

    @staticmethod
    def warp_by_optical_flow(image, horizontal, vertical):

        row_coords, col_coords = np.meshgrid(np.arange(image.shape[0]), np.arange(image.shape[1]), indexing='ij')
        optical_flow = np.array([row_coords + horizontal, col_coords + vertical])

        return image.apply(lambda x: warp(x, optical_flow))

    @staticmethod
    def _phase_fringe_filter(q, filter_size=3):

        cos_q, sin_q = q.real, q.imag

        kernel = np.ones((filter_size, filter_size), np.float64) / filter_size**2

        cos_q_filtered = cv2.filter2D(cos_q, -1, kernel)
        sin_q_filtered = cv2.filter2D(sin_q, -1, kernel)

        return sin_q_filtered + (cos_q_filtered * 1j)

    @staticmethod
    def _get_filter(shape):

        # columns = np.hamming(shape[0])[:, None]
        # rows = np.hamming(shape[1])[None, :]
        #
        # return np.sqrt(np.dot(columns, rows)) ** filter_size

        return window('hanning', shape)

    @staticmethod
    def _plot_inputs(image_1, image_2):
        f, axes = plt.subplots(1, 2)
        for ax, im in zip(axes, [image_1, image_2]):
            ax.imshow(im, cmap='gray')
            ax.axvline(image_1.shape[1] // 2, c='red')
            ax.axhline(image_1.shape[0] // 2, c='red')
        plt.show()

    @staticmethod
    def _plot_q(q):

        plt.title('Q')
        plt.imshow(np.angle(q), interpolation='none', cmap='hsv')
        plt.show()

    def _plot_svd(self, left, right, mu, mv, cu, cv, titles=['Y', 'X']):

        f, axes = plt.subplots(1, 2)
        for line, ax, m, c, title in zip([left, right], axes, [mu, mv], [cu, cv], titles):

            start, end = self._estimate_line_clip(line)

            ax.set_title(title)
            ax.plot(line)
            ax.axvline(start, c='green')
            ax.axvline(end, c='green')
            x = np.arange(0, len(line))
            ax.plot(x, x * m + c, c='red')
