import pyAgrum as gum
import pyAgrum.lib.dynamicBN as gdyn
import pyAgrum.lib.notebook as gnb
import pyAgrum.lib.explain as expl

from world_space.curr_world_space import interactables, interactions, interactions_dict, gestures
import dbn_helpers.gaze_and_gesture_cpds as cpds 
import dbn_helpers.gaze_and_gesture_dynamic_cpds as dynamic_cpds


class GazeAndGestureNet:
    def __init__(self):

        # string constructors using CBTs we already have 
        prior_constructor = f"""HA0{{{'|'.join(gestures)}}}; I0{{{'|'.join(interactions)}}}; GA0{{{'|'.join(interactables)}}}"""
        trans_constructor = f"""HA0->HAt{{{'|'.join(gestures)}}}; I0->It{{{'|'.join(interactions)}}}; GA0->GAt{{{'|'.join(interactables)}}}"""
        obs_constructor = f"""HAt<-It->GAt; GOt{{{'|'.join(interactables)}}}<-GAt; HOt{{{'|'.join(gestures)}}}<-HAt"""

        constructor = (prior_constructor + ";" + trans_constructor + ";" + obs_constructor).strip()

        # create a 2TBN representation of the DBN
        # a two-slice temporal Bayes net (2TBN)
        # https://www.cs.ubc.ca/~murphyk/Papers/dbnchapter.pdf
        self.twoTBN = gum.BayesNet.fastPrototype(constructor)

        self.initialize_all_cpds()

        self.one_slice_posteriors = {}
        self.all_slices_posteriors = {}
        self.network_observed_evidence = {}

        self.originalIt_cpd = self.twoTBN.cpt("It")[:]
        self.originalGA_cpd = self.twoTBN.cpt("GAt")[:]
        self.originalHA_cpd = self.twoTBN.cpt("HAt")[:]
        self.prior_certain_action_index = -1
        self.It_cpd_update_count = 0
        self.It_skewed_index_prior = -1


    def update(self, input_evidence_one_time_slice, visualize_inference=True, inference_engine="LazyPropagation"):
        """
            evidence_one_time_slice: 
                dictionary, e.g.: {'t0': {'GO0': 'music', 'HO0': 'tap'}}
        """
        t = int(list(input_evidence_one_time_slice.keys())[0][1:])
        # dynamic unroll 2-TBN
        # TODO store original cpd if dynamically updated cpd
        dbn = gdyn.unroll2TBN(self.twoTBN, 2)

        if inference_engine == "LazyPropagation":
            ie = gum.LazyPropagation(dbn)
        else:
            #TODO
            pass

        # add observed evidence to the 2-TBN
        evidence_this_step = list(input_evidence_one_time_slice.values())[0]
        evidence_types = list(evidence_this_step.keys())
        evidence_obs = list(evidence_this_step.values())
        for ev_i in range(len(evidence_types)):
            self.network_observed_evidence[f"{evidence_types[ev_i][:2]}1"] = evidence_obs[ev_i]   
        
        if t == 0:
            self.network_observed_evidence['I0'] = dbn.cpt('I0').toarray()
            self.network_observed_evidence['GA0'] = dbn.cpt('GA0').toarray()
            self.network_observed_evidence['HA0'] = dbn.cpt('HA0').toarray()

        elif t > 0: 
            # set posteriors from last time slice as priors
            # one_slice_posteriors should always be posteriors from last time slice, clear when taken, to store new posterior
            prior_from_posterior = {}
            # change name to t0 before adding for this 2-TBN
            for i in range(len(self.one_slice_posteriors.items())):
                key = list(self.one_slice_posteriors.keys())[i]
                new_key = f"{key[:-1]}0"
                prior_from_posterior[new_key] = list(self.one_slice_posteriors.values())[i]
            
            # put priors in update network_observed_evidence 
            self.network_observed_evidence.update(prior_from_posterior)
    
            # dynamically update cpd for I
            
            previous_posteriors_I = prior_from_posterior['I0']
            It_skewed_index = dynamic_cpds.if_certain_twoTBN_prior(previous_posteriors_I)
            if (It_skewed_index != -1):
                if(self.prior_certain_action_index == -1 or self.It_skewed_index_prior == It_skewed_index):
                    if(self.It_cpd_update_count < 5):
                        scaled_It_cpd = dynamic_cpds.scale_cpd(self.twoTBN.cpt('It')[:])
                        print("original cpd: ", self.twoTBN.cpt('It')[:])
                        print("scaled cpd: ", scaled_It_cpd)
                        self.update_cpt('It', scaled_It_cpd)
                        self.It_cpd_update_count += 1
                    else:
                        self.It_cpd_update_count = 0
                        self.update_cpt('It', self.originalIt_cpd) 
                self.prior_certain_action_index = It_skewed_index
                



            # if t > 1:
            #     print("one slice looks like this: ", self.one_slice_posteriors.get('I1', {}))
            #     # update dynamic cpds
            #     self.update_dynamic_cpds()

            #     #TODO the cpd should go back to the original cpd if the distribution shifts


            # one_slice_posteriors should always be posteriors from last time slice, clear when taken, to store new posterior
            self.one_slice_posteriors.clear()
        
        # set all evidence in inference engine
        # network_observed_evidence stores the evidence for each time step, alo use for visualization
        ie.setEvidence(self.network_observed_evidence)

        # exclude priors and observable values from target
        nodes_w_evidences = ie.softEvidenceNodes().union(ie.hardEvidenceNodes())
        # exclude observable nodes from target
        network_inference_targets = set(ie.targets()).difference(nodes_w_evidences)

        
        targets_to_infer = {dbn.idFromName('GA1'), dbn.idFromName('HA1'), dbn.idFromName('I1')}
        #TODO fix assertion here
        # assert targets_to_infer == network_inference_targets,"""
        #   f"t{t}: inference targets are not correctly set\n
        #   currently setting {sorted(network_inference_targets)}"""
        
        ie.setTargets(network_inference_targets)
        # run junction-tree-based inference
        ie.makeInference()
        print("makinginference")

        # get and store posteriors to be prior for the next time step
        for var in network_inference_targets:
            target_name = dbn.variable(var).name()
            self.one_slice_posteriors[target_name] = ie.posterior(target_name).tolist()
            self.all_slices_posteriors[f"t{t}"] = self.one_slice_posteriors

        if visualize_inference:
            # visualize inference at this tim step
            gnb.showInference(dbn, evs=self.network_observed_evidence)

        # clear the evidence dictionary as it is just used for visualization at this time step
        self.network_observed_evidence.clear()
        # self.update_cpt('It', self.originalIt_cpd )
        print(f"t{t} posteriors: {self.one_slice_posteriors}")
        return f"t{t} posteriors: {self.one_slice_posteriors}"


    def initialize_all_cpds(self):
        cpd_I0 = cpds.I0_prior()
        self.add_cpt('I0', cpd_I0)

        cpd_GA0 = cpds.GA0_prior()
        self.add_cpt('GA0', cpd_GA0)

        cpd_HA0 = cpds.HA0_prior()
        self.add_cpt('HA0', cpd_HA0)

        cpd_HOt = cpds.cpd_HOt(w_HA_HO_match=5)
        self.add_cpt('HOt', cpd_HOt)

        cpd_GOt = cpds.cpd_GOt(w_GA_GO_match=5) 
        self.add_cpt('GOt', cpd_GOt)

        cpd_GAt = cpds.cpd_GAt(w_given_GA0=3, w_given_It=5)
        self.add_cpt('GAt', cpd_GAt)
        
        cpd_HAt = cpds.cpd_HAt(w_given_HA0=5, w_given_It=5)
        self.add_cpt('HAt', cpd_HAt)

        cpd_It = cpds.cpd_It(w_given_I0=6)
        self.add_cpt('It', cpd_It)



    def update_dynamic_cpds(self):
        previous_posteriors_I = self.one_slice_posteriors.get('I1', [])
        if len(previous_posteriors_I) > 0:
            cpd_It = dynamic_cpds.dynamic_cpd_It(previous_posteriors_I, 'kl_divergence')
            self.update_cpt('It', cpd_It)


    def update_cpt(self, var, cpd):
        self.twoTBN.cpt(var)[:] = cpd

    def add_cpt(self, var, cpd):
        self.twoTBN.cpt(var)[:] = cpd

    def show_cpt(self, var):
        self.twoTBN.cpt(var)

    def visualize_entropy(self):
        expl.showInformation(self.twoTBN)




