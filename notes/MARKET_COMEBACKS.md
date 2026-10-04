# MARKET_COMEBACKS — the comeback market, explained

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

**This file explains concepts only.** It has no project results, no code, and no named leagues or matches.

**No number in this file comes from scraped data.** Every number is calculated from invented inputs: the rates of one invented [example match](#the-example-match), other invented rate settings, invented odds, and an invented season. Two independent calculations gave the same numbers.

**How to use it.** Before you measure a fact about comebacks, find the fact here. Every card has a **Kind** line, and every structural card has a **Basis** line. Measure only the empirical facts. [Section 6](#6-all-facts-by-kind) lists the facts by kind.

**Notation.** P(A) is the probability of A. P(A | B) is the probability of A, given B.

## Start here — three kinds of fact

Every fact about comebacks is one of three kinds.

| kind | it follows from | what to do |
|---|---|---|
| **Definitional** | the settlement rule, or arithmetic | Never measure it. Never report it as a finding. |
| **Structural** | the goal model | Derive it once, in this file. Data can show only how well the model fits. |
| **Empirical** | data only | Measure it. A confirmatory claim needs a preregistration. |

**Test for the kind.** Ask these questions in this order. Stop at the first "yes".

1. Does it follow from the settlement rule or from arithmetic alone? Then it is definitional.
2. Does it follow from the goal model? Then it is structural.
3. Does it need data? Then it is empirical.

**Trap:** Data that agrees with a structural fact does not make the fact a finding. The data shows only that the model fits.

### How a structural fact is known

Every structural card gives its basis. There are three bases:

| basis | what it means |
|---|---|
| **Proof** | True for every setting of the basic goal model. The card gives the proof, or names the rule that the proof uses. |
| **Grid check** | Calculated for a stated set of invented settings. True for those settings only, not for every possible setting. |
| **Example** | Calculated for the stated example or examples only. |

[Section 6](#6-all-facts-by-kind) also lists the basic goal model itself. Its basis is *assumption*: every proof, grid check and example rests on it.

**Rule:** Never quote a grid check or an example as a proof. A summary of a grid check starts with "In the checked settings". A summary of an example names the example.

### Not a fact about comebacks: statistical design

[Section 4](#4-why-comebacks-are-hard-to-measure) holds calculations about tests: sample sizes and counts by chance. They follow from the test and its assumptions, not from football. Their kind is *statistical design*. Calculate them. Never measure them.

## Contents

1. [The bet](#1-the-bet)
2. [The probability](#2-the-probability)
3. [The price](#3-the-price)
4. [Why comebacks are hard to measure](#4-why-comebacks-are-hard-to-measure)
5. [Open questions](#5-open-questions)
6. [All facts by kind](#6-all-facts-by-kind)

---

## 1. The bet

### The settlement rule

#### Comeback

The team that is behind at half-time (HT) wins the match at full-time (FT).

- **Kind:** definitional. This is the settlement rule. All other facts in this section follow from it.
- **Example:** HT 0-1, FT 2-1. The home team was behind at HT and won. That is a home comeback.
- **Not a comeback:** HT 0-1, FT 1-1. The team that was behind must win. A draw is not enough.
- **Not a comeback:** HT 1-1, FT 2-1. No team was behind at HT.
- **Names in this file:**
  - The *trailing team* is the team that is behind at HT.
  - The *leading team* is the other team.
  - The *deficit* is the number of goals that the trailing team is behind at HT.
  - The *completion rate* is P(the trailing team wins | a team is behind at HT). It is an average over all HT scores where a team is behind.
  - The *completion from an HT score* is P(the trailing team wins | that HT score). It depends on which team is behind, and on the deficit. See [Completion in the basic model](#completion-in-the-basic-model).

#### HT/FT notation

A comeback bet is a selection in the HT/FT market. A selection has the form "HT result / FT result".

- **Kind:** definitional.
- **The codes:** 1 is a home lead or a home win. X is a draw. 2 is an away lead or an away win.
- **2/1:** The away team leads at HT. The home team wins at FT. This is a home comeback.
- **1/2:** The home team leads at HT. The away team wins at FT. This is an away comeback.
- **Trap:** The second code shows the team that wins. In 2/1, the comeback is by the home team.

#### A comeback by either team

"A comeback in this match" is not one bet. It is two selections: 2/1 and 1/2.

- **Kind:** definitional.
- **Formula:** P(comeback) = P(2/1) + P(1/2).
- **Why you can add them:** Only one team can be behind at HT. So the two selections cannot both win.
- **Example:** P(2/1) = 2.48% and P(1/2) = 1.55%. So P(comeback) = 4.03%.
- **To bet on both:** See [Two selections as one bet](#two-selections-as-one-bet).

#### What the bet counts

The bet uses the official score at HT and at FT.

- **Kind:** definitional.
- **HT score:** It includes the added time of the first half.
- **FT score:** It is the score after normal time and its added time. Extra time and penalties do not count.
- **Own goals:** An own goal counts for the team that the scoreboard gives it to.
- **Cancelled goals:** A goal that the referee cancels does not count.

#### Abandoned and awarded matches

A match that stops early, or that an authority awards, needs a special rule.

- **Kind:** a rule, not a fact.
- **For a bet:** Each bookmaker has its own rule for these matches. Often the bet is void. Read the rule before you bet.
- **For data:** An awarded score (for example 3-0) does not show what happened on the field. Remove these matches before you calculate a rate.

#### Not "win from behind"

Some bookmakers sell a "win from behind" bet. It counts a deficit at any minute, not only at HT.

- **Kind:** definitional.
- **Example:** The home team is behind 0-1 after 20 minutes. It is 1-1 at HT, and the home team wins 2-1. "Win from behind" wins. The 2/1 bet loses, because the HT result is X.
- **This file covers only 2/1 and 1/2.**

### What the rule makes true in every comeback

#### Minimum goals

A comeback needs 3 goals or more.

- **Kind:** definitional. Do not measure it.
- **Why:** The trailing team must remove the deficit and then score one more goal. The smallest case is HT 0-1, FT 2-1.
- **General rule:** With a deficit of d goals, the trailing team must win the second half by d + 1 goals or more. So the match has 2d + 1 goals or more.
- **Example:** A deficit of 2 (HT 0-2) needs a second half of 3-0 or better. So the match has 5 goals or more.

#### Goals in each half

In every comeback, these four facts are true:

1. The first half has 1 goal or more. A draw at HT, 0-0 included, makes a comeback impossible.
2. The second half has 2 goals or more.
3. The trailing team scores 2 goals or more in the second half.
4. The trailing team wins the second half by 2 goals or more.

- **Kind:** definitional.

#### The final score

A comeback can end only at a score where the winner has 2 goals or more and the loser has 1 goal or more.

- **Kind:** definitional.
- **Why:** The loser led at HT, so it scored. The winner was behind and then won, so it scored 2 goals or more.
- **Possible:** 2-1, 3-1, 3-2, 4-1.
- **Not possible:** 1-0, 2-0, 3-0, and every draw.
- **So:** Both teams score in every comeback. Every comeback has more than 2.5 goals.

#### Odd and even goal totals

The final goal margin is odd when the goal total is odd. It is even when the goal total is even.

- **Kind:** definitional. It is arithmetic: the total and the margin differ by 2 × the loser's goals.
- **So:** An odd total can never end in a draw. An even total can never end with a one-goal margin.
- **Effect on comebacks:** The comeback rate by final goal total goes up and down between odd and even totals. See [Comeback rate by final goal total](#comeback-rate-by-final-goal-total).

#### The comeback environment

The comeback environment is the set of matches with three conditions: a decisive HT score, a decisive FT score, and 3 goals or more. (Decisive: not a draw.)

- **Kind:** definitional.
- **Why it matters:** Every comeback is inside the environment.
- **Trap:** A match in the environment is not always a comeback. Example: HT 1-0, FT 3-0.
- **Upper limit:** P(comeback) is never more than P(environment).

#### Filters that remove impossible matches

A filter that removes matches with fewer than 3 goals loses no comebacks.

- **Kind:** definitional. This is also true for a filter that removes matches with a draw at HT or at FT.
- **Trap:** This is not a finding. The filter uses the result, so nobody can use it before kickoff.
- **Oracle:** A filter that uses the result is an *oracle*. It shows the best possible case, not a rule that you can use.
- **The real question:** Can you predict before kickoff which matches will have fewer than 3 goals? That question is empirical. A filter is only as good as that prediction.
- **Headroom:** The part of the distance from the base rate to the oracle that a real filter covers.

---

## 2. The probability

### The chain

#### The two links

```
P(comeback) = P(a team is behind at HT) × P(the trailing team wins | a team is behind at HT)
```

- **Kind:** definitional. It is an identity of probability: P(C) = P(B) × P(C | B). Here B is "a team is behind at HT" and C is "comeback". It is true because every comeback is inside B.
- **Link 1:** P(B), the chance that a team is behind at HT.
- **Link 2:** P(C | B), the [completion rate](#comeback).
- **Example:** 55.95% × 7.20% = 4.03%.
- **Why it matters:** It splits one rare event into two common parts. Each part has much more data than the comeback itself.

#### The full form

The full form adds one term for each HT score where the home team is behind:

```
P(2/1) = Σ over HT scores h-a with h < a of
         P(HT score is h-a) × P(home team wins | HT score is h-a)
```

- **Kind:** definitional. It is the same identity, in more detail.
- **P(1/2):** It has the same form, over the HT scores with h > a, where the away team wins.
- **Why it matters:** The completion from an HT score changes much with the deficit and with the team that is behind. One average completion rate hides that.

#### Pre-match use

The completion rate describes the match after HT. This project uses it only inside a pre-match calculation.

- **Kind:** a project rule, not a fact.
- **Method:** Before kickoff, calculate P(HT score) for each HT score. Multiply each value by its completion from that HT score. Add the results. The sum is a pre-match probability.
- **Rule:** Do not bet at HT. Do not use in-play markets. This is a project decision, not a rule of statistics.

### The goal model

#### The basic goal model

Each team scores at a constant rate in each half. The four goal counts are independent.

- **Kind:** an assumption. Every structural fact in this file is true under this model.
- **The four rates:** home first half (λ₁), away first half (μ₁), home second half (λ₂), away second half (μ₂). A rate is the expected number of goals.
- **The distribution:** The goals of one team in one half have a Poisson distribution: P(k goals) = e^(−λ) × λ^k ÷ k!
- **What it does not include:** The second half does not depend on the HT score. Red cards, substitutions and tactics have no effect. See [What the basic model does not include](#what-the-basic-model-does-not-include).

#### Completion in the basic model

In the basic model, the completion from an HT score depends only on the deficit and on the second-half rates.

- **Kind:** structural.
- **Basis:** proof. From HT h-a with h < a, the home team must win the second half by a − h + 1 goals or more. In the model, the second half does not depend on the HT score. So only the deficit (a − h) and the second-half rates λ₂ and μ₂ count.
- **So:** HT 0-1 and HT 2-3 give the home team the same chance.
- **Who is behind counts:** The trailing team's second-half rate is in the formula. So from the same deficit, the home team and the away team can have very different chances. See [Worked example: all paths](#worked-example-all-paths).

#### The mirror rule

For two independent Poisson counts X and Y with means λ and μ, a win by k goals is (λ/μ)^k times as likely as a loss by k goals:

```
P(X − Y = k) = (λ/μ)^k × P(X − Y = −k)    for every k ≥ 1
```

- **Kind:** structural.
- **Basis:** proof. Write each side as a sum over the goals of the count that loses. Each term on the left is (λ/μ)^k times the matching term on the right.
- **So:** If λ > μ, every win by k goals is more likely than the loss by k goals. So, under the basic model, the team with more expected goals has the higher chance to win. A team's goals in the match are the sum of its goals in the two halves, so they also have a Poisson distribution.
- **Use in this file:** The proofs about the favourite use this rule.

#### The example match

The example match in this file has these invented rates:

| expected goals | first half | second half | match |
|---|---|---|---|
| home | 0.6 | 0.8 | 1.4 |
| away | 0.5 | 0.6 | 1.1 |
| both teams | 1.1 | 1.4 | 2.5 |

- **Kind:** invented input.
- 44% of the expected goals come in the first half.
- **Favourite:** In this file, the *favourite* is the team with more expected goals in the match. Here, that is the home team: 1.4 against 1.1. Under the basic model, by [the mirror rule](#the-mirror-rule), the favourite also has the higher chance to win.
- **Market favourite:** The *market favourite* is the team with the shorter win odds. If the model fits the market, the favourite and the market favourite are the same team.
- **Advantage:** The *advantage* is the favourite's rate divided by the other team's rate, in one half. Here it is 1.2 in the first half (0.6 ÷ 0.5) and 1.33 in the second half (0.8 ÷ 0.6).

#### Worked example: one path

Take one HT score: 0-1. The home team is behind by 1.

1. P(HT 0-1) = P(home scores 0) × P(away scores 1) = e^−0.6 × 0.5 × e^−0.5 = 0.5488 × 0.3033 = **16.64%**.
2. From 0-1, the home team must win the second half by 2 goals or more. Add one term for each number y of away goals in the second half:
   ```
   P = Σ over y of P(away scores y) × P(home scores y + 2 or more)
     = 0.5488 × 0.1912 + 0.3293 × 0.0474 + 0.0988 × 0.0091 + …
     = 12.15%
   ```
3. This path adds 16.64% × 12.15% = **2.02%** to P(2/1).

- **Kind:** structural.
- **Basis:** example.
- **Next:** Do the same for every HT score where the home team is behind. The sum is P(2/1).

#### Worked example: all paths

In the basic model, the completion from an HT score depends only on the deficit and on which team is behind. (The second-half rates are fixed for one match.) So the paths group by team and by deficit:

| deficit at HT | home behind | home then wins | adds to 2/1 | away behind | away then wins | adds to 1/2 |
|---|---|---|---|---|---|---|
| 1 | 19.27% | 12.15% | 2.34% | 23.12% | 6.36% | 1.47% |
| 2 | 4.59% | 2.92% | 0.13% | 6.61% | 1.17% | 0.08% |
| 3 | 0.75% | 0.55% | <0.01% | 1.29% | 0.17% | <0.01% |
| all | 24.71% | 10.03% | **2.48%** | 31.24% | 4.96% | **1.55%** |

- **Kind:** structural.
- **Basis:** example.
- **Who is behind counts:** From a deficit of 1, the home team wins in 12.15% of cases. The away team wins in only 6.36%. The home team has the higher second-half rate.
- **Either team:** 2.48% + 1.55% = 4.03%.
- **The two links:** A team is behind at HT in 55.95% of cases. The completion rate is 4.03% ÷ 55.95% = 7.20%.
- **HT draw:** 44.05%. No comeback is possible in these matches.

### What the model says

#### Deficit size

The completion from an HT score always falls as the deficit grows. How fast it falls depends on the second-half rates.

- **Kind:** structural.
- **Basis:** proof for "always falls": every second-half result that wins from a deficit of d + 1 also wins from a deficit of d, and some results win only from d. Example, and a grid check over 5 settings, for "how fast": second-half totals 0.7, 1.4, 2.1, 2.8 and 4.2 expected goals, home share 57%.
- **Example:** In the example match, the home team wins from a deficit of 1 in 12.15% of cases, from 2 in 2.92%, and from 3 in 0.55%. Each step is a factor of about 4 to 5.
- **In the checked settings, more second-half goals give a slower fall:** The factor from a deficit of 1 to a deficit of 2 is about 8 with 0.7 expected second-half goals, and about 2 with 4.2.
- **Effect:** In the example match, about 94% of comebacks start from a deficit of 1.

#### Expected goals

In the example match, growing all four rates by the same factor gives more comebacks, at least up to 40 expected goals. But when one team has the higher rate in both halves, the chance cannot increase for ever.

- **Kind:** structural.
- **Basis:** example for the table. Proof for "cannot increase for ever". Two more examples for where the chance is highest.
- **Example:** Multiply all four rates of the example match by the same number:

| expected goals | 1.5 | 2.0 | 2.5 | 3.0 | 3.5 | 4.0 |
|---|---|---|---|---|---|---|
| P(comeback) | 1.71% | 2.85% | 4.03% | 5.15% | 6.18% | 7.12% |

- **Why:** More first-half goals give fewer HT draws. More second-half goals give the trailing team more chances.
- **Size:** In this example, each extra 0.5 expected goals adds about 1 percentage point. The chance is still increasing at 40 expected goals (18.43%).
- **Proof that it cannot increase for ever:** Take a favourite with the higher rate in both halves. Grow all four rates without limit. In each half, the mean goal difference then grows faster than its spread. So the favourite is almost never behind at HT, and the underdog almost never wins the second half (Chebyshev's inequality). Every comeback needs one of these two events. So the comeback chance goes to 0. A chance that is more than 0 and goes to 0 cannot increase at every step.
- **Where the chance is highest (examples):** With 44% of the goals in the first half:
  - favourite's share 70%: at about 10 expected goals (8.30%);
  - favourite's share 90%: at about 5 expected goals (2.17%).
  - In these two examples, the more one-sided match has its highest point at a lower total.
- **Trap:** More expected goals do not always give more comebacks. The result also depends on where the extra goals go:
  - **Only to the first half:** The chance increases, then it decreases. Example, with 1.4 second-half goals: 4.16% at 2.0 first-half goals, about 3.3% at 5.0.
  - **Only to one team:** The chance increases, then it decreases. Example: the home rates of the example match × 2 give 5.63%, × 3 give about 5.3%.
  - **Only to the second half:** In this example, the chance increases. With 1.1 first-half goals: 3.98% at 1.4 second-half goals, about 10.3% at 4.0.
- **Why it matters:** The goal-line market gives information about the expected total. So a probability built from the market odds already includes this effect.

#### First half and second half

For a fixed total rate and fixed team shares, the comeback chance is highest at a first-half share between 0% and 100%.

- **Kind:** structural.
- **Basis:** proof. The comeback chance is continuous on the closed range 0% to 100%. A continuous function on a closed range always has a highest value (the extreme value theorem). At 0% and at 100%, the chance is 0, because one half has no goals. At every share between the two ends, the chance is more than 0. So every highest value is at a share between the two ends.
- **Example:** 2.5 expected goals. The home team has 56% of the expected goals in each half. Change only the first-half share:

| first-half share of the goals | 20% | 30% | 40% | 50% | 60% | 70% |
|---|---|---|---|---|---|---|
| P(comeback) | 4.17% | 4.50% | 4.21% | 3.55% | 2.69% | 1.77% |

- **Why:** A comeback needs at least 1 goal before HT and at least 2 goals after HT.
- **Where it is:** In this example, near 30%. Its place depends on the rates.

#### Favourite and underdog

A favourite with the higher rate in both halves is behind at HT less often. When it is behind, it wins more often.

- **Kind:** structural.
- **Basis:** proof, in two parts. Both parts use [the mirror rule](#the-mirror-rule):
  1. **Behind less often:** Apply the rule to the first half.
  2. **Wins more often when behind:** From each deficit, the favourite wins more often: apply the rule to the second half. Also, when the favourite is behind, its deficit is more often small: apply the rule to the first half. A small deficit is easier to remove.
- **Example:** 2.5 expected goals, 44% in the first half. Change only the home team's share of the expected goals. The share is the same in both halves:

| home share of the goals | 50% | 60% | 70% | 80% |
|---|---|---|---|---|
| home behind at HT | 27.93% | 20.99% | 14.64% | 8.98% |
| home then wins | 7.23% | 11.49% | 16.99% | 23.76% |
| P(2/1): comeback by the favourite | 2.02% | 2.41% | 2.49% | 2.13% |
| P(1/2): comeback by the underdog | 2.02% | 1.46% | 0.87% | 0.39% |
| P(comeback) | 4.04% | 3.87% | 3.36% | 2.53% |

#### Which comeback is more likely

If the favourite's [advantage](#the-example-match) is at least as large in the second half as in the first half, a comeback by the favourite is more likely than a comeback by the underdog.

- **Kind:** structural.
- **Basis:** proof. Write both comeback chances as sums over the deficit d and the second-half margin k, with k ≥ d + 1. By the mirror rule, each term for the favourite is (second-half advantage)^k ÷ (first-half advantage)^d times the matching term for the underdog. With the condition, this factor is at least the second-half advantage, which is more than 1.
- **A common case:** The same share of the expected goals in both halves gives the same advantage in both halves. So the condition is true for every column of the [Favourite and underdog](#favourite-and-underdog) table.
- **Example:** In the example match, the advantage is 1.2 in the first half and 1.33 in the second half. So 2/1 (2.48%) is more likely than 1/2 (1.55%).
- **Limit:** Without the condition, the result can reverse. Example: the favourite's rates are 1.0 and 0.9 (first half, second half), and the underdog's rates are 0.4 and 0.8. The advantage falls from 2.5 to 1.125. The favourite's comeback chance is 1.60%. The underdog's comeback chance is 3.23%.

#### Balance

In the checked settings, a balanced match gives the most comebacks. Near balance, the effect is small.

- **Kind:** structural.
- **Basis:** grid check, 1,210 settings: expected goals 1 to 6 in steps of 0.5; first-half share 30%, 40%, 44%, 50% or 60%; favourite's share 52% to 94% in steps of 2%; the same share in both halves. This file has no proof.
- **Example:** In the [Favourite and underdog](#favourite-and-underdog) table: 4.04% at a 50% share, 3.87% at 60%, 2.53% at 80%.
- **Also in this example:** The favourite's comeback chance changes little as the favourite becomes stronger. It falls only for a very strong favourite. The underdog's comeback chance falls fast.

#### The goal total after the match

If you know the final goal total, multiplying all four rates by the same number does not change the comeback chance.

- **Kind:** structural.
- **Basis:** proof. Take independent Poisson counts and fix their total. Then the counts have a multinomial distribution. Each goal goes to one of the four team-halves (for example, the home team in the first half). The probability for each team-half is its share of the total rate. Multiplying all four rates by one number does not change the shares.
- **Example:** Double all four rates of the example match. P(comeback | 5 goals) stays at 13.76%.
- **Limit:** A change in the shares does change the chance. For example, more expected goals for one team change it, even with the final total fixed.

#### Comeback rate by final goal total

In the checked settings, the comeback rate by final goal total goes up and down: each odd total is above its even neighbours.

- **Kind:** structural, with a definitional cause.
- **Basis:** example, and a grid check over 9 settings: first-half share 30%, 44% or 60%; home share 50%, 65% or 80%; final totals 3 to 8. The expected total does not change these rates, by [the rule above](#the-goal-total-after-the-match).
- **The pattern in the example match:**

| final goal total | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|
| P(comeback) | 10.29% | 3.95% | 13.76% | 6.55% | 15.62% | 8.41% |

- **Why it goes up and down:** An even total can end in a draw, and it can never end with a one-goal margin. That part is definitional. For the usual goal totals, most comebacks end with a one-goal margin. That part is structural.
- **Trap:** A table of comeback rates by final goal total will show this pattern. It is not a finding. Also, the final total is a post-match value. It is never a pre-match feature.

#### The most common comeback scores

In the example match, most comebacks end 2-1, with a one-goal margin.

- **Kind:** structural.
- **Basis:** example. The "How general" part is a grid check over 12 settings: expected goals 1.5 to 6.5 in steps of 1; home share 50% or 70%; first-half share 44%.
- **Example:** 78% of comebacks end with a one-goal margin. The final scores are: 2-1 55%, 3-2 20%, 3-1 13%, all others 12%.
- **Why:** In the example match, matches with 3 goals are much more common than matches with 5 goals or more.
- **How general:**
  - 2-1 is the most common comeback score up to about 3.5 expected goals. At 4.5 expected goals or more, 3-2 or 4-3 is the most common.
  - The share of one-goal margins falls as the expected goals increase: about 85% at 1.5 expected goals, and 55% to 62% at 5.5.

#### Sensitivity to the second-half rates

In the checked settings, a small change in the trailing team's second-half rate gives a large change in the comeback chance.

- **Kind:** structural. This card adds one thing to the basic model: the trailing team's second-half rate is multiplied by an invented number.
- **Basis:** example. The "How general" part is a grid check over 4 settings: expected goals 1.5, 2.5, 3.5 and 4.5; first-half share 44%; home share 56%.
- **Example:** The example match. The leading team does not change:

| trailing team's second-half rate | × 0.9 | × 1.0 | × 1.1 | × 1.2 | × 1.3 |
|---|---|---|---|---|---|
| P(comeback) | 3.35% | 4.03% | 4.75% | 5.50% | 6.29% |

- **Effect:** In this example, a 10% change in that rate gives a change of about 17% to 18% in the comeback chance.
- **How general:** In all 4 settings, a 10% increase gave 17.7% to 18.6% more comebacks.
- **The leading team counts less:** Multiply the leading team's second-half rate by 0.8. The comeback chance increases only from 4.03% to 4.48%.
- **Why it matters:** A real change in the second-half rates after HT would have a large effect. Whether it exists is an [open question](#score-effects).

### Limits of the model

#### What the basic model does not include

The basic model is a reference, not the truth. Real matches can be different in these ways:

1. **Score effects:** The second half can depend on the HT score.
2. **Red cards:** A red card changes both rates for the rest of the match.
3. **Low scores:** Real 0-0, 1-0, 0-1 and 1-1 results can be more common or less common than the model gives.
4. **Spread:** Goal counts can vary more than a Poisson distribution allows.
5. **Team news:** Injuries, lineups and motivation change the rates. The model knows only the rates.

- **Kind:** a list of the assumptions of the basic model. The size of each difference is empirical.
- **Rule:** A better model changes only the structural numbers. The definitional facts never change.

---

## 3. The price

#### The HT/FT market

The HT/FT market has 9 selections: 1/1, 1/X, 1/2, X/1, X/X, X/2, 2/1, 2/X, 2/2.

- **Kind:** definitional. In each completed match, exactly one selection wins.
- **The comeback selections:** 2/1 and 1/2. In the example match, the two have 4.03% of the probability. The other seven selections have the rest.

#### Odds and implied probability

Decimal odds give the return for a stake of 1. The return includes the stake. The implied probability is 1 ÷ odds.

- **Kind:** definitional.
- **Example:** Odds of 34.0 return 34 for a stake of 1. The implied probability is 1 ÷ 34.0 = 2.94%.
- **Fair odds:** 1 ÷ the true probability. In the example match, P(2/1) = 2.48%. So the fair odds are 40.3.

#### The margin

The *overround* is the sum of the implied probabilities of all selections, minus 100%. This file calls the overround the *margin*. Other name: vig.

- **Kind:** definitional. The size of the margin is empirical.
- **Example:** The 9 HT/FT odds give implied probabilities with a sum of 115%. The margin is 15%.
- **Trap:** Some sources use "margin" for 1 − 1 ÷ (the sum). With a sum of 115%, that gives 13.0%, not 15%. Check the definition before you compare two sources.
- **To remove the margin:** Divide each implied probability by the sum. This method divides the margin evenly between the selections. Shin's method can be useful when the margin is not even, for example on long odds. This file does not choose a method.

#### Margin on long odds

Bookmakers often put a larger part of the margin on long odds. This is the favourite–longshot bias.

- **Kind:** empirical. It is an empirical market pattern that betting research reports. Its size in a given market needs data.
- **Why it matters:** The comeback selections have long odds. So the margin can be a large part of their price.
- **Example:** A bookmaker offers 2/1 at 34.0, an implied 2.94%. If the model is correct, the fair probability is 2.48%. The difference is 0.46 percentage points, about 19% of the fair probability.

#### Break-even probability

A bet makes money in the long run only if the true probability is more than 1 ÷ odds.

- **Kind:** definitional. It is arithmetic.
- **Example:** At odds of 34.0, the break-even probability is 2.94%. The example match has P(2/1) = 2.48%. If the model is correct, the bet loses money in the long run.
- **Opening and closing odds:** The odds change before kickoff. The *opening odds* are the first odds. The *closing odds* are the last odds before kickoff.
- **Rule:** Compare a probability with the odds that were available at the time of the decision.

#### Two selections as one bet

To bet on a comeback by either team, bet on 2/1 and 1/2 together. Divide the stake in proportion to 1 ÷ odds. Then both results give the same return, and the pair is one bet.

- **Kind:** definitional. It is arithmetic.
- **Formula:** combined odds = 1 ÷ (1/o₁ + 1/o₂).
- **Example:** 2/1 at 34.0 and 1/2 at 51.0. The combined odds are 1 ÷ (0.0294 + 0.0196) = 20.4. For a stake of 10, put 6.0 on 2/1 and 4.0 on 1/2. Each result returns 204.
- **Break-even:** 1 ÷ 20.4 = 4.90%. The example match has P(comeback) = 4.03%. If the model is correct, the pair loses money in the long run.
- **Trap:** The pair carries the margin of both selections.

#### Prices that the main markets imply

The main markets give information about the rates. Under the goal model, that information gives a comeback probability.

- **Kind:** structural.
- **Basis:** proof. In the model, the comeback probability is a function of the four rates, and the markets are used to estimate the rates.
- **What each market gives:**
  - The goal-line market gives information about the expected total of goals. It does not give the split between the teams.
  - The 1X2 market gives information about the split between the teams.
  - Under the goal model, the two markets can be used together to estimate the expected goals of the two teams.
- **Method:** Find the rates that come closest to the 1X2 and goal-line probabilities. Calculate P(2/1) and P(1/2) from those rates.
- **Rule:** State the estimation method, including how the margin is removed. Two methods can give slightly different rates from the same odds.
- **Limit:** The split between the halves needs one more input. Examples: a fixed first-half share, or the odds of a half-time market.
- **Why it matters:** The main markets already imply a comeback probability. A comeback price far from that value has two possible causes: the margin, or information. The cause is empirical.

#### What a pre-match feature must do

A pre-match feature can change a comeback probability in only two ways:

1. It changes the chance to be behind at HT (link 1).
2. It changes the completion rate (link 2).

- **Kind:** definitional. It follows from [the chain](#the-chain).
- **Structural consequence:** In the basic model, both links depend only on the four rates. The market odds give information about the rates. So a feature that predicts only goals must predict them better than the market.
- **Empirical part:** A feature can also predict a difference from the basic model, for example a score effect. Whether the market prices such differences is empirical.

---

## 4. Why comebacks are hard to measure

All cards in this section are statistical design: calculations about tests, not facts about comebacks.

#### Rare events need large samples

A small difference in a rare rate needs many matches.

- **Kind:** statistical design. It follows from the test and its assumptions, not from football.
- **Example:** The base rate is 4%, the rate of the example match, rounded. A rule selects matches with a higher true rate. The table gives the number of selected matches that a test needs. The test is a two-sided one-sample test with a normal approximation, a 5% significance level and 80% power:

| true rate in the selection | 5% | 6% | 8% | 10% |
|---|---|---|---|---|
| matches needed | 3,221 | 852 | 234 | 113 |

- **Why it matters:** A rule with a true rate of 5% against a 4% base needs more than 3,000 selected matches. A smaller sample may not have enough power to detect the difference.

#### Team counts are small

One team has few comebacks in one season.

- **Kind:** statistical design.
- **Example:** A team plays 30 matches. The chance of a comeback by this team is 2% per match, half of the example match's 4%. So the team expects 0.6 comebacks in the season.
- **The counts:** 0 comebacks in 54.6% of seasons, 1 in 33.4%, 2 in 9.9%, 3 or more in 2.2%.

#### Comeback teams by chance

In a league, some teams have many comebacks by chance alone.

- **Kind:** statistical design.
- **Example:** 16 teams play 30 matches each. Each team has the same 2% chance per match. In 87% of seasons, at least one team has 2 comebacks or more. In 30% of seasons, at least one team has 3 or more. (The calculation treats the teams as independent.)
- **Trap:** A team with 3 comebacks in a season can be an average team.
- **Rule:** Do not select teams by their comeback count and then test them on the same data.

---

## 5. Open questions

All questions in this section are empirical. Only data can answer them. This file gives no answers.

### The model inputs

1. What are the four rates of a match? How much information about them do the market odds give?
2. What share of the goals comes in the first half? Is the share different between leagues?
3. Is a favourite's advantage larger in the first half or in the second half?
4. Do real low scores and real goal counts differ from the basic model? By how much?
5. Does the comeback chance increase with the expected goals by the amount that the model gives?
6. Do real comeback rates by final goal total follow the pattern of the model?

### Score effects

7. After HT, does the trailing team score faster than the model expects?
8. After HT, does the leading team score slower, or concede faster?
9. Do these effects change with the deficit, the minute, or the strength gap?

### Events during the match

10. Does a red card change the completion rate? Check the order: the card must come before the goals that it explains.
11. Do substitutions change the completion rate: their number, or their minute?
12. Does fatigue change the completion rate, for example after few rest days?

### Teams and leagues

13. Do some teams have a higher completion rate than their rates predict? Does this stay the same from season to season?
14. Do some leagues have more comebacks than their goal rates predict?
15. Does information before kickoff (lineups, motivation, the table) change link 1 or link 2 more than the market odds show?

### The price

16. How large is the margin on 2/1 and 1/2? Does it change with the odds?
17. Is the 2/1 or 1/2 price sometimes far from the value that the main markets imply? When?
18. How do the comeback odds change between the opening and the closing odds?

---

## 6. All facts by kind

Find a fact here before you measure it.

### Definitional — never measure it, never report it as a finding

| fact | card |
|---|---|
| A comeback needs a team behind at HT. A draw at HT makes it impossible. | [Comeback](#comeback), [Goals in each half](#goals-in-each-half) |
| "A comeback by either team" is two selections: P = P(2/1) + P(1/2). | [A comeback by either team](#a-comeback-by-either-team) |
| A comeback needs 3 goals or more. A deficit of d needs 2d + 1 goals or more. | [Minimum goals](#minimum-goals) |
| The trailing team scores 2 goals or more in the second half and wins it by 2 or more. | [Goals in each half](#goals-in-each-half) |
| The winner has 2 goals or more, and the loser 1 or more. No comeback ends 1-0, 2-0 or 3-0. | [The final score](#the-final-score) |
| Both teams score, and the match has more than 2.5 goals. | [The final score](#the-final-score) |
| An odd total is never a draw. An even total never ends with a one-goal margin. | [Odd and even goal totals](#odd-and-even-goal-totals) |
| Every comeback is in the comeback environment. | [The comeback environment](#the-comeback-environment) |
| A filter that removes impossible matches loses no comebacks. | [Filters that remove impossible matches](#filters-that-remove-impossible-matches) |
| P(comeback) = P(B) × P(C \| B), and its full form over HT scores. | [The two links](#the-two-links), [The full form](#the-full-form) |
| Implied probability, fair odds, the margin, break-even, combined odds. | [Section 3](#3-the-price) |
| A pre-match feature works only through link 1 or link 2. | [What a pre-match feature must do](#what-a-pre-match-feature-must-do) |

### Structural — derive it once, in this file

One basis per row. No row mixes a proof with a grid check or an example.

| fact | basis | card |
|---|---|---|
| Each team scores at a constant rate in each half. The four goal counts are independent Poisson counts. | assumption | [The basic goal model](#the-basic-goal-model) |
| Under the basic model, the completion from an HT score depends only on the deficit and on the second-half rates. So who is behind counts. | proof | [Completion in the basic model](#completion-in-the-basic-model) |
| A win by k goals is (λ/μ)^k times as likely as a loss by k goals. So, under the basic model, the team with more expected goals has the higher chance to win. | proof | [The mirror rule](#the-mirror-rule) |
| The completion always falls as the deficit grows. | proof | [Deficit size](#deficit-size) |
| In the checked settings, more second-half goals make the completion fall slower. | grid check | [Deficit size](#deficit-size) |
| In the example match, growing all four rates by one factor gives more comebacks, at least up to 40 expected goals. | example | [Expected goals](#expected-goals) |
| If one team has the higher rate in both halves, growing all four rates without limit takes the comeback chance to 0. | proof | [Expected goals](#expected-goals) |
| For a fixed total rate and fixed team shares, every highest comeback chance is at a first-half share between the two ends. | proof | [First half and second half](#first-half-and-second-half) |
| A favourite with the higher rate in both halves is behind less often. When it is behind, it wins more often. | proof | [Favourite and underdog](#favourite-and-underdog) |
| If the favourite's advantage is not smaller in the second half, its comeback is more likely than the underdog's. | proof | [Which comeback is more likely](#which-comeback-is-more-likely) |
| In the checked settings, a balanced match gives the most comebacks, and near balance the effect is small. | grid check | [Balance](#balance) |
| Given the final total, multiplying all four rates by one number does not change the comeback chance. | proof | [The goal total after the match](#the-goal-total-after-the-match) |
| In the checked settings, comeback rates by final total go up and down: each odd total is above its even neighbours. | grid check | [Comeback rate by final goal total](#comeback-rate-by-final-goal-total) |
| In the checked settings, 2-1 is the most common comeback score up to about 3.5 expected goals. | grid check | [The most common comeback scores](#the-most-common-comeback-scores) |
| In the checked settings, a 10% increase in the trailing team's second-half rate gives about 18% more comebacks. | grid check | [Sensitivity to the second-half rates](#sensitivity-to-the-second-half-rates) |
| Under the goal model, the main markets imply a comeback probability. | proof | [Prices that the main markets imply](#prices-that-the-main-markets-imply) |

### Statistical design — calculate it, never measure it

| fact | card |
|---|---|
| A small difference in a rare rate needs thousands of matches. | [Rare events need large samples](#rare-events-need-large-samples) |
| One team has few comebacks in one season. | [Team counts are small](#team-counts-are-small) |
| Average teams can show many comebacks by chance. | [Comeback teams by chance](#comeback-teams-by-chance) |

### Empirical — measure it

All the questions in [section 5](#5-open-questions). Also the size of the margin, and the favourite–longshot bias.
