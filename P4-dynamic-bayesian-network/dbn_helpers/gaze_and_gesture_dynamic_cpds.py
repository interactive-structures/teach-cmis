import numpy as np
import pyAgrum as gum
from scipy.stats import dirichlet
from scipy.special import rel_entr

from world_space.curr_world_space import interactions



def if_certain_twoTBN_prior(previous_posteriors_l, approach='z_score', w_given_I0=10, factor=2, scaling_strategy = 'expponential',\
                    threshold=0.2, kl_threshold=0.4, entropy_threshold=1.0, gini_threshold=0.3, z_threshold = 2.0):
                    #typicall z>2 is considered as outlier
    previous_posteriors = dict(zip(interactions, previous_posteriors_l))

    if approach == 'threshold':
        for i, interaction in enumerate(interactions):
            if previous_posteriors[interaction] > threshold * np.mean(list(previous_posteriors.values())):
                return i

    elif approach == "z_score":
        mean = np.mean(previous_posteriors_l)

        std_dev = np.std(previous_posteriors_l)

        z_scores = (previous_posteriors_l - mean)/std_dev
        z_above = np.where(z_scores > z_threshold)[0]
        if z_above.shape[0] > 0:
            return z_above[0]

            
    elif approach == 'kl_divergence':
        uniform_dist = np.ones(len(interactions)) / len(interactions)
        p = list(previous_posteriors.values())
        q = uniform_dist
        kl = rel_entr(np.asarray(p, dtype=np.float64), np.asarray(q, dtype=np.float64))
        print("kl: ", kl)
        # kl_divergence = calculate_kl_divergence(list(previous_posteriors.values()), uniform_dist)
        if sum(kl) > kl_threshold:
            print("kl skewed: ", np.where(kl > kl_threshold))
            return np.where(kl > kl_threshold)

    # elif approach == 'entropy':
    #     entropy = calculate_entropy(previous_posteriors_l)
    #     if entropy < entropy_threshold:
    #         return True
    # elif approach == 'gini':
    #     gini = calclate_gini(previous_posteriors_l)
    #     if gini > gini_threshold:
    #         return True
    return -1


def scale_cpd(original_cpd, scaling_strategy = 'power'):
    dirichlet_cpd = np.ones(original_cpd.shape)
    scaled_cpd = np.power(original_cpd, 3)
    
    for i in range(scaled_cpd.shape[0]):
        scaled_cpd_row = scaled_cpd[i, :]
        # dirichlet_It[i, :] = dirichlet.rvs(alpha_row, size=1).flatten()
        ### [TEMP] change to deterministic dirichlet to test
        dirichlet_cpd[i, :] = dirichlet.mean(scaled_cpd_row).flatten()
    return dirichlet_cpd