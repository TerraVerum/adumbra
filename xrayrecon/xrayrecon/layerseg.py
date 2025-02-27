from typing import Sequence, Tuple, Union

import cv2 as cv
import numpy as np
from qtextras import multiprocessApply
from scipy.signal import find_peaks, peak_prominences, peak_widths
from scipy.stats import norm


def templateMatchScores(cube: np.ndarray):
    # if (cube > 0).sum()/cube.size < 0.1:
    #   return np.zeros(cube.shape[-1]-1)
    # Transpose the volume to orient according to the slice plane selection
    filCube = cv.morphologyEx(cube, cv.MORPH_CLOSE, np.ones((3, 3)))
    scores = []
    iterCube = filCube.transpose([2, 0, 1])
    for prevSlice, curSlice in zip(iterCube, iterCube[1:, ...]):
        score = cv.matchTemplate(prevSlice, curSlice, cv.TM_CCOEFF)
        scores.append(score[0, 0])
    scores = np.array(scores)
    scores /= scores.max()
    return scores


def layerInfoFromScores(scores: np.ndarray):
    diff2 = np.diff(scores, 2)
    # Pad so that indices match locations in `scores`
    diff2 = np.concatenate([[0], diff2, [0]])
    diff2 /= diff2.max()
    peaks, _ = find_peaks(diff2, height=0.2)
    # Since 'peaks' should represent pairs of start, stop idxs, make sure there are
    # an even number of them
    peaks = peaks[len(peaks) % 2 :]
    pairs = [peaks[start : start + 2] for start in range(0, len(peaks), 2)]
    # Add dummy first pair for easier loop logic
    pairs.insert(0, [-1, -1])
    layerNames = []
    layerSlices = []
    for ii, pair in enumerate(pairs[1:], 1):
        # Pairs should start right before the base of each correlation peak, not
        # at the exact start
        pair[0] -= 1
        pair[-1] += 1
        layerNames.append(f"Via {ii-1}-{ii}")
        layerSlices.append([pairs[ii - 1][1] + 1, pair[0] - 1])
        layerNames.append(f"Layer {ii}")
        layerSlices.append(pair.tolist())
    # Drop first bad via layer
    del layerNames[0]
    del layerSlices[0]
    # Make sure layers start and stop at beginning and end of cube
    layerSlices[0][0] = 0
    layerSlices[-1][-1] = len(scores) - 1
    layerSlices = [np.arange(s[0], s[1] + 1, dtype=int) for s in layerSlices]
    ret = {"Layer Name": layerNames, "Slices": layerSlices}
    return ret


sz = Tuple[int, int]


def scoresLstForWindow(cube: np.ndarray, winSize: sz, spacing=1):
    """
    :param cube: 3d data cube to test layer scores on
    :param winSize: (w, h) of the analysis window
    """
    cubeH, cubeW = cube.shape[:2]
    winH, winW = winSize
    rrange = np.arange(0, cubeH - winH + 1, spacing)
    crange = np.arange(0, cubeW - winW + 1, spacing)

    def window_gen():
        for ii in rrange:
            for jj in crange:
                yield cube[ii : ii + winH, jj : jj + winW, :]

    tot = (cubeH - winH) * (cubeW - winW) / (spacing**2)

    scoresLst = np.asarray(
        multiprocessApply(
            templateMatchScores, window_gen(), "getting scores", total=tot, debug=True
        )
    )

    return scoresLst


def layerInfoForWindow(
    cube, winSizes: Union[sz, Sequence[sz]], spacing=1, returnMetric=False
):
    if isinstance(winSizes[0], int):
        winSizes = [winSizes]
    scoresLst = []
    for size in winSizes:
        scoresLst.append(scoresLstForWindow(cube, size, spacing))
    scoresLst = np.vstack(scoresLst)
    features = getFeatures(scoresLst)
    bestIdx = int(np.argmax(features))
    bestScores = scoresLst[bestIdx]
    layerInfo = layerInfoFromScores(bestScores)

    # iv = overlayFeatures_win_slice(cube, crange, rrange, features, winW, winH)
    if returnMetric:
        return layerInfo
    return None


def getFeatures(scoresLst: np.ndarray):
    scores = np.vstack(scoresLst)
    # Throw out peaks we are pretty sure don't hold up right away
    # maxNormedScore = scores.max(1)
    # scores = scores[maxNormedScore > 0.3]
    features = np.array([_peakFeatures(s) for s in scores])
    features[~np.isfinite(features)] = 0
    return features


def _peakFeatures(score):
    # Rule out generally bad scores
    if score.max() == 0:
        return 0
    peaks, features = find_peaks(score, height=0.2)
    widths = peak_widths(score, peaks)[0].astype(int)
    proms = peak_prominences(score, peaks)[0]
    widths[widths == 0] = 1
    errs = []
    for peak, width in zip(peaks, widths):
        gausPortion = score[peak - width : peak + width]
        mean, std = norm.fit(gausPortion)
        if len(gausPortion) == 0:
            continue
        x = np.linspace(gausPortion.min(), gausPortion.max(), 2 * width)
        y = norm.pdf(x, mean, std)
        errs.append(np.abs(gausPortion - y[: len(gausPortion)]).mean())

    retVal = len(peaks)
    retVal *= features["peak_heights"].mean()
    retVal *= np.diff(peaks).mean()
    retVal *= proms.mean()
    retVal *= len(peaks)
    retVal /= np.mean(errs)
    return retVal
