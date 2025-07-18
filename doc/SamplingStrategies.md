# 📶 Sampling Strategies

## Stratified Sampling

### PseudoAlgo
**Input:** 
* a optimal shape $s^*$
* a predefined sample size $N$
* a Knowledge base  $\mathcal{K}$ <br>

**Output:** a startified sample $D_c$   <br>

-- **Begin**<br>
1. Initialize from the shape ($s*$) a dictionary $P_{no}$, latter use to compute the number of occurences of each properties $p_i$ of $s*$, as:
   $P_{no}= \\{(p_1,0),..,(p_i,0),..,(p_n,0) \\}$
2. Sample a dataset $D$ of size $N$ tuples graph-text $(g,t)$ from $\mathcal{K}$
3. Update $P_{no}$ by iterating over $D$: <br>
**For each** $(g_i,t_i)$ of $D$: <br>
└──  **For each** $p_j$ of $g_i$ : <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └──  $$P_{no}\[p_j\]=P_{no}\[p_j\]+1$$

4. Define $\mu_p$ : <br>
   $$\mu_p = \frac{1}{|P_{no}|} \sum_{i=1}^{|P_{no}|} \frac{P_{no}\[p_i\]}{N}$$
  
5. Initialize the $s_-$ as an empty set, and iterate over the property stats $P_{no}$: <br>
**For each** $p_i$ in $P_{no}$:<br>
├── $$freq_{p_i}= \frac{P_{no}\[p_i\]}{N}$$<br>
└── **If** $$freq_{p_i} \lt  \mu_p$$: Add $p_i$ in $s_-$

6. Initialize class set $$C= s_-$$ and the class statistics set:<br>
$C_{nb}= \\{(c_1,0),..,(c_i,0),..,(c_n,0) \\}$

7. Attach now for each tuple of $D$ a stratum $c$:<br>
Initialize the $D_c$ the resulting startified sample <br>
**For each** $(g_i,t_i)$ of $D$: <br>
├── **If** $g_i$ do not contain a property listed in $s_-$: $D_{ci}=(g_i,t_i,"Other")$ <br>
├── **Else if** $g_i$ contains only one property $p_i$ listed in $s_-$: <br>
&nbsp;| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├──  $D_{ci}=(g_i,t_i,p_i)$  <br>
&nbsp;| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └──  $C_{nb}\[p_i\]=+1$ <br>
└── **Else if** $g_i$ contains more than one property $p_i$ listed in $s_-$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├──   Find the least represented stratum of $C_{nb}$: $p_-$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├──  $D_{ci}=(g_i,t_i,p_-)$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └──  $C_{nb}\[p_-\]=+1$ <br>
--**End**<br>
