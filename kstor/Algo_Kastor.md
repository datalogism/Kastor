# Pseudo-algo

## 1. Stratified Sampling 

1. Initialize from the shape ($s*$) a dictionary, which is describing the each properties $p_i$ of $s*$:
   $P_{nb}= \\{(p_1,0),..,(p_i,0),..,(p_n,0) \\}$
2. Sample a dataset $D$ of size $N$ tuples graph-text $(g,t)$ from your distilled Knowledge base
3. Update $Prop_{count}$ by iterating over $D$: <br>
&nbsp;&nbsp;&nbsp;For $(g_i,t_i)$ in $D$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;For each $p_j$ of $g_i$ : <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $$P_{nb}\[p_j\]=P_{nb}\[p_j\]+1$$

4. Define $\mu_p$ : <br>
   $$\mu_p = \frac{1}{|P_{nb}|} \sum_{i=1}^{|P_{nb}|} \frac{P_{nb}\[p_i\]}{N}$$
  
5. Initialize the $s*_-$ as an empty set, and iterate over the property stats $P_{nb}$: <br>
&nbsp;&nbsp;&nbsp; For $p_i$ in $P_{nb}$:<br>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; $$freq_{p_i}= \frac{P_{nb}\[p_i\]}{N}$$<br>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; If $$freq_{p_i} \lt  \mu_p$$:<br>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Add $p_i$ in $s*_-$

6. Initialize 



Get a sample of N graph-text tuples
1. Get the statistics concerning all the properties of $$s^*$$ in your knowledge base and define a probability threhold $\mu_p$ under which a property is defined as rare  
2. First define two subsets of the maximal shape $s^*$ studied:  $s^*_-$ and $s^*_+$, with $s^*_-$ gathering the rare properties and $s^*_-$ gathering the frequent properties
3. Defined a number of example you 
i=0

## Sampling 
