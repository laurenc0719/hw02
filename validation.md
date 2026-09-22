VALIDATION METHOD 1 - BY HAND
1. I wasn't really sure how to do any of the calculations by hand, so I asked claude for the best way to do it by hand.
It told me that amount should equal shares x price for security transactions. It said to test 100% of the population for when this isn't true by using this formula in excel:
=IF(OR(G2="",H2=""),"n/a",IF(ABS(ROUND(G2*H2,2)-I2)>0.01,"BREAK","ok"))
then to do a countifs on the number of breaks that should equal 897. That is what I got after testing it this way.

VALIDATION 2 - ASKING COWORK TO EXPLAIN THE CODE
In a new cowork chat, I uploaded the eda python file and asked Claude : "Walk me through each section. What should I see in the terminal when I run this script?”
It said the code was "90% of the way there", which is interesting because the code worked fine the first time I ran it in VSCode. This was the output Claude gave me: 
Section by section

Banner. Title, your name, the source file path (a Windows path like C:\MIS3060\EDA\data\raw\fact_transactions.csv), and a run timestamp. Every section after this gets a blank line and then a header between two 78-character ===== bars.

[2] Shape. Rows, columns, and the tuple. It should read 298,772 / 9 / (298772, 9).

[3] Columns and dtypes. A heads-up so you don't panic: pandas 3.x shows txn_type as str, not object, and txn_date as datetime64[us], not [ns]. If your professor's example screenshot shows object, that's just an older pandas (・ω・)b Also, security_id will show as float64 if it's numeric with nulls, since NaN forces the float type.

[4] Missing values. A table with column / missing / pct_missing columns and a total missing count. Expect security_id, shares, and price to have matching null counts if cash transactions don't carry a security.

[5] Descriptive stats. This is the full describe() grid: count, mean, std, min, 25%, 50%, 75%, and max for every numeric column.

[6] txn_type counts. Types sorted by count with percentages, then Distinct txn_type values: N.

[7] Unique entities. Counts of clients, advisors, and securities, plus a note about how many security_id values are null.

[8] Date range. Earliest date, latest date, span in days, and the number of null dates.

[9] Duplicate check. Duplicate txn_ids, unique txn_ids, and fully duplicated rows. Then either Result: txn_id is a valid unique primary key. or a WARNING line.

[10] Amount stats. Mean, median, skewness, and a one-line interpretation. The thresholds are ±0.5.

[11] Amount by type. Count, mean, and median of amount per txn_type, sorted by mean from high to low.

[12] Correlation matrix. A 3×3 grid for shares, price, and amount, followed by the "three strongest" ranking.

[13] Shares by type. Non-null count, min, max, and number of negatives per type, then an "Overall" line. Cash types will show NaN for min and max, which is expected.

(The .txt file gets written silently here, and it contains only items 2–13.)

[14] Shape validation. You should see OK: shape matches expected (298772, 9).. If you see a WARNING instead, your CSV is the wrong version or got truncated.

[15] Charts. Three saved -> ...png lines: the histogram, the box plot, and the scatter plot.

[16] + wrap-up. A confirmation that the profile was saved, then the ALL 17 STEPS COMPLETE banner with the paths to the charts and the profile.

VALIDATION METHOD 3 - ASK CLAUDE COWORK TO EXPLAIN THE OUTPUT 
I copy and pasted the terminal output into cowork and asked Claude: “What does each value mean? Flag anything unexpected.”
It had an unexpected flag in DTypes, which it said: 
If you join to a security dimension table later, cast it to nullable Int64 so it displays as 123, not 123.0. You can do that in the loader: pd.read_csv(..., dtype={"security_id": "Int64"}).
There was another unexpected flag in descriptive stats.
FLAG: The txn_id, client_id, advisor_id, and security_id rows are noise. A "mean txn_id of 149,386.5" means nothing, so drop those columns or at least ignore them.
price runs from $10 to $500 with the mean and median both around $255.
shares has its median near 249 and a max near 500.
The quartiles for both are almost perfectly evenly spaced. That's the signature of a uniform distribution, meaning this data was generated, not pulled from real trading. That's fine for class, but it explains some of the weirdness below.
amount minimum is $13.33, so there are no negative amounts. Sells and withdrawals are stored as positive numbers, with direction coming from txn_type. That means the signed-amount caveat I raised last time doesn't apply, and your skew number is legit.
It also flagged unique entities. 
2,700 clients, 25 advisors, 500 securities.
FLAG: The max client_id is 3,192, but only 2,700 distinct IDs appear. That leaves 492 IDs with zero transactions. If the client dimension table has 3,192 rows, those are clients who didn't transact in this window. They'll show up as NaN in a left join from the client table, so don't mistake that for broken data.
Advisors (max 25 = 25 unique) and securities (max 500 = 500 unique) are contiguous, no gaps.
FLAG: The printed note says "(e.g. Deposit / Withdrawal)" but leaves out Advisory Fee. Update that string to name all three.
It had a huge flag was in amount by type.
FLAG (big): Dividends average $64,077, which is basically the same as Buys ($63.7K) and Sells ($63.6K). A real dividend is a percent or two of the position value, not the entire trade value. It looks like the dividend amount was computed as shares × price, the same way trades are. Call this out as a business-logic issue: at face value, it overstates dividend income by roughly 50–100×.
FLAG: Advisory Fee has a mean of $7,375 but a median of only $859, so the mean is about 8.6× the median. That's a heavy tail inside the fee category. Either a few huge accounts are paying big fees, or there are outliers. Worth running a .describe() on the fee rows alone.
It said the most important flag was in shares by type.
FLAG (biggest one): There are 836 negative-share rows, and every single one is a Buy. Sells have a minimum of +1.003, so a negative sign isn't the convention for selling. A negative-share Buy is just invalid. It's also exactly 1.0% of Buys (836 / 83,556), which smells like a data-quality error your professor planted on purpose.
It gets weirder: amounts are never negative, so on those 836 rows amount ≠ shares × price (that product would be negative). The amount was probably calculated from the absolute value of shares, or the sign got flipped after the fact.

VALIDATION METHOD 4 - Business-Reasonableness Check
I asked Claude if the results made sense overall for the business context of the company.
It said what doesn't make sense is:
1. The dividends were wildly overstated
2. The cash doesn't reconcile without those dividends
3. Negative-share Buys aren't a real transaction
4. Minor: Billing frequency
5: Minor: The data is synthetic
I followed up on #3, since it didn't make sense for it to be included in the data if it wasn't real. 
It told me that it's not a valid Buy, but it could be a real event that got recorded wrong.
It also said that it was probably planted because the "whole point of EDA is to catch problems before anyone builds a dashboard or model on the data."

VALIDATION METHOD 5 - Cross-Validation
First, I asked Claude: In fact_transactions.csv, count the rows where shares is negative.
It told me it should be 836.
I then asked it : In fact_transactions.csv, count the rows where both shares and price are populated and amount differs from shares × price by more than $0.01.
That also got 836.
