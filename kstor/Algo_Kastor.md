# Pseudo-algo

## A. Stratified Sampling 

1. Initialize from the shape ($s*$) a dictionary, which is describing the each properties $p_i$ of $s*$, the property statistics set:
   $P_{nb}= \\{(p_1,0),..,(p_i,0),..,(p_n,0) \\}$
2. Sample a dataset $D$ of size $N$ tuples graph-text $(g,t)$ from your distilled Knowledge base
3. Update $Prop_{count}$ by iterating over $D$: <br>
&nbsp;&nbsp;&nbsp;For $(g_i,t_i)$ in $D$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;For each $p_j$ of $g_i$ : <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $$P_{nb}\[p_j\]=P_{nb}\[p_j\]+1$$

4. Define $\mu_p$ : <br>
   $$\mu_p = \frac{1}{|P_{nb}|} \sum_{i=1}^{|P_{nb}|} \frac{P_{nb}\[p_i\]}{N}$$
  
5. Initialize the $s_-$ as an empty set, and iterate over the property stats $P_{nb}$: <br>
&nbsp;&nbsp;&nbsp; For $p_i$ in $P_{nb}$:<br>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; $$freq_{p_i}= \frac{P_{nb}\[p_i\]}{N}$$<br>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; If $$freq_{p_i} \lt  \mu_p$$:<br>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Add $p_i$ in $s_-$

6. Initialize class set $$C= s_-$$ and the class statistics set:<br>
$C_{nb}= \\{(c_1,0),..,(c_i,0),..,(c_n,0) \\}$

7. Attach now for each tuple of $D$ a stratum $c$:<br>
&nbsp;&nbsp;&nbsp;For $(g_i,t_i)$ in $D$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; If $g_i$ do not contain a property listed in $s_-$: $c_i=$"Other" <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Elif: $g_i$ contains only one property $p_i$ listed in $s_-$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $c_i=p_i$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $C_{nb}\[c_i\]=+1$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Elif: $g_i$ contains more than one property $p_i$ listed in $s_-$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Attribute the least represented stratum of $C_{nb}$ to $c_i$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $C_{nb}\[c_i\]=+1$ <br>


## B. Template-based synthetic generation

### B1. KR0

1. Initiliaze the set of seed entities $Seed_data$ containing $N$ graph-text tuples and define the number of synthetic examples that must be generated $M$
2. Initiliaze the dictionary $Patt_{real}= \\{\\}$
3. Compute the number of realization in $Seed_data$ of each patterns: <br>
&nbsp;&nbsp;&nbsp;For $(g_i,t_i)$ in $D$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; define $Patt_i$ as the ordered set of properties described in $g_i$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; If $Patt_i$ not in $Patt_{real}$ : $Patt_{real}\[Patt_i\]=0$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $Patt_{real}\[Patt_i\]=+1$ <br>
4. Filter the set by keeping only the pattern of $Patt_{real}$ with $Patt_i$: $Patt_{real}\[Patt_i\]>= 2$ and save the result in $Patt_{real}2$
5. Initialise the set of the synthetic example $Synth_data$
6. Run the generation:

While $|Synth_data|$ < $M$: <br>
&nbsp;&nbsp;&nbsp; Select a random $Patt_p$ from $Patt_{real}2$ <br>
&nbsp;&nbsp;&nbsp; Select a entity $e_i$ following $Patt_p$ <br>
&nbsp;&nbsp;&nbsp; Select a entity $e_j$ !=  $e_i$ following $Patt_p$ <br>
&nbsp;&nbsp;&nbsp; If the couple $(e_i,e_j)$ do not exist in $Synth_data$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  

## Sampling 
