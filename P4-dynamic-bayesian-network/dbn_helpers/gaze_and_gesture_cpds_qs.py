import numpy as np
import pyAgrum as gum
from scipy.stats import dirichlet

# quick start cpds for gaze and gesture 

from world_space.curr_world_space import gestures, interactions, interactables, interactions_dict

def I0_prior(weight=100, rvs = True):
    alpha_I0 = np.ones(len(interactions)) * weight
    # if rvs:
    #     dirichlet_I0 = dirichlet.rvs(alpha_I0, size=1).flatten()
    # else:
    #     # deterministic dirichlet
    #     dirichlet_I0 = dirichlet.mean(alpha_I0, size=1).flatten()
    ### [TEMP] change to deterministic dirichlet to test
    dirichlet_I0 = dirichlet.mean(alpha_I0).flatten()
    return dirichlet_I0

def GA0_prior(weight=100, rvs=True):
    alpha_GA0 = np.ones(len(interactables)) * weight
    # if rvs:
    #     dirichlet_GA0 = dirichlet.rvs(alpha_GA0, size=1).flatten()
    # else:
    #     dirichlet_GA0 = dirichlet.mean(alpha_GA0, size=1).flatten()
    ### [TEMP] change to deterministic dirichlet to test
    dirichlet_GA0 = dirichlet.mean(alpha_GA0).flatten()
    return dirichlet_GA0

def HA0_prior(weight=100, rvs=True):
    alpha_HA0 = np.ones(len(gestures)) * weight
    # if rvs:
    #     dirichlet_HA0 = dirichlet.rvs(alpha_HA0, size=1).flatten()
    # else:
    #     dirichlet_HA0 = dirichlet.mean(alpha_HA0, size=1).flatten()
    ### [TEMP] change to deterministic dirichlet to test
    dirichlet_HA0 = dirichlet.mean(alpha_HA0).flatten()
    return dirichlet_HA0

def cpd_GOt(w_GA_GO_match=5):
    alpha_GO = np.ones((len(interactables), len(interactables)))
    dirichlet_GO = np.ones(alpha_GO.shape)
    np.fill_diagonal(alpha_GO, w_GA_GO_match)
    for i in range(alpha_GO.shape[0]):
        alpha_row = alpha_GO[i, :]
        # dirichlet_GO[i, :] = dirichlet.rvs(alpha_row, size=1).flatten()
        ### [TEMP] change to deterministic dirichlet to test
        dirichlet_GO[i, :] = dirichlet.mean(alpha_row).flatten()
    return dirichlet_GO


def cpd_HOt(w_HA_HO_match=5, rvs=True):
    alpha_HO = np.ones((len(gestures), len(gestures)))
    dirichlet_HO = np.ones(alpha_HO.shape)
    np.fill_diagonal(alpha_HO, w_HA_HO_match)
    for i in range(alpha_HO.shape[0]):
        alpha_row = alpha_HO[i, :]
        # if rvs:
        #     dirichlet_HO[i, :] = dirichlet.rvs(alpha_row, size=1).flatten()
        # else:
        #     dirichlet_HO[i, :] = dirichlet.mean(alpha_row).flatten()
        ### [TEMP] change to deterministic dirichlet to test
        dirichlet_HO[i, :] = dirichlet.mean(alpha_row).flatten()
    return dirichlet_HO

def cpd_It(w_given_I0=10):
    alpha_It = np.ones((len(interactions), len(interactions)))*3
    dirichlet_It = np.ones(alpha_It.shape)
    np.fill_diagonal(alpha_It, w_given_I0)
    for i in range(alpha_It.shape[0]):
        alpha_row = alpha_It[i, :]
        # dirichlet_It[i, :] = dirichlet.rvs(alpha_row, size=1).flatten()
        ### [TEMP] change to deterministic dirichlet to test
        dirichlet_It[i, :] = dirichlet.mean(alpha_row).flatten()
    return dirichlet_It


def cpd_GAt(w_given_GA0=10, w_given_It=10):
    alpha_GAt_It = np.ones((len(interactions), len(interactables)))
    alpha_GAt_GA0_It = np.ones((len(interactions), len(interactables), len(interactables)))
    alpha_GAt_GA0 = np.ones((len(interactables), len(interactables)))
    np.fill_diagonal(alpha_GAt_GA0, w_given_GA0)

    for i in range(len(interactions)):
        for j in range(len(interactables)):
            if j == len(interactables):
                continue
            elif interactions[i] in interactions_dict[interactables[j]]:
                alpha_GAt_It[i, j] = w_given_It

    for i in range(len(interactions)):
        for j in range(len(interactables)):
            for k in range(len(interactables)):
                # TODO: say in paper using chain rule to derive this cpd, with additional weight for adjusting mutual information between nodes
                alpha_GAt_GA0_It[i, j, k] = alpha_GAt_It[i, k] * alpha_GAt_GA0[k, j]

    # dirichlet_GAt_GA0_It = np.apply_along_axis(lambda row: dirichlet.rvs(row, size=1).flatten(), 2, alpha_GAt_GA0_It)
    ### [TEMP] change to deterministic dirichlet to test
    dirichlet_GAt_GA0_It = np.apply_along_axis(lambda row: dirichlet.mean(row).flatten(), 2, alpha_GAt_GA0_It)
    return dirichlet_GAt_GA0_It


def cpd_HAt(w_given_HA0=10, w_given_It=10, w_no_gesture_detected=100):
    # TODO gpt will be queried as an interaction designer for "expert elicitation" when user enters a new environment
    # placeholder for now (like HA0)
    gpt_elicitation = np.array([[0., 0., 0., 0., 7., 0.], 
                                [0., 7., 0., 0., 0., 0.], 
                                [0., 0., 7., 0., 0., 0.], 
                                [7., 0., 0., 0., 0., 0.], 
                                [0., 0., 0., 7., 0., 0.], 
                                [0., 7., 0., 0., 0., 0.], 
                                [0., 0., 0., 7., 0., 0.], 
                                [0., 0., 7., 0., 0., 0.], 
                                [0., 0., 0., 0., 0., 7.]]).astype(float)
    # episilon = 1
    # gpt_elicitation[gpt_elicitation == 0] = episilon
    # alpha_HAt_It = gpt_elicitation
    alpha_HAt_It = np.where(gpt_elicitation == 0, 1, w_given_It)
    alpha_HAt_It[-1, -1] = w_no_gesture_detected
    # alpha_HAt_It[-1, -1] = w_no_gesture_detected                
    alpha_HAt_HA0 = np.ones((len(gestures), len(gestures)))
    np.fill_diagonal(alpha_HAt_HA0, w_given_HA0)

    alpha_HAt_HA0_It = np.ones((len(interactions), len(gestures), len(gestures)))

    for i in range(len(interactions)):
        for j in range(len(gestures)):
            for k in range(len(gestures)):
                alpha_HAt_HA0_It[i, j, k] = alpha_HAt_It[i, k] * alpha_HAt_HA0[k, j]


    # dirichlet_HAt_HA0_It = np.apply_along_axis(lambda row: dirichlet.rvs(row, size=1).flatten(), 2, alpha_HAt_HA0_It)
    ### [TEMP] change to deterministic dirichlet to test
    dirichlet_HAt_HA0_It = np.apply_along_axis(lambda row: dirichlet.mean(row).flatten(), 2, alpha_HAt_HA0_It)
    return dirichlet_HAt_HA0_It
