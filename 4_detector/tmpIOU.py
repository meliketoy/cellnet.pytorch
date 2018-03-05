import os
import cv2
import sys
import csv
import math
import numpy as np

sum_IOU = 0
sum_OTE = 0
len_A_tot = 0
len_B_tot = 0

tot_TP = 0
tot_FP = 0

for i in range(1, (27+1)):
    print("Calculating IOU for TEST%d..." %i)
    with open('./results/cropped/TEST%d/TEST%d.csv' %(i,i)) as pred_csv:
    #thresh = 200
    #with open('./results/baseline/%d/TEST%d/TEST%d.csv' %(thresh,i,i)) as pred_csv:
        with open('/home/bumsoo/Data/test/Test_tight/TEST%d/TEST%d.csv' %(i,i)) as answ_csv:
            img = cv2.imread('/home/bumsoo/Data/test/CT_20/TEST%d.png' %i)
            pred_reader = csv.reader(pred_csv)
            answ_reader = csv.reader(answ_csv)

            lst_A, lst_B = [], []

            for row in pred_reader:
                lst_A.append(row)
                pred = row[0]

            for row in answ_reader:
                lst_B.append(row)
                label = row[0]

            len_A_tot += len(lst_A)
            len_B_tot += len(lst_B)

            once = 1

            for comp_A in lst_A:
                A_x, A_y, A_w, A_h = map(int, comp_A[1:])
                pred = comp_A[0]
                max_IOU = 0

                cv2.putText(img, str(pred), (A_x+A_w, A_y+A_h), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2, cv2.LINE_AA)
                cv2.rectangle(img, (A_x, A_y), (A_x+A_w, A_y+A_h), (0,255,0), 2)

                for comp_B in lst_B:
                    B_x, B_y, B_w, B_h = map(int, comp_B[1:])
                    label = comp_B[0]

                    in_x1 = max(A_x, B_x)
                    in_x2 = min(A_x+A_w, B_x+B_w)
                    in_w = in_x2 - in_x1

                    in_y1 = max(A_y, B_y)
                    in_y2 = min(A_y+A_h, B_y+B_h)
                    in_h = in_y2 - in_y1

                    if (in_w < 0 or in_h < 0):
                        interArea = 0
                    else:
                        interArea = in_w * in_h

                    unionArea = A_w * A_h + B_w * B_h - interArea

                    IOU = float(interArea) / float(unionArea)
                    if (once > 0):
                        cv2.putText(img, str(label), (B_x, B_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 2, cv2.LINE_AA)
                        cv2.rectangle(img, (B_x, B_y), (B_x+B_w, B_y+B_h), (255, 0, 0), 2)
                    if(IOU != 0.0):
                        cv2.rectangle(img, (in_x1, in_y1), (in_x2, in_y2), (0,0,255), 2)
                        cv2.putText(img, str(IOU), (in_x1+in_w/2, in_y1 + in_h/2),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2, cv2.LINE_AA)

                        sum_IOU += IOU
                        sum_OTE += math.sqrt((B_x-A_x)**2 + (B_y-A_y)**2)

                once = 0

            cv2.imwrite("./IOU/ours_TEST%d.png" %i , img)
            #cv2.imwrite("./IOU/baseline_%d_TEST%d.png" %(thresh, i), img)
