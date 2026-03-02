# SQLクエリ例 (Dune Analytics)

## 1. 日次アクティブユーザー数 (DAU)
```sql
SELECT
  date_trunc('day', block_time) AS day,
  COUNT(DISTINCT "from") AS active_users
FROM
  ethereum.transactions
WHERE
  to = '\xYourContractAddress' -- 自社コントラクトアドレス
  AND block_time > NOW() - INTERVAL '30 days'
GROUP BY
  1
ORDER BY
  1 DESC;
```

## 2. トークン保有者分布 (Holder Distribution)
```sql
WITH transfers AS (
  SELECT
    "to" AS address,
    value AS amount
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = '\xYourTokenAddress'
  UNION ALL
  SELECT
    "from" AS address,
    -value AS amount
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = '\xYourTokenAddress'
)
SELECT
  address,
  SUM(amount) / 1e18 AS balance
FROM
  transfers
GROUP BY
  1
HAVING
  SUM(amount) > 0
ORDER BY
  2 DESC
LIMIT 100;
```
