# -*- coding: UTF-8 -*-

import cv2
import matplotlib.pyplot as plt
import numpy as np


class PROIE():

    def __init__(self):
        #####
        pass

    # PRIVATE METHODS

    def _threshold(self):
        #####
        self.blur_img = cv2.GaussianBlur(self.in_img_g, (5, 5), 0)
        _, self.thresh_img = cv2.threshold(
            self.blur_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    def _contours(self):
        #####
        self.contours, _ = cv2.findContours(
            self.thresh_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        self.contours = self.contours[0]
        self.contour_img = self.in_img_c.copy()
        self.contour_img = cv2.drawContours(
            self.contour_img, [self.contours], 0, (255, 0, 0), 2)

    def _landmarks(self):
        #####
        M = cv2.moments(self.thresh_img)
        x_c = M['m10'] // M['m00']
        y_c = M['m01'] // M['m00']
        self.center_point = {"x": x_c, "y": y_c}
        self.contours = self.contours.reshape(-1, 2)
        left_id = np.argmin(self.contours.sum(-1))
        self.contours = np.concatenate(
            [self.contours[left_id:, :], self.contours[:left_id, :]])
        dist_c = np.sqrt(np.square(
            self.contours-[self.center_point["x"], self.center_point["y"]]).sum(-1))
        f = np.fft.rfft(dist_c)
        cutoff = 15
        f_new = np.concatenate([f[:cutoff], 0*f[cutoff:]])
        dist_c_1 = np.fft.irfft(f_new)
        derivative = np.diff(dist_c_1)
        sign_change = np.diff(np.sign(derivative))/2
        self.landmarks = {"x": [], "y": []}
        for landmark in self.contours[np.where(sign_change > 0)[0]]:
            self.landmarks["x"].append(landmark[0])
            self.landmarks["y"].append(landmark[1])

    def _landmarks_select(self):
        #####
        y_rank = np.array(np.argsort(self.landmarks["y"]))
        self.landmarks_selected = {"x": np.array(self.landmarks["x"])[
            y_rank][:3], "y": np.array(self.landmarks["y"])[y_rank][:3]}

        x_rank = np.array(np.argsort(self.landmarks_selected["x"]))
        self.landmarks_selected = {
            "x": self.landmarks_selected["x"][x_rank][[0, 2]], "y": self.landmarks_selected["y"][x_rank][[0, 2]]}

    def _alignement(self):
        #####
        h, w = self.in_img_g.shape
        theta = np.arctan2((self.landmarks_selected["y"][1] - self.landmarks_selected["y"][0]), (
            self.landmarks_selected["x"][1] - self.landmarks_selected["x"][0]))*180/np.pi
        R = cv2.getRotationMatrix2D(
            (self.landmarks_selected["x"][1], self.landmarks_selected["y"][1]), theta, 1)
        self.align_img = cv2.warpAffine(self.in_img_g, R, (w, h))

        point_1 = [self.landmarks_selected["x"]
                   [0], self.landmarks_selected["y"][0]]
        point_2 = [self.landmarks_selected["x"]
                   [1], self.landmarks_selected["y"][1]]

        point_1 = (R[:, :2] @ point_1 + R[:, -1]).astype(np.int)
        point_2 = (R[:, :2] @ point_2 + R[:, -1]).astype(np.int)

        self.landmarks_selected_align = {
            "x": [point_1[0], point_2[0]], "y": [point_1[1], point_2[1]]}

    def _roi_extract(self):
        #####
        point_1 = np.array([self.landmarks_selected_align["x"]
                            [0], self.landmarks_selected_align["y"][0]])
        point_2 = np.array([self.landmarks_selected_align["x"]
                            [1], self.landmarks_selected_align["y"][1]])

        self.ux = point_1[0]
        self.uy = point_1[1] + (point_2-point_1)[0]//3
        self.lx = point_2[0]
        self.ly = point_2[1] + 4*(point_2-point_1)[0]//3

        self.roi_zone_img = cv2.cvtColor(self.align_img, cv2.COLOR_GRAY2BGR)
        cv2.rectangle(self.roi_zone_img, (self.lx, self.ly),
                      (self.ux, self.uy), (0, 255, 0), 2)

        self.roi_img = self.align_img[self.uy:self.ly, self.ux:self.lx]

    # PUBLIC METHODS

    def extract_roi(self, path_in_img, rotate=False):
        #####
        self.in_img_c = cv2.imread(path_in_img)

        if(rotate):
            self.in_img_c = cv2.rotate(self.in_img_c, cv2.ROTATE_90_CLOCKWISE)

        if len(self.in_img_c.shape) == 3:
            self.in_img_g = cv2.cvtColor(self.in_img_c, cv2.COLOR_BGR2GRAY)
        else:
            self.in_img_g = self.in_img_c

        self._threshold()
        self._contours()
        self._landmarks()
        self._landmarks_select()
        self._alignement()
        self._roi_extract()

    def save(self, path_out_img):
        #####
        cv2.imwrite(path_out_img, self.roi_img)

    def show_result(self):
        #####
        plt.figure()

        plt.subplot(241)
        plt.imshow(self.in_img_g, cmap="gray")
        plt.title("original")

        plt.subplot(242)
        plt.imshow(self.thresh_img, cmap="gray")
        plt.title("threshold")

        plt.subplot(243)
        plt.imshow(self.contour_img, cmap="gray")
        plt.plot(self.center_point["x"], self.center_point["y"], 'bx')
        plt.title("contours")

        plt.subplot(244)
        plt.imshow(self.in_img_c, cmap="gray")
        for idx in range(len(self.landmarks["x"])):
            plt.plot(self.landmarks["x"][idx], self.landmarks["y"][idx], 'rx')
        plt.title("landmarks")

        plt.subplot(245)
        plt.imshow(self.in_img_c, cmap="gray")
        plt.plot(self.landmarks_selected["x"][0],
                 self.landmarks_selected["y"][0], 'rx')
        plt.plot(self.landmarks_selected["x"][1],
                 self.landmarks_selected["y"][1], 'rx')
        plt.title("selected")

        plt.subplot(246)
        plt.imshow(self.align_img, cmap="gray")
        plt.plot(self.landmarks_selected_align["x"][0],
                 self.landmarks_selected_align["y"][0], 'rx')
        plt.plot(self.landmarks_selected_align["x"][1],
                 self.landmarks_selected_align["y"][1], 'rx')
        plt.title("alignement")

        plt.subplot(247)
        plt.imshow(self.roi_zone_img, cmap="gray")
        plt.title("roi zone")

        plt.subplot(248)
        plt.imshow(self.roi_img, cmap="gray")
        plt.title("extraction")

        plt.show()