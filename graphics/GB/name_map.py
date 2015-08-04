import pandas as pd
gb = pd.read_csv('GB.csv')
mapping = gb[['NAME', 'CODE']]
mapping['uname'] = mapping['NAME'].apply(lambda x: x.lower().replace(' district', '').replace(' london boro', '').replace('city of ', '').replace(' (b)', '').split(' - ')[-1].replace(' ', '-'))
mapping.to_csv('mapping.csv', index=False)
