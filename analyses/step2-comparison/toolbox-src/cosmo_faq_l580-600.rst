        - makes it easier to "directly interpret the meaning of (what may ideally be) separable sub-clusters or local maxima within very extended clusters".
        - is less affected by nonstationarity.

    2) support for any type of modality that CoSMoMVPA supports, including:

        - fMRI volumetric, e.g. voxel, or voxel x time
        - fMRI surface-based, e.g. node, or node x time
        - MEEG time x channel (both in sensor and source space)
        - MEEG time x channel x frequency (both in sensor and source space)

        In the case of multiple dimensions (such as time x channel x frequency) it is possible to cluster only over a subset of the dimensions. For example, a time x channel x frequency dataset can be clustered over all dimensions, or clustered over channel x frequency (which allows for more precise temporal inferences), or over channel x time (for more precise frequency inferences).

    3) support for either standard permutation test, or the method by Stelzer et al. (2012). To use the Stelzer approach, the user has to generate null datasets themselves. :ref:`cosmo_randomize_targets` can be used for this, but requires using a for-loop to generate multiple null datasets.

Because components 1-3 can be crossed arbitrarily, it allows for multiple comparison correction for a wide variety of applications.

Notes:
    - There is no function for within-subject significance testing; through cosmo_randomize_targets and a ``for``-loop the user can do that themselves.
    - There is also univariate cosmo_stat for one-sample and two-sample t-tests, and one-way and repeated measures ANOVA.


