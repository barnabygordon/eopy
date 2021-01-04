import math
import cv2
import numpy as np
from tqdm import tqdm
from scipy.interpolate import griddata
from scipy.sparse.linalg import svds
from skimage.filters import window
from skimage.restoration import unwrap_phase
from skimage.transform import warp_polar, SimilarityTransform, warp, rotate
from sklearn import linear_model
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt

from eopy.processing import periodic


class PCRegistrator:

    def __init__(self, svd=True, filter_type='periodic', fringe_filter=False, ransac=False, ransac_threshold=0.02, line_filter=1., v=False):

        self._svd = svd
        self._filter_type = filter_type
        self._fringe_filter = fringe_filter
        self._ransac = ransac
        self._line_filter = line_filter
        self._v = v

        self._ransac_regressor = linear_model.RANSACRegressor(residual_threshold=ransac_threshold)

    def estimate_translation(self, image_1, image_2):

        image_1, image_2 = self._apply_filter(image_1, image_2)

        return self._estimate_shift(image_1, image_2)

    def estimate_rotation(self, image_1, image_2):

        image_1, image_2 = self._apply_filter(image_1, image_2)

        h, w = image_1.shape
        cX, cY = w // 2, h // 2

        polar_1 = warp_polar(image_1, radius=min(cX, cY), scaling='log')
        polar_2 = warp_polar(image_2, radius=min(cX, cY), scaling='log')

        _, rotation, __, score_rotation = self._estimate_shift(polar_1, polar_2)

        return rotation, score_rotation

    def _estimate_shift(self, image_1, image_2):

        f1 = np.fft.fftshift(np.fft.fft2(image_1))
        f2 = np.fft.fftshift(np.fft.fft2(image_2))

        q = self._phase_correlation(f1, f2)

        if self._fringe_filter:
            q = self._phase_fringe_filter(q)

        if self._v:
            self._plot_q(q)

        if self._svd:
            left, _, right = svds(q, k=1)
            u_left, u_right = unwrap_phase(np.angle(left[:, 0])), unwrap_phase(np.angle(right[0, :]))
        else:
            uq = unwrap_phase(np.angle(q), seed=1)
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

        if self._v:

            aligned = self.warp_image(image_2, x=x, y=y)

            f, axes = plt.subplots(1, 3, figsize=(10, 5))
            plt.title(f'X: {x} Y:{y}')
            for im, ax, title in zip([aligned, image_1, image_2], axes, ['im 2 aligned', 'im 1', 'im 2']):
                ax.imshow(im, cmap='gray')
                ax.set_title(title)
                ax.axis('off')
                ax.axvline(image_1.shape[0] // 2, c='red')
                ax.axhline(image_1.shape[0] // 2, c='red')
            f.suptitle(f'X: {x:.2f} Y:{y:.2f}')
            plt.show()

        return x, y, score_x, score_y

    def _calculate_shift(self, gradient, length):

        return gradient * length / (2 * math.pi)

    def scan_pairs(self, image_1, image_2, kernel_size=64, resolution=1, pad=False, guide=None) -> np.ndarray:

        half_kernel = kernel_size // 2

        if pad:
            padded_1 = np.pad(image_1, pad_width=kernel_size, mode='constant')
            padded_2 = np.pad(image_2, pad_width=kernel_size, mode='constant')
            if guide is not None:
                guide = np.stack([np.pad(guide[:, :, i], pad_width=kernel_size, mode='constant') for i in range(2)], axis=2)
        else:
            padded_1 = image_1
            padded_2 = image_2

        output = np.zeros((image_1.shape[0] // resolution, image_1.shape[1] // resolution, 4), dtype='float32')

        columns = image_1.shape[1] // resolution
        rows = image_1.shape[0] // resolution

        # with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        #     pool.starmap(self._scan_grid, )

        for ic, column in tqdm(enumerate(np.linspace(0, image_1.shape[1], columns, dtype=np.int)), total=columns):
            for ir, row in enumerate(np.linspace(0, image_1.shape[0], rows, dtype=np.int)):

                if guide is not None:
                    x_guide = int(guide[row+half_kernel, column+half_kernel, 0])
                    y_guide = int(guide[row+half_kernel, column+half_kernel, 1])
                else:
                    x_guide, y_guide = 0, 0

                window_1 = padded_1[row:row + kernel_size, column:column + kernel_size]
                window_2 = padded_2[row + y_guide:row + y_guide + kernel_size, column + x_guide:column + x_guide + kernel_size]

                if float(window_1.sum()) == .0 or float(window_2.sum()) == .0:
                    continue

                x, y, x_error, y_error = self.estimate_translation(window_1, window_2)
                output[ir, ic] = np.dstack([x + x_guide, y + y_guide, x_error, y_error])

        return output

    def _phase_correlation(self, f1, f2):

        g = f1 * f2.conjugate()
        with np.errstate(divide='ignore'):
            q = np.divide(g, abs(g))
            q[np.isnan(q)] = 0.
            return q

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

    def _apply_filter(self, image_1, image_2):

        if self._filter_type == 'window':
            window_filter = self._get_filter(image_1.shape)
            image_1 = image_1 * window_filter
            image_2 = image_2 * window_filter

        if self._filter_type == 'periodic':

            image_1, _ = periodic.rper(image_1, inverse_dft=True)
            image_2, _ = periodic.rper(image_2, inverse_dft=True)

        return image_1, image_2

    @staticmethod
    def _get_magnitude(f):

        fshift = np.fft.fftshift(f)
        return np.log(1+np.abs(fshift))
        # return 20 * np.log(np.abs(fshift))

    @staticmethod
    def warp_image(image, x=0, y=0, scale=1):

        transform = SimilarityTransform(scale=scale, translation=(x, y))

        return warp(image, transform, preserve_range=True)

    @staticmethod
    def rotate_image(image, rotation=0):

        return rotate(image, angle=rotation, preserve_range=True)

    @staticmethod
    def warp_by_optical_flow(image, horizontal, vertical, order=1):

        row_coords, col_coords = np.meshgrid(np.arange(image.shape[0]), np.arange(image.shape[1]), indexing='ij')
        optical_flow = np.array([row_coords + horizontal, col_coords + vertical])

        return image.apply(lambda x: warp(x, optical_flow, order=order, preserve_range=True))

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
    def _plot_q(q):

        plt.title('Q')
        plt.imshow(np.angle(q), interpolation='none')
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
        plt.show()

    def interpolate(self, disparity, error, error_limit, method='linear'):

        disparity[error < error_limit] = np.nan

        indices = np.argwhere(~np.isnan(disparity))
        y, x = indices[:, 0], indices[:, 1]
        yi, xi = np.mgrid[0:disparity.shape[0], 0:disparity.shape[1]]

        return griddata((x, y), disparity[y, x], (xi, yi), method=method)

    def resize(self, disparity: np.ndarray, reference: np.ndarray, factor=20) -> np.ndarray:

        resized = np.zeros((reference.shape[0], reference.shape[1], 2), dtype='float32')
        for i in range(2):
            resized[:, :, i] = cv2.resize(disparity[:, :, i], (reference.shape[1], reference.shape[0]), fx=factor, fy=factor, interpolation=cv2.INTER_AREA)

        return resized

    def test(self, image_1: np.ndarray, image_2: np.ndarray, kernel_size: int, seed: int):

        np.random.seed(seed)
        x, y = np.random.randint(0, image_1.shape[1]), np.random.randint(0, image_1.shape[0])

        window_1 = image_1[y:y + kernel_size, x:x + kernel_size]
        window_2 = image_2[y:y + kernel_size, x:x + kernel_size]

        x, y, _, _ = self.estimate_translation(window_1, window_2)

        aligned = self.warp_image(window_2, x=x, y=y)

        print(f'Shifting x={x} y={y}')
        f, axes = plt.subplots(1, 3)
        for im, ax, title in zip([aligned, window_1, window_2], axes, ['im 2 aligned', 'im 1', 'im 2']):

            ax.imshow(im, cmap='gray')
            ax.set_title(title)
            ax.axis('off')
            ax.axvline(kernel_size // 2, c='red')
            ax.axhline(kernel_size // 2, c='red')
        plt.show()
