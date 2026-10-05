# Reference-Choice Robustness (RCR): Method & Mathematical Formulation

## 1. Mathematical Formalization

For an executable reasoning task \(x\), let \(V(x)\) be the complete valid-solution space containing all executable trajectories \(y\) that satisfy formal task rules and constraints:

$$V(x) = \{ y \mid \text{RulesCheck}(x, y) = \text{TRUE} \land \text{ConstraintsCheck}(x, y) = \text{TRUE} \}$$

In standard benchmark construction, a single reference trajectory \(R^* \in V(x)\) is arbitrarily selected as the "gold standard" reference. Model predictions \(y\) are evaluated using an evaluator \(E(y \mid R^*)\).

We define **Reference-Choice Robustness (RCR)** by analyzing the sensitivity of benchmark conclusions \(C_E(R)\) as \(R\) varies over the complete valid space \(V(x)\).

## 2. Benchmark Conclusion \(C_E(R)\)

For a reference choice vector \(\mathbf{R} = (R_1, R_2, \dots, R_N) \in \prod_{k=1}^N V(x_k)\), the benchmark conclusion \(C_E(\mathbf{R})\) includes:
1. **Model Scores**: \(S_m(\mathbf{R}) = \frac{1}{N} \sum_{k=1}^N E(y_{m,k} \mid R_k)\)
2. **Model Ranking**: \(\text{Rank}_E(\mathbf{R}) = \text{argsort}_m(-S_m(\mathbf{R}))\)
3. **Pairwise Winner Decisions**: \(\text{Winner}_{A,B}(\mathbf{R}) = \text{sign}(S_A(\mathbf{R}) - S_B(\mathbf{R}))\)
4. **Statistical Significance Decisions**: \(D_{A,B}(\mathbf{R}) \in \{ \text{SIG\_A\_WINS}, \text{SIG\_B\_WINS}, \text{NON\_SIGNIFICANT} \}\)

## 3. Metrics

### Kendall \(\tau\) Stability
$$\tau_{\text{mean}} = \mathbb{E}_{\mathbf{R} \sim \mathcal{U}(\prod V(x))} \left[ \tau\left(\text{Rank}_E(\mathbf{R}), \text{Rank}_E(\mathbf{R}_{\text{canonical}})\right) \right]$$

### Pairwise Winner Reversal Probability
$$P(\text{Reversal}) = \mathbb{P}_{\mathbf{R}_1, \mathbf{R}_2} \left[ \text{Winner}_{A,B}(\mathbf{R}_1) \neq \text{Winner}_{A,B}(\mathbf{R}_2) \right]$$

### Oracle Recovery Rate \(RCR(E)\)
$$RCR(E) = \mathbb{P}_{\mathbf{R}} \left[ \text{Rank}_E(\mathbf{R}) == \text{Rank}_{\text{oracle}} \right]$$
where \(\text{Rank}_{\text{oracle}}\) is the reference-invariant ranking computed by the executable semantic oracle \(E_3(y, x)\).
