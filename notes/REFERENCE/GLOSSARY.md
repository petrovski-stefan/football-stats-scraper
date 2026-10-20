# GLOSSARY — the concepts this project uses

**Group: Reference.** Change it only to correct or extend it. Keep the headings and numbers, because other files cite them.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

**This file explains concepts only.** It has no project results, no code, and no named leagues or matches. The numbers in the examples are invented to show the idea.

**How to use it.** Find the term. Read the first line. Stop if that is enough. The bullets then give why it matters, an example, and how this project uses the concept.

## Start here — five cards that explain most of the project

1. [Comeback](#comeback) — the event that the project tries to predict.
2. [Base rate](#base-rate) — the rate with no selection. Every result is compared with it.
3. [Lift](#lift) — how much better than chance a rule is.
4. [Exploratory and confirmatory](#exploratory-and-confirmatory) — why a good result is not yet a finding.
5. [Spent](#spent) — why old data cannot confirm anything.

## Contents

1. [Football and betting](#1-football-and-betting)
2. [Statistics basics](#2-statistics-basics)
3. [Leakage and validation](#3-leakage-and-validation)
4. [Testing protocol](#4-testing-protocol)
5. [Ledger vocabulary](#5-ledger-vocabulary)

---

## 1. Football and betting

### The targets

#### Comeback

The team that is behind at half-time (HT) wins the match at full-time (FT).

- **Example:** HT 1-0, FT 1-2. The away team was behind at HT and won. That is an away comeback.
- **Not a comeback:** HT 1-0, FT 1-1. The team that was behind must win. A draw is not enough.
- **Why it matters:** It is the main target of the project.

#### 7+

The match has 7 or more goals in total.

- **Example:** FT 4-3 is 7+. FT 4-2 is not.
- **Why it matters:** It is the second target of the project.

#### Pre-match only

Every prediction uses only information that is known before kickoff.

- **Why it matters:** It is the project scope. It is a project decision, not a rule of statistics.
- **Example:** A model that needs the HT score is not a pre-match model. You can use it only inside a pre-match chain, never as a prediction at half-time.
- **Rule:** No in-play markets. No in-play features. No half-time products.

### How a comeback happens

#### HT-decisive

One team leads at half-time. The HT score is not a draw.

- **Example:** HT 1-0 and HT 0-2 are HT-decisive. HT 1-1 is not.
- **Why it matters:** A comeback is not possible without it. It is the first link in the [comeback chain](#the-comeback-chain).

#### Completion rate

Of the matches where a team is behind at HT, the share where that team wins.

- **Example:** In 100 matches, a team is behind at HT. In 10 of them, that team wins. The completion rate is 10%.
- **Why it matters:** It is the second link in the comeback chain.

#### The comeback chain

P(comeback) = P(a team is behind at HT) × P(that team wins).

- **Example:** 60% × 10% = 6%.
- **Why it matters:** It splits one rare event into two common parts. You can study each part with more data.
- **Names in the notes:** "factor 1" is link 1. "Factor 2" is link 2. A "chained pricer" is a model built this way.

#### Comeback environment

A match with all three conditions: HT-decisive, FT-decisive (not a draw at FT), and 3 or more goals.

- **Why it matters:** Every comeback is inside it. A comeback needs at least 3 goals, for example HT 0-1 and FT 2-1.
- **Oracle:** A filter that knows the result. It keeps only environment matches and loses no comebacks. Nobody can build it before kickoff, but it shows the best possible case.
- **Headroom:** The part of the distance from the base rate to the oracle that a real filter covers.

### Odds

#### 1X2 odds

Decimal prices for the three results: home win (1), draw (X), away win (2).

- **Example:** Odds of 2.50 on a home win pay 2.50 for a stake of 1.
- **Opening and closing price:** The first price that the bookmaker shows, and the last price before kickoff.

#### Implied probability

1 ÷ decimal odds. It is the chance that the price shows.

- **Example:** Odds 2.50 → 1 ÷ 2.50 = 40%.
- **Trap:** The sum of the three 1X2 values is more than 100%. The extra part is the [vig](#vig).

#### Vig

The bookmaker's margin: the sum of the implied probabilities, minus 100%. Other names: overround, margin.

- **Example:** Odds 1.90 / 3.60 / 4.20 give 52.6% + 27.8% + 23.8% = 104.2%. The vig is 4.2%.
- **Vig-free:** Divide each value by the sum. The home win becomes 52.6 ÷ 1.042 = 50.5%.
- **Note:** This simple method spreads the vig evenly. Shin's method is a better method for long odds.

#### Favourite–longshot bias

Bets on long odds lose more money than bets on short odds.

- **Why:** The bookmaker puts more of the margin on the long odds.
- **Why it matters:** Comeback bets have long odds. So this project produces calibrated probabilities, not bets.

### Market lines

#### O/U line

The goal line for an over/under bet, for example 2.5 goals.

- **Example:** "Over 2.5" wins if the match has 3 or more goals.
- **Line or price:** Some bookmakers hold both prices near even and move the line. Then the line carries the information, not the price.

#### Asian handicap (AH) line

A goal handicap that the bookmaker gives to one team to make the match equal.

- **Example:** A line of −1.25 on the favourite means the favourite starts 1.25 goals down for the bet.
- **Split line:** A line such as "0/−0.5" is the mean of its two halves: −0.25.
- **Trap:** Sources use different signs for the favourite. Check the sign convention before you compare two sources.

#### The market as the benchmark

The bookmaker's price already contains most public information: form, injuries, lineups.

- **Why it matters:** A feature has value only if it adds information to the price.
- **"Priced":** The market already contains the feature. The feature has no effect when the odds are in the model.
- **In this project:** A candidate is compared with the market price before any outcome test. See the [market-orthogonality screen](#market-orthogonality-screen).

---

## 2. Statistics basics

### Rates

#### Base rate

The rate of an event in all matches, with no selection.

- **Example:** 50 comebacks in 1,000 matches. The base rate is 5%.
- **Why it matters:** You compare every result with the base rate of the same matches.
- **Trap:** A base rate from a small sample can be wrong. Use the largest sample that you have.

#### Hit rate

The share of selected matches that have the event. Other name: precision.

- **Example:** A rule selects 200 matches. 16 have a comeback. The hit rate is 8%.

#### Lift

Lift is the hit rate in a selection divided by the base rate.

- **Example:** Hit rate 8%, base rate 5%. Lift = 8 ÷ 5 = 1.6×.
- **Why it matters:** Lift shows if a rule finds more comebacks than chance. 1.00× is chance.
- **In this project:** A pass needs a minimum lift, fixed before the test.

### Uncertainty

#### Confidence interval (CI)

A range that probably contains the true value. A 95% CI contains it in about 95 of 100 repeated studies.

- **Example:** 6 comebacks in 100 matches is 6%. The 95% CI is about [2.8%, 12.5%]. A base rate of 5% is inside, so the result shows nothing.
- **Why it matters:** A small sample gives a wide range.

#### Wilson CI and lower bound

A method for a CI on a rate. It stays correct when counts are small or the rate is near 0%.

- **Lower bound (LB):** The low end of the range. If the LB is above the base rate, the true rate is probably above it too.
- **In this project:** A pass needs the Wilson LB above the base rate.

#### p-value

The probability of a result this strong, or stronger, if no real effect exists.

- **Example:** p = 0.03 means that chance alone gives a result this strong about 3 times in 100.
- **Trap:** Many tests make small p-values by chance. See [multiple testing](#multiple-testing).
- **Rule:** Correct the p-values for the number of tests. See [Holm correction](#holm-correction).

#### Null

The null hypothesis is the assumption that no real effect exists. A null result is a test that did not show an effect.

- **Why it matters:** A null result from a test with low [power](#power) does not show that the effect is absent.

#### Power

The probability that a test finds a real effect of a stated size. The usual standard is 80%.

- **Why it matters:** Power tells you how many matches a test needs before you start.
- **Trap:** A test with low power often fails when the effect is real.

#### Rare-event trap

With a rare event, small samples often show zero hits by chance alone.

- **Example:** With a 5% event, the chance to see zero in 20 matches is about 0.36. In 40 matches, it is about 0.13.
- **Why it matters:** "I never saw one" is normal for a rare event. It is not evidence.
- **Rule:** Before a claim, calculate the count that the base rate expects. Do not form a belief from a few positive cases.

### Scores for a rule

#### Slate (top-N)

The set of matches that a rule selects: the N matches with the highest scores.

- **Rule:** Fix N before the test. A slate size chosen after the results is not a test.
- **Fact:** Equal scores can make a slate a little larger than N.

#### Precision@top-N

The hit rate in the top-N slate.

- **Why it matters:** The goal is a small set of good candidates, not a good score over all matches.
- **In this project:** It is the main metric for a candidate rule. It is reported with the Wilson CI and the lift.

#### AUC

The probability that a model ranks a random positive match above a random negative match. 0.5 is chance. 1.0 is perfect.

- **Trap:** AUC measures the ranking of all matches. A rule can be very good on a small slate and still have an AUC near 0.5.
- **In this project:** AUC does not judge a candidate rule. It can rank one condition over all matches.

#### Brier score

The mean of (predicted probability − result)², where the result is 1 or 0. A lower score is better.

- **Example:** You predict 10%. The event does not occur: (0.10 − 0)² = 0.01. The event occurs: (0.10 − 1)² = 0.81.
- **Trap:** For a rare event, a good model and a constant guess get almost the same Brier score.
- **In this project:** It is not the verdict for a candidate rule. Log-loss is a similar score with the same limit.

---

## 3. Leakage and validation

### Leakage

#### Leakage

A feature uses information that was not known at prediction time. The result is a number that is confident and wrong.

- **Example:** A "recent goals" feature that includes the goals of the match that it predicts.
- **Why it matters:** It is the main failure mode of this project. Leaky code passes every lint and type check.
- **Four common traps:**
  1. Odds collected after the match.
  2. Standings from after the round.
  3. Shuffled cross-validation.
  4. Web information that you cannot rebuild for past matches.

#### Post-match column

A column that is known only after the match. It is a label, never a feature.

- **Examples:** The HT score, the FT score, and the comeback flag of the match itself.
- **Leak check:** Set every post-match column to empty. Build the features again. The output must not change.

#### As-of-round

A feature for round k uses only data from the rounds before k.

- **Example:** The standings for round 10 come from the table after round 9.
- **Trap:** A check that compares rolling features across rounds does not find a leak from the same row.

#### Ordering check

For an event-based claim, check if the event came before or after the goals that it "explains".

- **Example:** A red card seems to cause comebacks. But if the red card came after the equaliser, the comeback caused the red card.
- **Why it matters:** An event comes after the score change as often as before it.
- **Rule:** Every event-based claim needs this check against the goal timeline.

### Honest evaluation

#### Walk-forward

Train on the past. Predict the next block. Move forward one block. Do it again.

- **Why it matters:** It copies real use: you always predict the future from the past.
- **Rule:** Never use shuffled cross-validation. A random split puts future form into the training data.

#### Burn-in

The first rounds of a season are removed, because rolling form does not exist yet.

- **Trap:** Calculate test sizes and bars after the burn-in, not before.

#### Leave-one-league-out (LOLO)

Build the rule on all leagues but one. Test it on the league that you left out. Do this for each league.

- **Why it matters:** It tests if a rule works in a league that it has not seen.
- **In this project:** A claim that passes the other tests but fails LOLO is an artifact of the data.

### Leagues in one test

#### Mantel–Haenszel (MH)

A method that combines an effect across strata into one test. Here, a stratum is a league-season.

- **Why it matters:** Leagues have different base rates. A plain pooled test mixes them and pushes the effect toward zero.
- **Odds ratio (OR):** The effect size that MH combines. 1.0 means no effect. Above 1.0 means more comebacks.
- **Rule:** Stratify by league. Never test per league.

#### Per-league testing

A separate test in each league. This project does not use it.

- **Why:** It multiplies the number of tests. It also makes each test small, so only a very large effect can pass.

### Free screens before an outcome test

#### Outcome-free screen

A check that reads no outcome column. So it costs nothing from the test budget, and nobody can tune it to the results.

- **The two screens:** the [reliability screen](#reliability-screen) and the [market-orthogonality screen](#market-orthogonality-screen).
- **Rule:** Run them before any outcome test.

#### Reliability screen

It measures if a feature is a stable team trait, at the depth that the feature really has.

- **Method:** Split each team's matches into odd and even. Calculate the trait on each half. Correlate the halves across teams ([split-half](#split-half-reliability)). Then convert the value to the real depth ([Spearman–Brown](#spearmanbrown)).
- **Rule:** Kill the feature if the value at the real depth is below a minimum fixed before the screen.
- **Why it matters:** A trait that is not stable is noise. No good idea behind it can change that.

#### Split-half reliability

The correlation of a trait between two halves of each team's matches.

- **Example:** Teams with many yellow cards in odd matches also have many in even matches. The split-half value is high.
- **Trap:** This is the raw value, not the screen value. The screen uses the value at the real depth.

#### Spearman–Brown

A formula that converts a reliability value from one number of matches to a different number.

- **Why it matters:** A feature can read only a few past matches. A trait can be stable over 20 matches and noise over 6.
- **Formulas:** r_full = 2r / (1 + r). Then r1 = r_full / (k − (k − 1) · r_full), with k = matches per team. Then r6 = 6 · r1 / (1 + 5 · r1). A value below 0 becomes 0.
- **Example:** Split-half 0.50, 38 matches per team: 0.67 at 38 matches → 0.05 at 1 match → 0.24 at 6 matches.
- **Effect:** A feature with reliability r loses signal by the factor √r. At r = 0.25, it keeps only half of its signal.

#### Market-orthogonality screen

Correlate the candidate's score with the market price before any outcome test.

- **Why it matters:** A rule with no link to the market has no link to the best known signal.
- **Rule:** Kill the candidate below a low bar (no signal). Kill it above a high bar (the market already has it). Pass between the two bars.

---

## 4. Testing protocol

### The core idea

#### Exploratory and confirmatory

An exploratory result comes from a search of the data. A confirmatory result comes from a test that was written before the data existed and was run once.

- **Why it matters:** A search finds chance patterns. Only a confirmatory test can show that a pattern is real.

#### Preregistration

A written test plan, committed before the test. It fixes the hypothesis, the family, the metric, the pass bar, the data, and the one run.

- **Why it matters:** After the plan is fixed, nobody can change the test to fit the result.

#### Amendment

A dated change to a preregistration. It goes at the end of the log. The old text stays as it is.

- **Why it matters:** A silent edit after the results changes the test after you saw the result.
- **Erratum:** A dated amendment that corrects a number. It wins over the old number.

#### Pass bar

The result that a test must reach. You fix it before the test.

- **The four conditions in this project.** A pass needs all four:
  1. A Holm-corrected p-value below the significance level.
  2. A Wilson LB above the base rate.
  3. A minimum lift, at a slate size fixed before the test.
  4. The same sign in leave-one-league-out.
- **Rule:** Three of four is a null result with a note. It is not a finding.

#### Candidate protocol

The four gates for every new rule or feature. Stop at the first failure.

1. **a — Graveyard check:** Is it a Dead claim with new words?
2. **b — Reliability screen:** for features built from team history only.
3. **c — Market-orthogonality screen.**
4. **d — Outcome test:** precision@top-N, Wilson CI, lift, MH strata.

### Too many tests

#### Multiple testing

If you do many tests, some pass by chance alone.

- **Example:** You do 20 tests of rules with no real effect, at the 5% level. You expect about 1 false pass. The chance of at least one is about 64%.
- **Other names:** multiplicity, forking paths. P-hacking is when you pick the best cut and report only that cut.
- **Rule:** Count every test. Correct for the count. See [Holm correction](#holm-correction).

#### Holm correction

A method that makes p-values stricter for the number of tests in a family.

- **How:** Sort the m p-values, smallest first. Multiply the smallest by m, the next by m − 1, and continue. Each corrected value is at least as large as the value before it.
- **Example:** Three tests: p = 0.01, 0.03, 0.04. Corrected: 0.03, 0.06, 0.06. At the 5% level, only the first passes.

#### Family

The closed list of claims that one Holm correction covers. Holm's m is the size of the family.

- **Rule:** The list is closed. A new claim needs a dated amendment before the confirmatory data exists.
- **Why:** Each added claim makes the correction stricter for all claims.

#### Winner's curse

The best of many results looks better than it really is.

- **Example:** 20 leagues have the same true comeback rate. By chance, one of them shows a high rate. If you select that league and test it on the same data, it "passes".
- **Rule:** Do not select leagues, teams or rules by their results and then test them on the same data.

### Holdout and confirmatory set

#### Holdout

Data that nobody examines until the one final test.

- **Why it matters:** It is the only protection against results that come from repeated searches.

#### Look

Any analysis that reads the outcome columns of a data set. The purpose of the analysis does not matter.

- **Why it matters:** Each look decreases the value of the holdout. After enough looks, the holdout is [spent](#spent).
- **Rule:** Record each look. A run that reads outcomes saves its raw output as a [run record](#run-record).

#### Spent

A data set whose outcomes informed earlier analyses. It cannot confirm anything.

- **Why it matters:** A test on spent data tests an idea that the same data helped to make.
- **Rule:** Never run the final test on spent data.

#### One opening

The confirmatory test runs once. Its raw output is saved and committed.

- **Why it matters:** A second run is a second look.
- **Rule:** If the raw output is lost, do not run the test again to recover it.

#### Confirmatory set

The data for the next real test. It is data first collected after its plan was declared, and never stored before.

- **Rule:** Declare the league list and the collection date in a dated amendment. Commit it before the collection starts.
- **Trap:** Data collected without that amendment is dev data. It is not confirmatory.

#### Eligibility

A league-season can join the confirmatory set only if none of its matches is already stored.

- **"Stored" means:** in a league file, in the event store, or in the history block of any stored match.
- **Rule:** One stored match disqualifies the whole league-season.
- **Why:** The stored matches are not a random part. A team's history chose them.

#### Dev data

Data that you can explore freely. Every result from it is exploratory.

- **Example:** Any league-season that was stored before the confirmatory plan.

---

## 5. Ledger vocabulary

### The ledger

#### STATE ledger

The ledger is one table with one row per claim: status, key number, n, and source. n is the number of matches or cases behind the key number.

- **Rule 1:** If the ledger and its source note disagree, the source note is correct.
- **Rule 2:** When a study ends, update the ledger in the same commit.
- **Also in the ledger:** the open leads (what to do next), and the conflicts that are listed but not resolved.

#### Statuses for results

- **Dead:** tested, and it failed. Two variants: *Dead (priced)* means the market already has it. *Dead (reliability screen)* means the screen killed it before an outcome test.
- **Live-exploratory:** positive, but not preregistered.
- **Live-preregistered:** passed a preregistered bar.

#### Statuses for open claims

- **Reopened:** once Dead, now not resolved.
- **On-retry-list:** in the closed retry list, not yet tested on the new data.
- **Untested:** never tested.

#### Graveyard

All Dead claims, plus the claims that the retry list marks "do not retry".

- **Why it matters:** Most "new" ideas are already in it.
- **Rule:** A candidate that measures the same thing as a Dead claim stops at the graveyard check. New words, new weights or a new window do not change this.

#### Note-only

A ledger row with no committed raw output. Only the note records the number.

- **Why it matters:** Nobody can check a note-only number against its run.

#### Run record

The saved raw output of a run that reads outcomes. Commit it in the same commit as the note that reports it.

- **Why it matters:** It lets anybody check a reported number against the run that made it.

### The numbered items

#### F-numbers

An F-number (F1 to F13) names one finding of an old league study. The project dropped that study on 2026-10-13.

- **Why it matters:** Older notes still cite findings by these numbers.

#### Retry list

The closed list of claims to test again on new data. Its tiers:

- **Tier 1:** do not retry. These claims failed with enough power.
- **Tier 2:** more data can help.
- **Tier 3:** never tested.

#### Claim numbers

A claim number names one claim on the retry list. Some claims carry a condition, for example a stratum that the test must exclude.

#### A-numbers

An A-number names one amendment in the preregistration log.

- **Why it matters:** A later amendment can correct an earlier one. Read the whole log, not only the first plan.

#### D-numbers

A D-number names one open decision that needs the owner.

- **Rule:** Each decision keeps its current value until the owner decides it.
