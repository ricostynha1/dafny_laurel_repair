from multiprocess import Pool
import os
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster

HOLE = ("HOLE", "<__>")


class MostSimilarSubsequence:
    """
    Compute the most similar subsequence of s and t.
    `comp` is a binary function that compares elements from s and t, and returns
    a float in [0, 1] representing the similarity between the two elements,
    where 0 means the elements are completely dissimilar and 1 means they are
    identical.
    """

    def __init__(self, s: list, t: list, comp) -> None:
        self.s = s
        self.t = t
        self.comp = comp

        # self.mss_val[i, j] = the similarity of the most similar subsequence of s[:i] and t[:j]
        self.mss_val = np.zeros((len(s) + 1, len(t) + 1), dtype=float)
        self.mss_prev = np.ones((len(s) + 1, len(t) + 1, 2), dtype=int) * -1
        # 0: skip both, 1: skip s, 2: skip t, 3: match
        self.mss_choice = np.zeros((len(s) + 1, len(t) + 1), dtype=int)
        self.mss_contrib = np.zeros((len(s) + 1, len(t) + 1), dtype=float)
        self.comp_res = np.zeros((len(s) + 1, len(t) + 1), dtype=float)
        self._compute_mss()

        self.s_sub, self.t_sub = None, None
        self._backtrack_mss()

        self.similarity_map = None
        self._define_similarity()

    def _compute_mss(self):
        # for i in range(1, len(self.s) + 1):
        #     for j in range (1, len(self.t) + 1):
        #         # Compute the similarity between the two elements
        #         self.comp_res[i, j] = self.comp(self.s[i - 1], self.t[j - 1])
        #         # If we match the current elements?
        #         match = self.mss_val[i - 1, j - 1] + self.comp_res[i, j]
        #         # If we skip the current element in s
        #         skip_s = self.mss_val[i - 1, j]
        #         # If we skip the current element in t
        #         skip_t = self.mss_val[i, j - 1]

        #         self.mss_val[i, j] = self.mss_val[i - 1, j - 1]
        #         # # This should be already initialized
        #         # self.mss_prev[i, j] = [-1, -1]
        #         # self.mss_choice[i, j] = 0

        #         if match > self.mss_val[i, j]:
        #             self.mss_val[i, j] = match
        #             self.mss_prev[i, j] = [-1, -1]
        #             self.mss_choice[i, j] = 3
        #         if skip_s > self.mss_val[i, j]:
        #             self.mss_val[i, j] = skip_s
        #             self.mss_prev[i, j] = [-1, 0]
        #             self.mss_choice[i, j] = 1
        #         if skip_t > self.mss_val[i, j]:
        #             self.mss_val[i, j] = skip_t
        #             self.mss_prev[i, j] = [0, -1]
        #             self.mss_choice[i, j] = 2

        # implement the above by iterating over the anti-diagonals
        for d in range(len(self.s) + len(self.t) + 1):
            for i in range(max(0, d - len(self.t)), min(len(self.s) + 1, d + 1)):
                j = d - i
                if i == 0 or j == 0:
                    self.mss_val[i, j] = 0
                    continue
                # Compute the similarity between the two elements
                self.comp_res[i, j] = self.comp(self.s[i - 1], self.t[j - 1])
                # If we match the current elements
                match = self.mss_val[i - 1, j - 1] + self.comp_res[i, j]
                # If we skip the current element in s
                skip_s = self.mss_val[i - 1, j]
                # If we skip the current element in t
                skip_t = self.mss_val[i, j - 1]

                self.mss_val[i, j] = self.mss_val[i - 1, j - 1]
                # # This should be already initialized
                # self.mss_prev[i, j] = [-1, -1]
                # self.mss_choice[i, j] = 0

                if match > self.mss_val[i, j]:
                    self.mss_val[i, j] = match
                    self.mss_prev[i, j] = [-1, -1]
                    self.mss_choice[i, j] = 3
                if skip_s > self.mss_val[i, j]:
                    self.mss_val[i, j] = skip_s
                    self.mss_prev[i, j] = [-1, 0]
                    self.mss_choice[i, j] = 1
                if skip_t > self.mss_val[i, j]:
                    self.mss_val[i, j] = skip_t
                    self.mss_prev[i, j] = [0, -1]
                    self.mss_choice[i, j] = 2

    def _backtrack_mss(self):
        i, j = len(self.s), len(self.t)
        self.s_sub, self.t_sub = [], []
        while i > 0 and j > 0:
            if self.mss_choice[i, j] == 3:
                self.s_sub.append(i - 1)
                self.t_sub.append(j - 1)
                # self.mss_contrib[i, j] = 1
                self.mss_contrib[i, j] = self.comp_res[i, j]
            # i, j = self.mss_prev[i, j]
            di, dj = self.mss_prev[i, j]
            i, j = i + di, j + dj
        self.s_sub.reverse()
        self.t_sub.reverse()

    def _define_similarity(self):
        mss = self.mss_val[len(self.s), len(self.t)]
        len_s, len_t = len(self.s), len(self.t)
        sim_mean = 2 * mss / (len_s + len_t) if len_s + len_t > 0 else 1
        sim_min = mss / min(len_s, len_t) if min(len_s, len_t) > 0 else 1
        sim_max = mss / max(len_s, len_t) if max(len_s, len_t) > 0 else 1
        self.similarity_map = {"mean": sim_mean, "min": sim_min, "max": sim_max}

    def mss(self):
        return self.mss_val[len(self.s), len(self.t)]

    def similarity(self, approx):
        if approx not in self.similarity_map:
            raise ValueError(f"Invalid approximation style: {approx}")
        return self.similarity_map[approx]

    def distance(self, approx):
        return 1 - self.similarity(approx)


class HierarchicalClustering:
    def __init__(self, objs, comp, method) -> None:
        self.objs = objs
        self.comp = comp
        self.method = method

        self.dist = None
        self._compute_distance_matrix()

        self.hac_res = None
        self._compute_hac()

    def _compute_distance_matrix(self):
        n = len(self.objs)
        self.dist = np.zeros((n, n))

        n_cpus = os.cpu_count() - 1
        print(f"Using {n_cpus} cpus for computing distances")

        def distance_across_row(reference_idx):
            print(f"Computing distances for row {reference_idx}")
            row = np.zeros(n)
            for i in range(n):
                if i > reference_idx:
                    row[i] = 1 - self.comp(self.objs[reference_idx], self.objs[i])
            return row

        # Create a pool of workers
        with Pool(n_cpus) as pool:
            rows = pool.map(distance_across_row, range(n))
            for i in range(n):
                self.dist[i] = rows[i]

        self.dist = self.dist + self.dist.T

    def _compute_hac(self):
        self.hac_res = linkage(self.dist, method=self.method)
        assert len(self.hac_res) == len(self.objs) - 1

    def add_row(self, obj):
        self.objs.append(obj)
        n = len(self.objs)

        def distance_across_row(reference_idx):
            print(f"Computing distances for row {reference_idx}")
            row = np.zeros(n)
            for i in range(n):
                row[i] = 1 - self.comp(self.objs[reference_idx], self.objs[i])
            return row

        row = distance_across_row(len(self.objs) - 1)
        self.dist = np.vstack([self.dist, row[:-1]])
        self.dist = np.hstack([self.dist, row.reshape(-1, 1)])
        return n - 1

    def remove_row(self, idx):
        self.objs.pop(idx)
        self.dist = np.delete(self.dist, idx, axis=0)
        self.dist = np.delete(self.dist, idx, axis=1)

    def get_size(self):
        return len(self.objs)

    def get_cluster(self, idx):
        """
        Return the cluster that was formed at the given iteration.
        """
        if idx < len(self.objs):
            return [idx]
        l_idx = int(self.hac_res[idx - len(self.objs), 0])
        r_idx = int(self.hac_res[idx - len(self.objs), 1])
        l_cluster = self.get_cluster(l_idx)
        r_cluster = self.get_cluster(r_idx)
        return l_cluster + r_cluster

    def in_order_aux(self, idx):
        if idx < self.get_size():
            return [idx]
        l_idx = int(self.hac_res[idx - self.get_size(), 0])
        r_idx = int(self.hac_res[idx - self.get_size(), 1])
        l_in_order = self.in_order_aux(l_idx)
        r_in_order = self.in_order_aux(r_idx)
        return l_in_order + r_in_order

    def in_order(self):
        return self.in_order_aux(2 * self.get_size() - 2)

    def top_k_clusters(self, k: int):
        cl_id = fcluster(self.hac_res, t=k, criterion="maxclust")
        n_clusters = max(cl_id)
        clusters = [[] for _ in range(n_clusters)]
        for i, c in enumerate(cl_id):
            clusters[c - 1].append(i)
        return clusters

    def clusters_by_k(self, k: float, criterion="distance"):
        """
        Return the clusters when cutting the dendrogram at height k.
        """
        cl_id = fcluster(self.hac_res, t=k, criterion=criterion)
        n_clusters = max(cl_id)
        clusters = [[] for _ in range(n_clusters)]
        for i, c in enumerate(cl_id):
            clusters[c - 1].append(i)
        return clusters

    def get_cluster_of_obj(self, obj_idx, threshold):
        """
        Return the cluster that the object at the given index belongs to.
        """
        print(f"threshold: {threshold}")
        obj_row = self.dist[obj_idx]
        # get the n min from that row indices
        t_closest = np.argsort(obj_row)[: threshold + 1]
        t_select = []
        print(obj_row)
        for i in range(threshold + 1):
            if obj_row[t_closest[i]] < 0.45:
                print(f"distance: {obj_row[t_closest[i]]}")
                t_select.append(t_closest[i])
        return None, t_select
        clusters = self.top_k_clusters(threshold)
        # clusters = self.clusters_by_k(threshold)
        for i, cluster in enumerate(clusters):
            if obj_idx in cluster:
                return i, cluster
        return None, None

    def centroid(self, cluster):
        # avg_dist = lambda p: sum(self.dist[p, q] for q in cluster) / len(cluster)
        avg_dist = lambda p: sum(self.dist[p, q] for q in cluster)
        ctr = min(cluster, key=avg_dist)
        return ctr

    def chebyshev_center(self, cluster):
        radius = lambda p: max(self.dist[p, q] for q in cluster)
        ctr = min(cluster, key=radius)
        return ctr

    def diff_exemplars(self, cluster):
        if len(cluster) == 1:
            return cluster[0], cluster[0]
        ctr = self.centroid(cluster)
        cluster = [c for c in cluster if c != ctr]
        return ctr, max(cluster, key=lambda c: self.dist[ctr, c])


def token_comp_dafny(t, k):
    if not isinstance(t, tuple) or not isinstance(k, tuple):
        return 0
    if t[0] != k[0]:
        return 0
    return 1


def line_comp(s, t):
    mss = MostSimilarSubsequence(s, t, token_comp_dafny)
    return mss.similarity("mean")


def id_comp(s, t):
    return 1 if s == t else 0


def mss_comp_aux(base_comp):
    def comp(s, t):
        if not isinstance(s, list) or not isinstance(t, list):
            return base_comp(s, t)
        else:
            mss = MostSimilarSubsequence(s, t, comp)
            return mss.similarity("mean")

    return comp


def hole_metacomp(comp):
    """
    Given a comparison function `comp`, extends it to compare holes.
    The behavior of holes is as wildcards: they match anything exactly i.e. with value 1.
    """

    def hole_comp(s, t):
        if s == HOLE or t == HOLE:
            return 0
        else:
            return comp(s, t)

    return hole_comp


def mss_anti_unify(s, t, base_comp):
    """
    Given two sequences `s` and `t`, return a sequence `u` that is the anti-unification of `s` and `t`.
    """
    if not isinstance(s, list) or not isinstance(t, list):
        # # maybe check if token_comp is zero then return HOLE
        # if token_comp(s, t) == 1:
        #     return s
        # else:
        #     return HOLE
        if base_comp(s, t) == 0:
            return HOLE
        else:
            # these should always be tokens in this case, and we make the choice to always return the first one
            if not isinstance(s, list):
                return s
            else:
                return t
    else:
        mss_res = MostSimilarSubsequence(s, t, mss_comp_aux(base_comp))
        # mss = MostSimilarSubsequence(s, t, hole_metacomp(mss_comp))
        u = []
        ci, cj = 0, 0
        for i, j in zip(mss_res.s_sub, mss_res.t_sub):
            holes = max(i - ci, j - cj)
            u += [HOLE for _ in range(holes)]
            u.append(mss_anti_unify(s[i], t[j], base_comp))
            ci, cj = i + 1, j + 1
        holes = max(len(s) - ci, len(t) - cj)
        u += [HOLE for _ in range(holes)]
        return u


def mss_anti_unify_many(sggs, base_comp):
    """
    Given a list of sequences `sggs`, return a sequence `u` that is the anti-unification of all `sggs`.
    """
    if len(sggs) == 0:
        return []
    u = sggs[0]
    for sgg in sggs[1:]:
        u = mss_anti_unify(u, sgg, base_comp)
    return u


def simplify_sketch(sketch):
    """
    Given a sketch, simplify it by merging contiguous holes, and doing so recursively.
    """
    if not isinstance(sketch, list):
        return sketch
    else:
        simplified = []
        i = 0
        while i < len(sketch):
            if sketch[i] == HOLE:
                j = i + 1
                while j < len(sketch) and sketch[j] == HOLE:
                    j += 1
                simplified.append(HOLE)
                i = j
            else:
                simplified.append(simplify_sketch(sketch[i]))
                i += 1
        return simplified
