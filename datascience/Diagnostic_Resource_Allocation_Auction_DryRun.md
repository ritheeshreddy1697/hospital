# Diagnostic Resource Allocation Auction (MRI / CT / LAB) — End-to-End Dry Run

## 1. Context & Executive Summary

In a modern acute hospital, diagnostic imaging resources (e.g., High-Field MRI Scanner Slot 1) are highly scarce and shared across Emergency Room (ER), Operating Theatre (OT), and Intensive Care Unit (ICU). 

Traditional first-come-first-served queuing fails because clinical urgency and downstream flow bottlenecks change dynamically. 

This document presents a complete **3-Turn Auction Dry Run** for allocating one available **Diagnostic MRI Slot** at 13:00 across three competing department agents (**ER**, **OT**, **ICU**).

---

## 2. Agent Definitions & Utility Formulation

Each department computes its **Utility Ceiling** ($U_t$) — the maximum willingness-to-pay in priority points for the diagnostic slot at round $t$, based on patient state, clinical risk, and downstream bottleneck cost.

$$U_t = w_{\text{urgency}} \cdot \text{RiskScore}_t + w_{\text{flow}} \cdot \text{DelayCost}_t - \text{AlternativeValue}_t$$

### Competing Patients at 13:00:
1. **ER Agent (Emergency Room)**: Acute stroke suspect requiring urgent MRI Brain DWI sequence to determine thrombolysis window.
   - Initial Utility $U_1(\text{ER}) = 140$
   - Priority Shift Budget $B_0(\text{ER}) = 750$ points
2. **OT Agent (Operating Theatre)**: Post-op spinal surgery patient requiring emergency MRI Spine check prior to closing/transfer.
   - Initial Utility $U_1(\text{OT}) = 120$
   - Priority Shift Budget $B_0(\text{OT}) = 620$ points
3. **ICU Agent (Intensive Care Unit)**: Stable septic encephalopathy patient needing routine MRI Brain monitoring.
   - Initial Utility $U_1(\text{ICU}) = 90$
   - Priority Shift Budget $B_0(\text{ICU}) = 500$ points

---

## 3. The 3-Round Auction Mechanics

### Round 1 (13:00) — Initial Bidding
Agents calculate initial bid based on aggression parameter $\alpha = 0.60$ relative to headroom between current highest opponent bid and utility ceiling.

- **ER Round 1 Bid**:
  $$\text{Bid}_1(\text{ER}) = 85 \text{ points}$$
- **OT Round 1 Bid**:
  $$\text{Bid}_1(\text{OT}) = 78 \text{ points}$$
- **ICU Round 1 Bid**:
  $$\text{Bid}_1(\text{ICU}) = 55 \text{ points}$$

**Round 1 Leader**: ER (85 points).

---

### Round 2 (13:05) — Mid-Auction Dynamic Event & ICU Withdrawal

#### Dynamic Hospital Event at 13:04:
- ICU receives lab confirmation: CT scan alternative slot available at 13:30. Expected diagnostic confidence is 88%.
- ICU updates alternative pathway value: $\text{AlternativeValue}_2(\text{ICU}) = 50$.
- ICU recalculated Utility Ceiling drops:
  $$U_2(\text{ICU}) = 90 - 40 = 50$$

#### Round 2 Bidding:
- **ICU Evaluation**: Current highest bid is 85 (ER). ICU's updated ceiling is 50.
  $$Q(\text{Continue}) = 32 \quad \text{vs} \quad Q(\text{Withdraw}) = 62$$
  **ICU Action**: **WITHDRAW**. ICU exits auction to utilize CT scan slot.

- **OT Round 2 Bid**:
  OT sees ER bid at 85. OT remaining headroom $= 120 - 85 = 35$.
  RL aggression $\alpha = 0.70 \implies \Delta = 35 \times 0.70 \approx 25$.
  $$\text{Bid}_2(\text{OT}) = 85 + 25 = 110 \text{ points}$$

- **ER Round 2 Bid**:
  ER sees OT leading at 110. ER ceiling $= 140$. Headroom $= 30$.
  RL aggression $\alpha = 0.50 \implies \Delta = 15$.
  $$\text{Bid}_2(\text{ER}) = 110 + 15 = 125 \text{ points}$$

**Round 2 Standings**: ER (125) leads; OT (110) second; ICU (Withdrawn).

---

### Round 3 (13:10) — Final Re-evaluation & Resolution

#### Dynamic Hospital Event at 13:09:
- OT spinal patient neurological exam stabilizes; intraoperative ultrasound provides adequate visualization. OT utility ceiling drops from 120 to 95.
- OT's previous bid (110) exceeds its updated utility ceiling (95).
  $$Q(\text{Continue}) = 41 \quad \text{vs} \quad Q(\text{Withdraw}) = 78$$
  **OT Action**: **WITHDRAW**. OT cancels MRI request and proceeds with ultrasound protocol.

- **ER Final Round Action**:
  ER is sole remaining bidder. ER current bid $= 125$, utility ceiling $= 140$.
  Closing minimum market threshold $= 120$.
  $$\text{Final Winning Allocation Bid} = 125 \text{ points}$$

---

## 4. Complete Auction Summary Table

| Agent | Initial Utility | Round 1 Bid | Round 2 Utility | Round 2 Bid | Round 3 Utility | Round 3 Final Action | Result | Final Cost Charged |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ER** | 140 | 85 | 140 | 125 | 140 | **Bid 125** | **WIN** | **125 points** |
| **OT** | 120 | 78 | 120 | 110 | 95 | **Withdraw** | Lose | 2 points (Participation) |
| **ICU** | 90 | 55 | 50 | Withdraw | — | — | Lose | 2 points (Participation) |

---

## 5. Post-Auction Budget Reconciliation

Utility points represent valuation capacity and are **not** consumed. Shift budget priority points are consumed by the winner.

- **ER Budget Update**:
  $$B_{\text{new}}(\text{ER}) = 750 - 125 = 625 \text{ points}$$
- **OT Budget Update**:
  $$B_{\text{new}}(\text{OT}) = 620 - 2 = 618 \text{ points}$$
- **ICU Budget Update**:
  $$B_{\text{new}}(\text{ICU}) = 500 - 2 = 498 \text{ points}$$

### Reinforcement Learning Outcome Reward:
Post-allocation clinical monitoring yields positive reward $R = +165$ (ER stroke patient thrombolysis window saved + zero OT complications), reinforcing ER's bidding policy for acute stroke states.
