# Pseudo-algo

## A. Stratified Sampling 

**Input:** a optimal shape $s*$, a predefined sample size $N$, and distilled Knowledge base  $\mathcal{K}_{distill.}(s^*)$  <br>
**Output:** a startified sample $D_c$   <br>

-- **Begin:**<br>
1. Initialize from the shape ($s*$) a dictionary $P_{no}$, latter use to compute the number of occurences of each $p_i$ of $s*$, as:
   $P_{no}= \\{(p_1,0),..,(p_i,0),..,(p_n,0) \\}$
2. Sample a dataset $D$ of size $N$ tuples graph-text $(g,t)$ from $\mathcal{K}_{distill.}(s^*)$
3. Update $P_{no}$ by iterating over $D$: <br>
&nbsp;&nbsp;&nbsp;For each $(g_i,t_i)$ of $D$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;For each $p_j$ of $g_i$ : <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $$P_{no}\[p_j\]=P_{no}\[p_j\]+1$$

4. Define $\mu_p$ : <br>
   $$\mu_p = \frac{1}{|P_{no}|} \sum_{i=1}^{|P_{no}|} \frac{P_{no}\[p_i\]}{N}$$
  
5. Initialize the $s_-$ as an empty set, and iterate over the property stats $P_{no}$: <br>
&nbsp;&nbsp;&nbsp; For $p_i$ in $P_{no}$:<br>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; $$freq_{p_i}= \frac{P_{no}\[p_i\]}{N}$$<br>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; If $$freq_{p_i} \lt  \mu_p$$:<br>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Add $p_i$ in $s_-$

6. Initialize class set $$C= s_-$$ and the class statistics set:<br>
$C_{nb}= \\{(c_1,0),..,(c_i,0),..,(c_n,0) \\}$

7. Attach now for each tuple of $D$ a stratum $c$:<br>
Initialize the $D_c$ the resulting startified sample <br>
&nbsp;&nbsp;&nbsp;For each $(g_i,t_i)$ of $D$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; If $g_i$ do not contain a property listed in $s_-$: $D_{ci}=(g_i,t_i,"Other")$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Elif: $g_i$ contains only one property $p_i$ listed in $s_-$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  $D_{ci}=(g_i,t_i,p_i)$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $C_{nb}\[p_i\]=+1$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Elif: $g_i$ contains more than one property $p_i$ listed in $s_-$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Find the least represented stratum of $C_{nb}$: $p_-$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $D_{ci}=(g_i,t_i,p_-)$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $C_{nb}\[p_-\]=+1$ <br>
--**End**<br>

## B. Template-based synthetic generation

### B1. KR0
**Input:** a set $Seed_{data}$ containing $n$ entities, prefined the number $N$ of synthetic examples that must be generated, and distilled Knowledge base $\mathcal{K}_{distill.}$ <br>
**Output:** a set $Synth_{data}$ of $N$ generated quadruple $(e_1,e_2,g_2,\hat{w_2})$ <br>

-- **Begin:**<br>
1. Initiliaze the dictionary $Patt_{real}= \\{\\}$
2. Compute the number of realization in $Seed_{data}$ of each patterns: <br>
&nbsp;&nbsp;&nbsp;For each $e_i$ in $Seed_{data}$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; get the associated graph-text couple $(g_i,t_i)$ associated to $e_i$ in $\mathcal{K}_{distill.}$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; define $Patt_i$ as the ordered set of properties described in $g_i$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; If $Patt_i$ not in $Patt_{real}$ : $Patt_{real}\[Patt_i\]=0$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $Patt_{real}\[Patt_i\]=+1$ <br>
3. Filter the dictionnary $Patt_{real}$ by keeping only the pattern: $Patt_{real}\[Patt_i\]>= 2$ and save the result in $Patt_{real}2$
4. Initialise the set of the synthetic example $Synth_{data}$
5. Run the generation:

&nbsp;&nbsp;&nbsp;While $|Synth_{data}|$ < $M$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Select a random $Patt_p$ from $Patt_{real}2$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Select a entity $e_i$ related to a graph $g_i$ following $Patt_p$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Select a entity $e_j$ related to a graph $g_j$ following $Patt_p$ with $e_j$ !=  $e_i$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; If $(e_i,e_j)$ and $(e_j,e_i)$ do not exist in $Synth_data$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Create a template $t_i$ from $w_i$ the abstract associated to $e_i$ in $\mathcal{K}_{distill.}$,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; by masking each properties values of $g_i$, the graph associated to $e_i$, in $w_i$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Fill the template $t_i$ with the data of $g_j$ the graph associated to $e_j$ in $\mathcal{K}_{distill.}$ this new abstract is named $\hat{w_j}$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Add $(e_i,e_j,g_j,\hat{w_j})$ in $Synth_{data}$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Create a template $t_j$ from $w_j$ the abstract associated to $e_j$ in $\mathcal{K}_{distill.}$,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; by masking each properties values of $g_j$, the graph associated to $e_j$, in $w_j$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Fill the template $t_j$ with each properties values of $g_i$ the graph associated to $e_i$ in $\mathcal{K}_{distill.}$ this new abstract is named $\hat{w_i}$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Add $(e_j,e_i,g_i,\hat{w_i})$ in $Synth_{data}$ <br>
--**End**<br>

## Sampling 
