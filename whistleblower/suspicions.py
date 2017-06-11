import os

import numpy as np
import pandas as pd

DATA_PATH = 'data'


class Suspicions:
    """
    Load suspicious reimbursements.
    """

    SOCIAL_ACCOUNTS_FILE = '2017-06-11-congresspeople-social-accounts.xz'

    def __init__(self, data_path=DATA_PATH):
        self.data_path = data_path

    def all(self):
        dataset = self.__reimbursements()
        dataset = dataset.merge(self.__companies(),
                                how='left',
                                left_on='cnpj_cpf',
                                right_on='cnpj')
        dataset = dataset.merge(self.__suspicions())
        dataset = dataset.merge(self.__twitter_profiles(),
                                on='congressperson_id')
        # rows = dataset.iloc[:, -6:].any(axis=1) \
        #     & dataset.congressperson_id.notnull()
        suspicious_cols = ['meal_price_outlier',
                           'suspicious_traveled_speed_day']
        rows = dataset.loc[:, suspicious_cols].any(axis=1) \
            & dataset.congressperson_id.notnull()
        return dataset[rows].sort_values('total_net_value', ascending=False)

    def __reimbursements(self):
        dataset = pd.read_csv(os.path.join(self.data_path, 'reimbursements.xz'),
                              dtype={'applicant_id': np.str,
                                     'cnpj_cpf': np.str,
                                     'congressperson_id': np.str,
                                     'subquota_number': np.str},
                              low_memory=False)
        dataset['issue_date'] = pd.to_datetime(
            dataset['issue_date'], errors='coerce')
        dataset = dataset.query('year >= 2016')
        # dataset = dataset.query('term == 2015')
        return dataset

    def __companies(self):
        path = os.path.join(self.data_path, '2016-09-03-companies.xz')
        dataset = pd.read_csv(path, dtype={'cnpj': np.str}, low_memory=False)
        dataset['cnpj'] = dataset['cnpj'].str.replace(r'\D', '')
        dataset['situation_date'] = pd.to_datetime(
            dataset['situation_date'], errors='coerce')
        return dataset

    def __suspicions(self):
        return pd.read_csv(os.path.join(self.data_path, 'suspicions.xz'),
                           dtype={'applicant_id': np.str})

    def __twitter_profiles(self):
        path = os.path.join(self.data_path, self.SOCIAL_ACCOUNTS_FILE)
        dataset = pd.read_csv(path, dtype={'congressperson_id': np.str})
        cols = ['twitter_profile', 'secondary_twitter_profile']
        return dataset[dataset[cols].any(axis=1)]
