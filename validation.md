
### 2A — Table Check
| Check | Expected | Your Script Produced | Match? | Notes |
|---|---|---|---|---|
| Dataset shape | (298772, 9) | (298772, 9) | Yes | |
| Null count — `security_id` | 101,597 | 101,597 | Yes | = Deposit + Withdrawal + Advisory Fee |
| Null count — `amount` | 0 | 0 | Yes | |
| Unique `txn_type` values | 6 | 6 | Yes | |
| Count of `Buy` transactions | 83,556 | 83,556 | Yes | 27.97% of rows |
| `txn_date` data type | object | datetime64[us] | **No** | See Discrepancy 1 |
| Earliest `txn_date` | 2020-01-01 | 2020-01-01 | Yes | |
| Latest `txn_date` | 2024-12-30 | 2024-12-30 | Yes | |
| Duplicate `txn_id` count | 0 | 0 | Yes | Valid primary key |
| Mean `amount` | $54,075.17 | $54,075.17 | Yes | |
| Median `amount` | $41,220.48 | $41,220.49 | **No** | See Discrepancy 2 |
| Skewness of `amount` | 1.15 | 1.15 (1.146296) | Yes | Right-skewed |
| Correlation `shares`–`amount` | 0.65 | 0.65 (0.648771) | Yes | |
| Correlation `price`–`amount` | 0.64 | 0.64 (0.644727) | Yes | |
| Correlation `shares`–`price` | 0.00 | 0.00 (0.002726) | Yes | Independent |
| Negative `shares` count (Buy only) | 836 | 836 | Yes | All negatives are Buy |
| Profile file created | Yes | Yes | Yes | `hw02/hw02_profile.txt` |
| Chart files created (3) | Yes | Yes | Yes | All 3 PNGs, 150 DPI |

Discrepancy 1: 
Me: "Can you explain the discrepancy in txn date data type?"
Claude: The discrepancy has two independent causes

Cause 1 — my choice. I load with parse_dates=["txn_date"], which converts the column to datetime64[us] at read time. The rubric assumes a plain pd.read_csv() that leaves it as text.

Cause 2 — your pandas version. This is the one that makes "object" unreachable. Here's what a plain read gives on your machine:

read_csv(parse_dates=['txn_date'])  ->  datetime64[us]
read_csv()                          ->  str          ← not "object"

Historically, pandas had no real string type. Any text column got dumped into object dtype — a NumPy array of pointers to individual Python string objects. Slow, memory-hungry, and object told you nothing about what was actually in there (strings? dicts? mixed garbage?).

pandas 3.0 fixed that. PDEP-14 made a dedicated str dtype the default for text. So on pandas 3.0.6, text columns come back as str, not object. The rubric's expected value was written against pandas 2.x.

Meaning: removing parse_dates does not get you to object. It gets you to str. The only way to literally produce object is to force it:

python
pd.read_csv(path, dtype={"txn_date": object})

Which is you contorting your code to satisfy a stale expected value.

Why I parsed the dates anyway

String min/max on dates works only by coincidence — it happens to be right for ISO-8601 (YYYY-MM-DD) because alphabetical order equals chronological order. Change the format and it silently breaks:

US-format: ['12/30/2019', '01/01/2024', '06/15/2021']
  string min : 01/01/2024   ← WRONG (should be 12/30/2019)
  string max : 12/30/2019   ← WRONG (should be 01/01/2024)
  parsed min : 2019-12-30   ✓
  parsed max : 2024-01-01   ✓

No error. No warning. Just a wrong date range in your report. Your file happens to be ISO, so strings would've worked — but the code would be correct by luck, not by construction.

Parsing also buys you things strings can't do at all:

	string	datetime
Date range in days	✗	1,825
Filter to 2024	✗	67,405 txns
Memory	20.0 MB	2.4 MB

8× less memory, and item 8's "span" line only exists because the column is a real date.

Also: datetime64[us], not [ns]

Every tutorial says datetime64[ns]. Yours says [us] (microseconds). Not a bug — pandas 3.0 now infers the smallest resolution the data needs instead of always forcing nanoseconds. Your data is date-only, so microseconds is plenty.

Discrepancy 2:
Me: Can you explain the discrepancy in median amount?
Claude: Okay this one's a four-link chain and every link is doing something reasonable. Here's the whole thing:

Link 1 — your row count is even

298,772 rows. With an even count there's no single middle value, so the median is the average of the two middle observations:

position 149,386 : $41,219.90
position 149,387 : $41,221.07
           average: $41,220.485

The true median is $41,220.485. Not a rounding artifact — that's genuinely the number.

Link 2 — the gap between them is an odd number of cents

They differ by $1.17. Averaging two 2-decimal values whose gap is an odd number of cents always lands you on a half-cent. If the gap had been $1.16 or $1.18 you'd have gotten a clean 2-decimal median and none of this would've happened. You got unlucky by exactly one cent.

Link 3 — .485 doesn't exist in binary

Floating point can't represent $41,220.485 exactly. What's actually in memory:

41220.485000000000582076609134674072265625

Note it's slightly above .485. That matters in a second.

Link 4 — the two methods take different routes
f"{med:,.2f}"     -> 41,220.49    ← my script
round(med, 2)     -> 41220.48     ← the rubric

Why .49: Python's string formatting reads the actual stored binary value. That value is above .485, so rounding up to .49 is correct.

Why .48: numpy's round doesn't read the value directly — it multiplies by 100 first:

med * 100        = 4122048.5        ← float math lands exactly on .5
np.rint(4122048.5) = 4122048.0      ← half-to-EVEN, and 4122048 is even
/ 100            = 41220.48

Two things stacked: the ×100 step wiped out the "slightly above" information, and then rint used banker's rounding, which breaks ties toward the even number. 4122048 is even, so down it went.

Excel gives .49 (half away from zero), same as my script.

So who's right?

.49 is more defensible — it reflects the actual stored value, and it's what both Python's formatter and Excel produce. .48 is an artifact of numpy's scale-then-round implementation colliding with banker's rounding.

But the difference is one cent on a $41,220 median — 0.0000243%. Immaterial by any standard you'd ever apply. Neither answer is wrong; they're answering slightly different questions.

The pattern worth naming

This is the third time a half-cent boundary has bitten you today:

Cross-foot: 860 vs 873 vs 897 breaks
The 24 "$0.01 rounding" exceptions
This median

Same root cause every time — amount was rounded to 2 decimals when the dataset was built, so half-cent values are everywhere, and every tool breaks ties differently. One practical takeaway: set tolerances to straddle the boundary, never sit on it. That's why >0.01 gave a rock-stable 836 while ROUND(...) gave three different answers.

### 2B — Explain the Code and Output
1. Claude refused to produce any numeric values, saying that inventing them would be fabrication. Glad to see AI now has a moral code. Therefore, it gave me more structural predictions. It matched with the exception of 4 discrepancies:
It predicted txn_type would be an object, and txn_date would be datetime64[us]. In actuality it was both str and datetime64.
It also said shares <--> amount would be strongly positive, and price <--> amount would be weak to moderate. My script gave me a 0.65 and 0.64 output, meaning they're basically the same.
It predicted that negative shares would appear on sell/withdrawal, while all 836 negatives are on Buy.
It also said the histogram would be squished into one bar while it reads pretty clearly.

2. It flagged using the absolute value of shares in the amount equation of interesting, because the negative-shares rows have positive amounts. It also flagged:
No sign convention on amount,, the 0.65/0.64 correlation being an artifact, advisory fee being a separate distribution, dividend rows carry a price up to $500/share, transactions on all the calendar days including weekends and holidays, client_id gaps, describe() profiling ID columns, and made a larger "meta-flag" at the end saying the data was probably synthetic.

3. It identified and explained the 101,597 nulls in security_id as structural and not missing data. It said that the security_id, shares, and price are all null in the same rows and that Deposit + withdrawal + advisory fee = 101,597 exactly. It told me I should not impute this data.

4. It did flag this. It said that every one of the calendar days has transactions, which is not realistic because banks don't operate on bank holidays. It said that it matters because volume trends are artificially smooth and that day-of-week and seasonality analysis is invalid.

5. Claude predicted that the histogram would be unreadable and be squished into a single bar, but it's actually pretty well-distributed across all of the bins. Its prediction for the box amount by type matched, which was that there would be five boxes with similar medians. It also predicted the scatter shares amount graph would be an "unreadable blob" and it's actually pretty clean.

6. Me: Why is the shares and amount correlation only 0.65 if amount is derived from shares x price? Wouldn't that mean it's closer to 1
   Claude: Because Pearson's r measures linear association, and a product of two random variables isn't linear in either one. When you multiply shares by an independent random price, the price variation scatters the points into a wedge rather than a line — the relationship is perfect but not straight, so r understates it badly. Two confirmations: (a) taking logs converts the product into a sum, log(amount) = log(shares) + log(price), and the correlation rises to 0.76; (b) price↔amount is 0.64, essentially identical to shares — neither input dominates, because both contribute symmetrically to the product. The takeaway for the writeup is that "moderate correlation" is the wrong interpretation. amount is an exact identity, and reporting r = 0.65 as evidence of a moderate relationship would understate a relationship that is actually deterministic.

### 2C — Business Check & Cross-Validation
1. Deposit, withdrawal, and advisory fee don't involve buying or selling a security. A deposit is when a client moves cash into the account, a withdrawal is when a client moves cash out, and the advisory fee is just the firm's management fee. The deposit count is 35,981, the withdrawal count is 29,850, and the advisory fee count is 35,766, which adds up to 101,597. The same three columns are null in the same rows because a transaction either has a security or it doesn't.

2. It would mean that the company is buying more securities than selling. I asked claude to put a dollar value to it to help me understand what it would mean. Net securities purchases is 1.52billion, and net cash flows from clients is 0.33 billion. This would mean that there's more capital flowing in then out, and AUM is growing organically.

3. My claude fixed this in the script by doing a line that said:
df = pd.read_csv(data_path, parse_dates=["txn_date"]). However, if it had stayed as a string, the .diff would make a typeerror because you can't subtract one string from another. The .dt accessor would raise an attributeerror. However, the sorting and filtering would appear to work.

4. I think it could be plausible, but it would sit at the upper band depending on the type of firm it is. I looked up what would be normal and got this website: https://smartasset.com/advisor-resources/average-number-of-clients-per-financial-advisor
which said that the median clients per firm is 73, and the average per-securities registered advisor would be 173. I suspect that it's skewed by large firms. Therefore, depending on our firm size it is definetly possible.

5. Two explanations could be that there was either a data-entry/ETL sign error, or that it's a legitimate reversal or contra entry, and negative shares could be an accounting mechanism for unwinding the original.
I think that the first explanation would make sense, because the amounts in those situations are also positive and a contra-entry in accounting would wipe both sides of the journal entry.

**Cross-validation.**
6. Both scripts returned a buy count of 83,556. All of the other amounts it provided also matched exactly.
7. Both of the results returned exactly 83,556, so neither is wrong and fortunately I don't have to reconcile.
8. It's good because it tests completeness and not just matching. You have to go through every other category to be able to subtract, meaning you need to know the values in each column. Therefore it tests different things than filtering.
