"""
Posts the latest flagged picture in the Alerts folder to BI Mastodon account.
"""

import os
import sys
import glob
import re
import time
import cfg

from toot import console, User, App, http, config
from PIL import Image

from common import doPost, labelImg, writeList, readBinaryFile, readTextFile, getMapFileName, dprint

class TootImg():


    debugPath = "debug.pics/"

    def detect(self, color, testtype, filePath, srcImg, mergeImg, classes):
        filename = os.path.basename(filePath)
        dprint("Checking " + filePath + " with " + testtype)

        ## Send to DeepStack
        response = doPost(cfg.dsUrl + "v1/vision/" + testtype, files={"image":srcImg,"min_confidence": "0.70"})
        tidx = testtype.rfind('/')
        if tidx > 0:
            testtype = testtype[tidx + 1:]

        ## Nothing found
        if (len(response["predictions"]) == 0):
            return None
    
        idx = filename.rfind('.')
        description = "@bi #biAlert "

        outfile = self.debugPath + filename[0:idx] + ".labeled" + filename[idx:]
        dprint(outfile)
        ## Double check we have not done this one and the stamp changed or something else weird happened.
        if os.path.exists(outfile):
            print("Already posted:"+ outfile + "=" + time.strftime('%d %b %Y %H:%M:%S', time.localtime(os.path.getmtime(outfile))))
            return None
        
##mouse,bird,cat,horse,sheep,cow,elephant,bear,zebra,giraffe,pig,raccoon,coyote,squirrel,bunny,cat_black,cat_grey,cat_orange,cat_tort,cat_calico,cow,deer,opossum
        mode="w"
        cnt=0
        for item in response["predictions"]:
            try:
                idx = classes.index(item["label"])
            except ValueError:
                dprint("Filtering out:" + str(item["label"]))
                continue

            confidence = round(float(item["confidence"]) * 100, 2)
            if confidence < 70:
                errfile =  filename[0:idx] + ".err"
                with open(os.path.join(self.debugPath, errfile), mode) as fout:
                    if fout.mode == mode:
                        for line in response:
                            fout.write(line + "\n")
                    else:
                        raise ValueError("FAILED to write to " + os.path.join(path , filename))
                continue
                
            ## generate labled pic
            y_max = int(item["y_max"])
            y_min = int(item["y_min"])
            x_max = int(item["x_max"])
            x_min = int(item["x_min"])
            labelImg(outfile, mergeImg, item["label"] + ":" + testtype, x_min, y_min, color , x_max, y_max)

            # Object ID    x_center    y_center    x_width    y_height
            description  = description + " #" + str(item["label"]) + " " + str(confidence) + "%"    
            cnt = cnt + 1
    
        if cnt == 0:
            return None
            
        ## Send result to Mastodon
        args = []
        args.append("--debug")
        args.append("--verbose")
        args.append("-d")
        args.append(description)
        args.append("-m")
        args.append(outfile)
        args.append(description)
        dprint("Sending description:"+ description)
        user, app = config.get_user_app('bi@dea42.social')
        console.run_command(app, user, 'post', args)
        
        ## return file to let caller know we found a good one.
        return  outfile   

    def run(self, args):
        if len(args) < 2:
            print("USAGE: tootImg image")
            print(" imageFolderExp like HV445.20240225_124754.13165.3.jpg")
            return 
        
        dprint(args[1])
        classes = readTextFile("classes.txt").splitlines()
        dprint("Read:./classes.txt")
        dprint(classes)
               
        filename = args[1]
        try:
            dprint(filename)
            dprint(os.stat(filename))
            mergeimg = Image.open(filename).convert("RGB")
            srcimg = readBinaryFile(filename)
            outfile = self.detect('cyan', "custom/RMRR", filename, srcimg, mergeimg,classes)
            if outfile:         
                print ("marked up file written to " + outfile)
                lastrun=os.path.getmtime(filename)
                if os.path.getmtime(outfile) - lastrun > 43200:
                    print("Bumped lastrun from "+ time.strftime('%d %b %Y %H:%M:%S', time.localtime(lastrun)))
                    lastrun = lastrun + 43200
                    
                os.utime(self.debugPath,(lastrun,lastrun))
                print("Lastrun set to "+ time.strftime('%d %b %Y %H:%M:%S', time.localtime(lastrun)))
                return

        except Exception as inst:
            print(inst)
#########################################################


TootImg().run(sys.argv)
