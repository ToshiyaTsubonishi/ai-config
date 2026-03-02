import json
import random
from datetime import datetime, timedelta

def generate_transactions(account_id, days=90):
    transactions = []
    balance = random.randint(100000, 5000000)
    current_date = datetime.now()

    for i in range(days):
        date = current_date - timedelta(days=days-i)
        date_str = date.strftime("%Y-%m-%d")
        
        if date.day == 25: # Salary
            amount = 300000 + random.randint(0, 50000)
            balance += amount
            transactions.append({"date": date_str, "type": "DEPOSIT", "desc": "Salary", "amount": amount, "balance": balance})
        
        if random.random() < 0.3: # Spending
            amount = random.randint(1000, 15000)
            balance -= amount
            transactions.append({"date": date_str, "type": "PAYMENT", "desc": "Shopping", "amount": -amount, "balance": balance})

    return transactions

if __name__ == "__main__":
    print(json.dumps(generate_transactions("123456"), indent=2))

