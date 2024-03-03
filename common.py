from datetime import datetime
import json
import os
import shutil
import sys

from PIL import Image, ImageFont, ImageDraw
import requests
import logging

import cfg

testsRan = 0
testsSkipped = 0
testsFailed = 0
testsPassed = 0
testsWarned = 0
progressCnt = 0
startCnt = 0
startTime = datetime.now()

"""if cfg.debugPrintOn == "N" prints a '.' wrapped at maxProgressCnt columns"""

log = logging.getLogger('tootImg')
log.setLevel(logging.INFO)
handler = logging.FileHandler("tootBI.log")
formatter = logging.Formatter(
    "%(asctime)s : %(name)s  : %(funcName)s : %(levelname)s : %(message)s"
)
handler.setFormatter(formatter)
log.addHandler(handler)


def progressPrint():
    global progressCnt
    
    progressCnt += 1
    if progressCnt >= cfg.maxProgressCnt:
        sys.stdout.write('\r')
        progressCnt = 0
    sys.stdout.write('.')


"""single point to turn off all the debug messages or preappend a newline and reset progressCnt"""


def dprint(msg):
    global progressCnt

    if cfg.debugPrintOn == "Y":
        if progressCnt > 0:
            log.info("")
            progressCnt = 0

        log.info(msg)

"""log tests as skipped"""        


def skipped(msg, skipped):
    global testsSkipped
    
    testsSkipped += skipped
    log.info("Skipped " + str(skipped) + " " + msg)


"""if cfg.debugPrintOn == "Y" adds new line to log so progress dots do not make messages appear off screen""" 


def addNL():
    global progressCnt

    if progressCnt > 0:
        log.error("")
        progressCnt = 0


"""if failOnError == "Y" ends testing with message
if failOnError == "N" calls warn with msg"""


def fail(msg):
    global testsFailed
    
    addNL()
    testsFailed += 1
    if cfg.failOnError == "Y":
        raise ValueError("FAILED:" + msg)
    else:
        addNL()    
        log.error("\nFAILED:" + msg + "\n")


"""write msg to stderr"""


def warn(msg):
    global testsWarned
    
    addNL()    
    testsWarned += 1
#    sys.stderr.write("WARN:" + msg + "\n")
    log.warn("\n" + msg + "\n")


"""if cfg.debugPrintOn == "Y" prints PASSED: msg otherwise a '.'"""


def passed(msg):
    global testsPassed
    
    testsPassed += 1
    if cfg.debugPrintOn == "Y":
        addNL()
        log.info("PASSED:" )
        log.info(str(msg))
    else:
        progressPrint()

    log.info("testsPassed:" + str(testsPassed))


""" Increment testsRan """


def incTestRan():
    global testsRan
    testsRan += 1
    log.info("testsRan:" + str(testsRan))


""" Get testsRan """


def getTestRan():
    global testsRan
    return testsRan


""" Get testsPassed """


def getTestsPassed():
    global testsPassed
    return testsPassed


""" Get testsSkipped """


def getTestsSkipped():
    global testsSkipped
    return testsSkipped


""" Get testsFailed """


def getTestsFailed():
    global testsFailed
    return testsFailed


""" Get testsSkipped """


def getTestsWarned():
    global testsWarned
    return testsWarned


""" Reset test counters """


def resetTestCnts(text=None):
    global testsRan
    global testsSkipped
    global testsFailed
    global testsPassed
    global testsWarned
    global startCnt

    startCnt = 0
    testsRan = 0
    testsSkipped = 0
    testsFailed = 0
    testsPassed = 0
    testsWarned = 0
    logStart(text)


def chkTestCnts(ran, passed, skipped, failed, warned):
    global testsRan
    global testsSkipped
    global testsFailed
    global testsPassed
    global testsWarned
    
    assertEqual("TestRan", ran, testsRan)
    assertEqual("TestsPassed", passed + 1, testsPassed)
    assertEqual("TestsSkipped", skipped, testsSkipped)
    assertEqual("TestsFailed", failed, testsFailed)
    assertEqual("TestsWarned", warned, testsWarned)
    if skipped > 0:
        log.info("\n" + str(skipped) + " skipped tests expected")
    if failed > 0:
        log.info("\n" + str(failed) + " failed tests expected")
    if warned > 0:
        log.info("\n" + str(warned) + " warned tests expected")


"""initialize vars for test counting and timing"""


def logStart(text=None):
    global startCnt
    global startTime
    global testsRan

    startCnt = testsRan
    log.info("startCnt:" + str(startCnt))
    startTime = datetime.now()
    if not text == None:
        log.info(text)


"""output info about the test set just run"""


def logEnd(text):
    global startCnt
    global startTime
    global testsRan
    global testsSkipped

    log.info("startCnt:" + str(startCnt))
    idx = text.rfind(' ')
    if idx == -1:
        log.error("\nRan " + str(testsRan - startCnt) + " " + text + " tests in " + str(datetime.now() - startTime))
        showTestReport()
    else:
        log.info("\n" + text + " in " + str(datetime.now() - startTime))
    # log.info("\nProcessed " + str(testsRan) + " mapping files, " + str(testsSkipped) + " could not be processed in " + str(datetime.now() - startTime))

"""if test is true run method
if test is false add tests to skip count."""


def logit(test, method, msg, skipCnt):
    if test: 
        method()
    else:
        skipped(msg, skipCnt)

"""if test is true call passed
if test is false call fail"""


def assertTrue(msg, test):
    incTestRan()
    if test:
        passed(msg)
    else:
        fail(msg)

"""if expected == found is true call passed
if expected == found is false call fail
"""


def assertEqual(msg, expected, found):
    incTestRan()
    if expected == found:
        passed(msg)
    else:
        fail(msg + ": expected:" + str(expected) + " but got:" + str(found))

"""if test is true call passed
if test is false call warn"""


def warnTrue(msg, test):
    incTestRan()
    if test:
        passed(msg)
    else:
        warn(msg)

"""send a command to DeepStack
:param testType: API part of URL that goes after v1/vision/ :class:`String` object.
:param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
:param \*\*kwargs: Optional arguments that ``request`` takes.
returns JSON object of response
"""


def doPost(url, data=None, **kwargs):
    """Sends a POST request, gets clean response and checks it for success

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """
    log.info("url:"+url)
    response = requests.post(url, data=data, **kwargs)
    log.info(url + " returned " + str(response.status_code))
    if response.status_code == 200:
        jres = response.json()
    # deserializes into dict and returns dict.
    # note needs this to clean up or will fail when reading some responses.
        jres = json.loads(json.dumps(jres))
        log.info("jres string = " + str(jres))
        return jres
    else:  # Since we have no json to return fake some up in case we are not failing on errors.
        return json.loads('{ "duration": 0, "predictions": [], "success": true }')


"""read in binary file and return"""


def readImageFile(fileName):
    return readBinaryFile(os.path.join(cfg.imgPath , fileName))


"""read in binary file and return"""


def readBinaryFile(filePath):
    return readFile(filePath, "rb")


"""read in binary file and return"""


def readTextFile(filePath):
    return readFile(filePath, "r")


"""read in binary file and return"""


def readFile(filePath, readType):
    incTestRan()
    # with closes on section exit
    if os.path.exists(filePath):
        with open(filePath, readType) as f:
            if f.mode == readType:
                data = f.read()
                passed(str(testsRan) + ":Reading " + filePath)
                return data
            else:
                skipped(str(testsRan) + ":Could not read " + filePath, 1)
    else:
        skipped(str(testsRan) + ":Could not find " + filePath, 1)
        
    return ""


"""write list like classes.txt out"""


def writeList(path, filename, lines, mode="w"):
    if not os.path.isdir(path):
        os.makedirs(path)
    with open(os.path.join(path, filename), mode) as fout:
        if fout.mode == mode:
            for line in lines:
                fout.write(line + "\n")
        else:
            raise ValueError("FAILED to write to " + os.path.join(path , filename))

""" read the classes.txt file in folder and return lines as a list.
If classes.txt does not exist, returns empty list
"""


def readClassList(folder):
    rtn = readTextFile(os.path.join(folder , "classes.txt"))
    if rtn == "":
        return []
    else:
        return rtn.splitlines()

"""add an image filename and object's confidence to to a list file named objName+".lst.txt" in the debug files folder 
so we can easily find files with objects of a type or no objects in them"""


def appendDebugList(objName, filename, confidence):
    with open(os.path.join(cfg.debugPath, objName + ".lst.txt"), "a") as fout:
        if fout.mode == "a":
                fout.write(filename + " " + str(confidence) + "\n")
        else:
            raise ValueError("FAILED to write to " + os.path.join(cfg.debugPath , objName + ".lst.txt"))


"""remove all the old debug files in cfg.debugPath"""


def clearDebugPics():
    clearFolder(cfg.debugPath)

    
"""remove all the files in folder"""


def clearFolder(folder):
    try:
        shutil.rmtree(folder)
        os.mkdir(folder)
    except OSError as e:
        warn("Error: %s : %s" % (folder, e.strerror))


def clearDebugLists():
    try:
        for fn in os.listdir(cfg.debugPath):
            if fn.endswith(".lst.txt"):
                os.remove(os.path.join(cfg.debugPath, fn)) 
    except OSError as e:
        warn("Error: %s : %s" % (cfg.debugPath, e.strerror))


"""Quick test that the server is up."""


def serverUpTest():
    logStart()
    response = requests.get(cfg.dsUrl)
    if not response.status_code == 200:
        raise ValueError("FAILED:DeepStack respond with:" + str(response.status_code))

    logEnd("server up")


""" generate a map file path from the folder and imgName by swapping the extension with '.txt' """


def getMapFileName(folder, imgName):
    idx = imgName.rfind('.')
    return os.path.join(folder, imgName[0:idx] + ".txt")


""" Get the names of all the image files in folder """


def getImgNames(folder):
        return getfileNames(folder, cfg.includedExts)


""" Get the names of all the files in folder with an extension in includedExts """


def getfileNames(folder, includedExts=cfg.includedExts):
        imgNames = [fn for fn in os.listdir(folder)
        if any(fn.endswith(ext) for ext in includedExts)]
        return imgNames


def genMap(fromFolder, toFolder):
    with open(os.path.join(toFolder, "classes.map.txt"), "w") as fout:
        if fout.mode == "w":
            fromClasses = readClassList(os.path.join(fromFolder, "classes.txt"))  
            toClasses = readClassList(os.path.join(toFolder, "classes.txt"))  
            clsOut = []
            for index in range(len(fromClasses)):
                name = fromClasses[index]
                if not name in toClasses:
                    toClasses.append(name)
                
                clsOut.append(toClasses.index(name))    
                srcdId = newClasses.index(name)
                self.idxMap[srcdId] = clsOut.index(name)
                line = "Mapping:" + str(srcdId) + ":" + name + " used " + str(self.clsCnt[index]) + " times to " + str(self.idxMap[srcdId]) + ":" + clsOut[self.idxMap[srcdId]]
                passed(line)
                fout.write(line + "\n")
    return clsOut

""" Check the number of files of a type are in folder
Pass [] as includedExts to look at all files.
"""


def chkFileCnt(folder, includedExts, expectedCnt):
    if len(includedExts) > 0: 
        imgNames = [fn for fn in os.listdir(folder)
        if any(fn.endswith(ext) for ext in cfg.includedExts)]
        return imgNames
    else:
        imgNames = os.listdir(folder)
       
    assertEqual("Files in " + folder + ":\n" + str(imgNames) + "\n", expectedCnt, len(imgNames)) 


""" Compare generated map file for imgFilename in srcFolder with saved expected file in expectedFolder """


def compareMapFiles(srcFolder, expectedFolder, imgFilename):
    gennedMap = getMapFileName(srcFolder, imgFilename)
    assertTrue("No generated map found for " + imgFilename, os.path.exists(gennedMap))
    createdData = readTextFile(gennedMap).splitlines()
    expectedMap = getMapFileName(expectedFolder, imgFilename)
    assertTrue("No expected map found for " + imgFilename, os.path.exists(gennedMap))
    expectedData = readTextFile(expectedMap).splitlines()
    for index in range(len(expectedData)):
        assertEqual("Map data mismatch", expectedData[index], createdData[index])


""" Compare generated file with saved expected file """


def compareTextFiles(createdFilePath, expectedFilePath):
    assertTrue("No generated file found " + createdFilePath, os.path.exists(createdFilePath))
    createdData = readTextFile(createdFilePath)
    assertTrue("No expected file found " + expectedFilePath, os.path.exists(expectedFilePath))
    expectedData = readTextFile(expectedFilePath)
    assertEqual("Map data", expectedData, createdData)

"""If savePath != None Save the cropped image that was found by object detection.
if mergePath != None the marks up image with rectangle around and label on found object
Mainly for checking extra objects found in tests. """


def saveFound(item, imgPath, savePath=None, mergePath=None):
    image = Image.open(imgPath).convert("RGB")
    y_max = int(item["y_max"])
    y_min = int(item["y_min"])
    x_max = int(item["x_max"])
    x_min = int(item["x_min"])
    # Save the cropped image that was found by object detection.
    if not savePath == None:
        cropped = image.crop((x_min, y_min, x_max, y_max))
        cropped.save(savePath)
        
    # highlight found object on debug image
    if not mergePath == None:
        if os.path.exists(mergePath):
            image = Image.open(mergePath).convert("RGB")
            labelImg(mergePath, image, item["label"], x_min, y_min, "green", x_max, y_max)
            
    return image.size


def labelImg(mergePath, image, text, x_min, y_min, color="black", x_max=-1, y_max=-1):

        draw = ImageDraw.Draw(image)
        if x_max > -1 and y_max > -1:
            # xy – Two points to define the bounding box. Sequence of either [(x0, y0), (x1, y1)] or [x0, y0, x1, y1]. The second point is just outside the drawn
            draw.rectangle((x_min, y_min, x_max, y_max), fill=None, outline=color)

        font = ImageFont.truetype("arial", size=20)
        # get text size
        draw.text((x_min, y_min), text, font=font, fill=color)
        image.save(mergePath)
        
        return image

"""If savePath != None Save the cropped image that was mapped in training file.
Mainly for checking missed objects found in tests. """


def saveExpected(data, imgPath, savePath=None, mergePath=None, text=""):
    image = Image.open(imgPath).convert("RGB")
    w, h = image.size

    # Object ID    x_center    y_center    x_width    y_height
    xy = data.split()
    x_center = float(xy[0]) * w
    y_center = float(xy[1]) * h
    x_width = float(xy[2]) * w
    y_height = float(xy[3]) * h
    y_max = int(y_center + y_height / 2)
    y_min = int(y_center - y_height / 2)
    x_max = int(x_center + x_width / 2)
    x_min = int(x_center - x_width / 2)
    # Save the cropped image that was found by object detection.
    if not savePath == None:
        cropped = image.crop((x_min, y_min, x_max, y_max))
        cropped.save(savePath)
        
    # highlight found object on debug image
    if not mergePath == None:
        if os.path.exists(mergePath):
            image = Image.open(mergePath).convert("RGB")

        labelImg(mergePath, image, text, x_min, y_min, "red", x_max, y_max)
        
    return image.size


"""to help with debug and tweaking of maps update the class lists for debugPath and lableImg"""


def saveLabels2labelImgData(classList):
    writeList(cfg.debugPath , "classes.txt", classList)

    if os.path.exists(cfg.labelImgData):
        writeList(cfg.labelImgData , "predefined_classes.txt", classList)
        writeList(cfg.labelImgData , "predefined_classes." + cfg.trainedName + ".txt", classList)

"""
Creates path if needed
Throws ValueError if path already exists and is not a folder
"""        


def mkdirs(path):
    if not os.path.exists(path):
        os.makedirs(path)
    if not os.path.isdir(path):
        raise ValueError(path + " exists and is not a folder!")

"""
Moves or copies as allowed srcFile to dstFolder
Creates dstFolder if needed
Note throws Error if file already exists and overwrite is not True
"""        


def mv(srcFile, dstFolder, overwrite=None):
    mkdirs(dstFolder)
    if (overwrite):
        dstFolder = os.path.join(dstFolder, shutil._basename(srcFile))
    shutil.move(srcFile, dstFolder)

"""
Show cfg options being used
"""        


def showConfig():
    log.error("Using folders:")
    log.error("trainPath:" + cfg.trainPath)
    log.error("testPath:" + cfg.testPath)
    log.error("validPath:" + cfg.validPath)
    log.error("labeled:" + cfg.labeled)
    log.error("unlabeled:" + cfg.unlabeled)
    log.error("newPicPath:" + cfg.newPicPath)
    log.error("debugPath:" + cfg.debugPath)
    log.error("\nimgPath:" + cfg.imgPath)
    log.error("labelImgData:" + cfg.labelImgData)
    
    log.error("\nUsing options:")
    log.error("dsUrl:" + cfg.dsUrl)
    log.error("mode:" + cfg.mode) 
    log.error("trainedName:" + cfg.trainedName) 
    log.error("maxProgressCnt:" + str(cfg.maxProgressCnt))
    log.error("debugPrintOn:" + cfg.debugPrintOn)
    log.error("saveDebugPics:" + cfg.saveDebugPics)
    log.error("failOnError:" + cfg.failOnError)
    log.error("min_confidence:" + str(cfg.min_confidence))
    log.error("includedExts:" + str(cfg.includedExts))
    log.error("tests2Run:" + str(cfg.tests2Run)) 

"""
Sets trainPath to path and sets testPath, vaildPath, labeled, unlabeled and debugPath relative to it.
Effectively changes from using the deepstack folder to a models folder.
if newPath is not empty then sets paths relative to it instead.
"""        


def setPaths(path="", newPath=""): 
    if len(path) > 0:
        cfg.trainPath = path.replace("\\", "/")
    
    if len(newPath) > 0:
        newPath = newPath.replace("\\", "/")
        if not newPath.endswith("/"):
            newPath = newPath + "/"
        cfg.newPicPath = newPath
        cfg.trainPath = os.path.join(newPath, "../train")
        mkdirs(cfg.trainPath)
    
    if not cfg.trainPath.endswith("/"):
        cfg.trainPath = cfg.trainPath + "/"
        
    if not cfg.trainPath.endswith("train/"):
        cfg.trainPath = os.path.join(cfg.trainPath, "train/")
    
    if not os.path.exists(cfg.trainPath):
        raise ValueError(cfg.trainPath + " does not exist")
    
    cfg.testPath = cfg.trainPath.replace("train/", "test/")
    mkdirs(cfg.testPath)
    cfg.validPath = cfg.trainPath.replace("train/", "valid/")
    mkdirs(cfg.validPath)
    cfg.labeled = cfg.trainPath.replace("train/", "labeled/")
    mkdirs(cfg.labeled)
    cfg.unlabeled = cfg.trainPath.replace("train/", "unlabeled/")
    mkdirs(cfg.unlabeled)
    cfg.debugPath = cfg.trainPath.replace("train/", "debug.pics/")  
    mkdirs(cfg.debugPath)
    
    if cfg.debugPrintOn == "Y":
        showConfig()
    
"""
Check toPath ends with subFolder
if not adds subFolder to toPath
Then creates toPath if needed.
"""


def genFolder(toPath, subFolder):
    if not toPath.endswith("/"):
        toPath = toPath + "/"
        
    if not subFolder.endswith("/"):
        subFolder = subFolder + "/"
        
    if not toPath.endswith(subFolder):
        toPath = os.path.join(toPath, subFolder)
    
    if not os.path.exists(toPath):
        os.mkdir(toPath)
        
    return toPath

""" If fout is not None write test report summary to a file
Otherwise to the screen
"""


def showTestReport(fout=None):
    if fout == None:
        log.error("")
        otherPassed = testsRan - testsPassed - testsWarned - testsFailed
        log.error("Of " + str(testsRan + testsSkipped) + " tests")
        log.error(" Ran:" + str(testsRan))
        log.error(" Skipped:" + str(testsSkipped))
        log.error(" Passed:" + str(testsPassed + otherPassed))
        log.error(" Warnings:" + str(testsWarned))
        log.error(" Failed:" + str(testsFailed))
    else:
        fout.write("\n")
        fout.write("Of " + str(testsRan + testsSkipped) + " tests\n")
        fout.write(" Ran:" + str(testsRan) + "\n")
        fout.write(" Skipped:" + str(testsSkipped) + "\n")
        fout.write(" Passed:" + str(testsPassed) + "\n")
        fout.write(" Warnings:" + str(testsWarned) + "\n")
        fout.write(" Failed:" + str(testsFailed) + "\n")
