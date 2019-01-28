# Fuzzy Matching of Company Names

This repo documents the functions to match company record by the following criteria:
- company name (with fuzzy matching)
- distance from zipcode or tuple of city and state
- street address (wip)

## error log
```
[4, 14, 21, 26, 27, 37, 38, 42, 45, 47, 49, 56, 65, 72, 75, 76, 90, 96]
with jelly

4: 86 mismatch
14: 86 mismatch
21: 91, 85
26: 86: # if in  NY, then use 5 miles as cutoff
27: 86 NJ
37: BEAR STEARN', 'Bear Stearns Asset Management Inc.') # maybe there is a bug
38: add academy, healthcare to keys,
42: add property to keys
45: need to merge record in target dataset,SEQA and seneca
47: rid of 'the'
49: more than 30 miles away
56: SATURN CAPITAL MANAGEMENT LLC', 'Saturn Partners, LLC'
65: add lab to keys
72: add america, asia to keys
75: add health to keys
76: RFI intl vs RFI investments
90: 87 score
96: add law to keys, 85 scores

[16, 26, 28, 37, 45, 49, 56, 60, 86]
with fuzzy
```

- add software, academy, school to keys
- adjust threahold based on how far away they are