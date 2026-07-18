I want to analyze every final lattice and calculate the average cluster size. This will probably be computationally expensive but I wanna answer the following question:

for high supersaturations (high mu values): is the configuration really fully mixed (no local clusters) or do we have to domains with finite size (red/blue clusters) that just flop and back and forth. Both situations produce the same order parameter $m=0$. So, I want to study the order parameter $q$ (number of "wrong bonds"), and $r$ which is the average cluster size. $q$ is already calculated for the supersaturation so we should need $<q>$ and the correspondingn standard error for every mu.

The cluster size can be something like:

We define a cluster C(x) as the maximal700
set of connected lattice sites (i, j) with a given particle state k (k ∈ {r, b}
for active red and blue particles, respectively) where connectivity means that
(i, j) and (i′, j′) share at least one edge. The size |C(k)| of every cluster is
the cardinality of said set. We only regard clusters with a cardinality larger
than four. The average cluster size is then given as the average of these
cardinalities ⟨s(k)⟩. Finally, we normalize by the number of overall lattice
sites in the system to obtain the average, normalized cluster size r(k):
r(k) = ⟨s(k)⟩ x × y
If not mentioned otherwise, we report the average, normalized cluster
size for blue particles r(b). Both order parameters were measured within the
limits of 0.2x to 0.7x to disregard any boundary effects of the ends of the
simulation box.
