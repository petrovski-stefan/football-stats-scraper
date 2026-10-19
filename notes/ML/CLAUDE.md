# notes/ML/ — results of ML methods run on the corpus

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

The rule of this group: Claude writes a doc from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it.

A doc runs again only when the corpus changes (a league is added or removed) or its method changes. The rules for every note are in `notes/CLAUDE.md`.

## 1. What goes here

- One doc for each ML method, run on one scope of the data. The numbers come from a runner of the `ml/` package (`ml/CLAUDE.md`).
- ML is a method with a fitted predictive model whose settings are tuned on the data (the user, 2026-10-16). Other methods go to `notes/ANALYSIS/`.
- The tree, the doc template, the workflow and the honesty rules are those of `notes/ANALYSIS/CLAUDE.md` §2–5. This file gives only the differences.

## 2. The differences

1. **A claim compares out of sample.** It compares a model with model A, the odds alone, on the season cohort that the model did not see. A gain inside the training rows is not a claim.
2. **The header names the models, the split and the score.**
3. **A SHAP value tells which fields a model reads.** It does not tell that a field causes comebacks. A field with a large SHAP value, in a model that does not beat model A, is not a finding.
4. **Looks:** count each model, each split and each N.
5. **The kind is empirical.**
