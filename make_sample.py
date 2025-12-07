import pandas as pd
df = pd.read_csv('MHCLD_PUF_2023_clean.csv', nrows=100000)
df.to_csv('MHCLD_sample.csv', index=False)