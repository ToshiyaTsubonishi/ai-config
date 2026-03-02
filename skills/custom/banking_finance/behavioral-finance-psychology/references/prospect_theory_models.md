# Prospect Theory Models for AGI

## 1. Value Function (価値関数)
ユーザーが感じる「主観的な価値」は、実際の金額とは異なる。

$$ V(x) = \begin{cases} x^\alpha & \text{if } x \ge 0 \\ -\lambda(-x)^\beta & \text{if } x < 0 \end{cases} $$

*   $x$: 損益額
*   $\lambda$ (Lambda): 損失回避係数（通常 2.25）。損失は利益の約2.25倍痛い。
*   $\alpha, \beta$: 感応度逓減（通常 0.88）。金額が大きくなると感度が鈍る。

## 2. Weighting Function (確率加重関数)
人間は低い確率を過大評価し、高い確率を過小評価する。

*   **宝くじ効果:** 当選確率が極めて低いIPOなどを過剰に買いたがる。
*   **確実性効果:** 99%大丈夫でも、1%の暴落リスクを過剰に恐れて定期預金を選ぶ。

## 3. Implementation in Python
```python
def calculate_subjective_pain(loss_amount, lambda_param=2.25):
    """
    損失額からユーザーが感じる『精神的苦痛』を算出する。
    """
    return -lambda_param * (abs(loss_amount) ** 0.88)
```

