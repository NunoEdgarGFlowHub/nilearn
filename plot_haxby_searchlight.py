from matplotlib import pyplot
from sklearn.cross_validation import KFold
from sklearn.metrics import f1_score


### Load Haxby dataset ########################################################
from nisl import datasets
dataset = datasets.fetch_haxby()
fmri_data = dataset.data
mask = dataset.mask
affine = dataset.affine
y = dataset.target
conditions = dataset.target_strings
session = dataset.session

### Preprocess data ###########################################################
import numpy as np

# Change axis in order to have X under n_samples * x * y * z
X = np.rollaxis(fmri_data, 3)
# X.shape is (1452, 41, 40, 49)

# Detrend data on each session independently
from scipy import signal
for s in np.unique(session):
        X[session == s] = signal.detrend(X[session == s], axis=0)

### Prepare the masksi ########################################################
# Here we will use several masks :
# * mask is the original mask
# * process_mask is a subset of mask, it contains voxels that should be
#   processed (we only keep the slice z = 26)
mask = (dataset.mask != 0)
process_mask = mask.copy()
process_mask[..., 27:] = False
process_mask[..., :25] = False

### Restrict to faces and houses ##############################################

# Keep only data corresponding to face or houses
condition_mask = np.logical_or(conditions == 'face', conditions == 'house')
X = X[condition_mask]
y = y[condition_mask]
session = session[condition_mask]
conditions = conditions[condition_mask]

### Searchlight ###############################################################

from nisl import searchlight

# Make processing parallel
# /!\ As each thread will print its progress, this could mess up a little
#     information output.
n_jobs = 2

score_func = f1_score

# A cross validation method is needed to measure precision of each voxel
cv = KFold(y.size, k=4)
searchlight = searchlight.SearchLight(mask, process_mask, radius=1.5,
        n_jobs=n_jobs, score_func=score_func, verbose=True, cv=cv)
# scores.scores is an array containing per voxel precision
scores = searchlight.fit(X, y)

### Unmask the data and display it
pyplot.imshow(np.rot90(scores.scores[..., 26]), interpolation='nearest',
        cmap=pyplot.cm.spectral, vmin=0, vmax=1)
pyplot.colorbar()
pyplot.show()