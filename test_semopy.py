import pandas as pd
import numpy as np
import semopy

np.random.seed(42)
n = 200
factor = np.random.normal(0, 1, n)
q1 = factor * 0.8 + np.random.normal(0, 0.5, n)
q2 = factor * 0.7 + np.random.normal(0, 0.6, n)
q3 = factor * 0.9 + np.random.normal(0, 0.4, n)

df = pd.DataFrame({'Q1': q1, 'Q2': q2, 'Q3': q3})

model_desc = "F =~ Q1 + Q2 + Q3"
model = semopy.Model(model_desc)
res = model.fit(df)
print(res)
stats = semopy.calc_stats(model)
print(stats.columns)
print(stats)

# Standardization
inspec = model.inspect(std_est=True)
print(inspec)
