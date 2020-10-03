# -*- coding: UTF-8 -*-

from PROIE import *

if __name__ == '__main__':
    #####
    path_in_img = "resources/palmprint.jpg"

    proie = PROIE()

    proie.extract_roi(path_in_img, rotate=True)
    proie.show_result()
    proie.save("resources/palmprint_roi.jpg")