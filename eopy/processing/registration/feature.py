import numpy as np
from skimage.feature import ORB, match_descriptors
from skimage.measure import ransac
from skimage.transform import ProjectiveTransform


class FeatureRegistrator:

    def estimate_homography(self, image_1: np.ndarray, image_2: np.ndarray):

        keypoints_1, keypoints_2, descriptors_1, descriptors_2 = self.get_features(image_1, image_2)

        matches = self.get_matches(descriptors_1, descriptors_2)

    def get_features(self, image_1, image_2):

        orb = ORB(n_keypoints=1000, fast_threshold=0.05)

        orb.detect_and_extract(image_1)
        keypoints_1 = orb.keypoints
        descriptors_1 = orb.descriptors

        orb.detect_and_extract(image_2)
        keypoints_2 = orb.keypoints
        descriptors_2 = orb.descriptors

        return keypoints_1, keypoints_2, descriptors_1, descriptors_2

    def get_matches(self, descriptors_1, descriptors_2):

        return match_descriptors(descriptors_1, descriptors_2, cross_check=True)

    def filter_matches(self, keypoints_1, keypoints_2, matches):

        src = keypoints_2[matches[:, 1]][:, ::-1]
        dst = keypoints_1[matches[:, 0]][:, ::-1]

        model_robust, inliers = ransac((src, dst), ProjectiveTransform, min_samples=4, residual_threshold=2)

        return model_robust
