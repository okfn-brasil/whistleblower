import os

import numpy as np
import pandas as pd

PATH = 'data'

dataset = pd.read_csv(os.path.join(PATH, 'reimbursements.xz'),
                      dtype={'applicant_id': np.str,
                             'cnpj_cpf': np.str,
                             'congressperson_id': np.str,
                             'subquota_number': np.str},
                      low_memory=False)
dataset['issue_date'] = pd.to_datetime(
    dataset['issue_date'], errors='coerce')
dataset = dataset.query('year == 2017')

companies = pd.read_csv(os.path.join(PATH, '2016-09-03-companies.xz'),
                        dtype={'cnpj': np.str},
                        low_memory=False)
companies['cnpj'] = companies['cnpj'].str.replace(r'\D', '')
companies['situation_date'] = pd.to_datetime(
    companies['situation_date'], errors='coerce')

dataset = dataset.merge(companies,
                        how='left',
                        left_on='cnpj_cpf',
                        right_on='cnpj')
del(companies)


suspicions = pd.read_csv(os.path.join(PATH, 'suspicions.xz'),
                         dtype={'applicant_id': np.str})
dataset = dataset.merge(suspicions)
del(suspicions)

rows = dataset.iloc[:, -6:-1].any(axis=1) \
    & dataset.congressperson_id.notnull()
dataset = dataset[rows].sort_values('total_net_value', ascending=False)
