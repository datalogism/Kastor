# 👶 Augmentation strategies

We detail in this document the algorithms implemented to reach a **sufficient exposure per property**

## 1. Template-based synthetic generation

### KR0 - same pattern level remplacement

#### Pseudo-Algo
**Input:** 
* a set $Seed_{data}$ containing $n$ entities
* a prefined the number $N$ of synthetic examples that must be generated
* a Knowledge base $\mathcal{K}$ <br>

**Output:** a set $Synth_{data}$ of $N$ generated quadruple $(e_1,e_2,g_2,\hat{w_2})$ <br>

-- **Begin**<br>
1. Initiliaze the dictionary $Patt_{real}= \\{\\}$
2. Compute the number of realization in $Seed_{data}$ of each patterns: <br>
**For each** $e_i$ in $Seed_{data}$: <br>
├── get the associated graph-text couple $(g_i,t_i)$ associated to $e_i$ in $\mathcal{K}$ <br>
├── define $Patt_i$ as the ordered set of properties described in $g_i$ <br>
├── **If** $Patt_i$ not in $Patt_{real}$: $Patt_{real}\[Patt_i\]=0$ <br>
└── $Patt_{real}\[Patt_i\]=+1$ <br>
4. Filter the dictionnary $Patt_{real}$ by keeping only the pattern: $Patt_{real}\[Patt_i\]>= 2$ and save the result in $Patt_{real}2$
5. Initialise the set of the synthetic example $Synth_{data}$
6. Run the generation:

**While** $|Synth_{data}|$ < $M$: <br>
├── Select a random $Patt_p$ from $Patt_{real}2$ <br>
├── Select a entity $e_i$ related to a graph $g_i$ following $Patt_p$ <br>
├── Select a entity $e_j$ related to a graph $g_j$ following $Patt_p$ with $e_j$ !=  $e_i$  <br>
└── **If** $(e_i,e_j)$ and $(e_j,e_i)$ do not exist in $Synth_{data}$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── Create a template $t_i$ from $w_i$ the abstract associated to $e_i$ in $\mathcal{K}$,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; by masking each properties values of $g_i$, the graph associated to $e_i$, in $w_i$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├──  Fill the template $t_i$ with the data of $g_j$ the graph associated to $e_j$ in $\mathcal{K}$ this new abstract is named $\hat{w_j}$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├──  Add $(e_i,e_j,g_j,\hat{w_j})$ in $Synth_{data}$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├──  Create a template $t_j$ from $w_j$ the abstract associated to $e_j$ in $\mathcal{K}$,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; by masking each properties values of $g_j$, the graph associated to $e_j$, in $w_j$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├──  Fill the template $t_j$ with each properties values of $g_i$ the graph associated to $e_i$ in $\mathcal{K}$ this new abstract is named $\hat{w_i}$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └──  Add $(e_j,e_i,g_i,\hat{w_i})$ in $Synth_{data}$ <br>
--**End**<br>

---
### KR1 - upper pattern level remplacement

#### Pseudo-Algo
**Input:** 
* a set $Seed_{data}$ containing $n$ entities
* a prefined the number $N$ of synthetic examples that must be generated
* a Knowledge base $\mathcal{K}$ <br>

**Output:** a set $Synth_{data}$ of $N$ generated quadruple $(e_1,e_2,\hat{g_1},\hat{w_1})$ <br>

-- **Begin**<br>
1. Initiliaze the dictionary $Patt_{real}= \\{\\}$
2. Compute the number of realization in $Seed_{data}$ of each patterns: <br>
**For each** $e_i$ in $Seed_{data}$: <br>
├── get the associated graph-text couple $(g_i,t_i)$ associated to $e_i$ in $\mathcal{K}$  <br>
├── define $Patt_i$ as the ordered set of properties described in $g_i$ <br>
├── **If** $Patt_i$ not in $Patt_{real}$ : $Patt_{real}\[Patt_i\]=0$ <br>
└── $Patt_{real}\[Patt_i\]=+1$ <br>
3. Initialise the set of the synthetic example $Synth_{data}$
4. Run the generation:

**While** $|Synth_{data}|$ < $M$: <br>
├── Select a random $Patt_{p1}$ from $Patt_{real}$, the length of this pattern is noted $l_{p1}$ <br>
├── Select a entity $e_i$ related to a graph $g_i$ following $Patt_{p1}$ <br>
├── Select a random $Patt_{p2}$ of length $l_{p1}-1$ listing only properties that could be find in $Patt_{p1}$<br>
├── Select a entity $e_j$ related to a graph $g_j$ following $Patt_{p2}$ <br>
└── **If** $(e_i,e_j)$ do not exist in $Synth_data$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── Create a template $t_j$ from $w_j$ the abstract associated to $e_j$ in $\mathcal{K}$,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; by masking each properties values of $g_j$, the graph associated to $e_j$, in $w_j$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── Fill the template $t_j$ with the data of $g_i$ the graph associated to $e_i$ in $\mathcal{K}$ this new abstract is named $\hat{w_i}$  <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └──  Add $(e_i,e_j,\hat{g_i},\hat{w_i})$ in $Synth_{data}$ <br>
--**End**<br>

## 2. Optimal Sufficient Exposure sampling

### Pseudo-Algo
**Input:** 
* a shape $s^*$ containing $p_n$ properties
* a sufficient exposure threshold defined as $\lambda=1000$
* a Knowledge base $\mathcal{K}$ <br>

**Output:** a sample $D_{SE}$ containing graph-text tuples $(g,t)$ <br>

-- **Begin:**<br>
1. Initialize from the shape ($s*$) a dictionary $P1_{no}$, latter use to compute the number of occurences of each properties $p_i$ of $s*$, as:
   $P1_{no}= \\{(p_1,0),..,(p_i,0),..,(p_n,0) \\}$
2. Compute the number of occurence of each properties in $\mathcal{K}$:<br>
&nbsp;&nbsp;&nbsp; For each $p_i$ of P1_{no}$:<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $$P1_{no}[p_i]= \mathcal{K}(p_i)$$
3. Sort $P_{no}$ from the least to the most represented properties in $\mathcal{K}$
4. Initialize variable $loop_{all}=TRUE$ and $D_{SE}$
5. Initialize from the shape ($s*$) a new dictionary $P2_{no}$, latter use to compute the number of occurences of each properties $p_i$ of $s*$, as:
   $P2_{no}= \\{(p_1,0),..,(p_i,0),..,(p_n,0) \\}$
6. Start the sampling :
&nbsp;| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 
**For each** $p_i$ in $P2_{no}$: <br>
└──  **If** $loop_{all}==TRUE$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └──  **While** $P2_{no}[p_j]$ <= $\lambda$ : <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├──  Select a random text-graph couple $(g,t)$, where $g$ contains $p_i$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └──  **If** $(g,t)$ not in $D_{SE}$ : <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├──  Add $(g,t)$ in $D_{SE}$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├──  **For each** $p_j$ in $g$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  └──  $P2_{no}[p_j]$=+1 <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├──   $all_{saturated}=TRUE$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├──   **For each** $p_k$ in $P2_{no}[p_j]$: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └──  **If** $P2_{no}[p_k]$ < $\lambda$ : $all_{saturated}=FALSE$ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  └──  **If** $all_saturated==TRUE$: $loop_{all}=FALSE$<br>
-- **End**<br>

