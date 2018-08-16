import datetime as dt
import os

import numpy as np
import pandas as pd

from serenata_toolbox import datasets

DATA_PATH = 'data'


class Suspicions:
    """
    Load suspicious reimbursements.
    """

    COMPANIES_FILE = '2016-09-03-companies.xz'
    CONGRESSPEOPLE_FILE = '2017-05-29-deputies.xz'
    SOCIAL_ACCOUNTS_FILE = '2018-02-05-congresspeople-social-accounts.xz'

    def __init__(self, year=None, data_path=DATA_PATH):
        self.year = year or dt.datetime.today().year
        self.data_path = data_path

    def fetch(self):
        datasets.fetch(self.COMPANIES_FILE, self.data_path)
        datasets.fetch(self.CONGRESSPEOPLE_FILE, self.data_path)
        datasets.fetch(self.SOCIAL_ACCOUNTS_FILE, self.data_path)

    def all(self):
        dataset = self.reimbursements()
        dataset = dataset.merge(self.__companies(),
                                how='left',
                                left_on='cnpj_cpf',
                                right_on='cnpj',
                                suffixes=('', '_company'))
        dataset = dataset.merge(self.__suspicions(),
                                suffixes=('', '_suspicion'))
        dataset = dataset.merge(self.__social_accounts(),
                                how='left',
                                on='congressperson_id',
                                suffixes=('', '_social_account'))
        dataset = dataset.merge(self.__congresspeople(),
                                how='left',
                                on='congressperson_id',
                                suffixes=('', '_congressperson'))
        suspicious_cols = ['meal_price_outlier',
                           'suspicious_traveled_speed_day']
        rows = dataset.loc[:, suspicious_cols].any(axis=1) \
            & dataset['congressperson_id'].notnull()
        return dataset.loc[rows, dataset.notnull().any()]

    def reimbursements(self):
        path = os.path.join(self.data_path, 'reimbursements-{}.csv'.format(self.year))
        dataset = pd.read_csv(path,
                              dtype={'applicant_id': np.str,
                                     'cnpj_cpf': np.str,
                                     'congressperson_id': np.str,
                                     'subquota_number': np.str},
                              low_memory=False)
        dataset['issue_date'] = pd.to_datetime(
            dataset['issue_date'], errors='coerce')
        return dataset

    def __companies(self):
        path = os.path.join(self.data_path, self.COMPANIES_FILE)
        dataset = pd.read_csv(path, dtype={'cnpj': np.str}, low_memory=False)
        dataset['cnpj'] = dataset['cnpj'].str.replace(r'\D', '')
        dataset['situation_date'] = pd.to_datetime(
            dataset['situation_date'], errors='coerce')
        return dataset.iloc[:, :-2]  # Drop duplicated columns

    def __suspicions(self):
        return pd.read_csv(os.path.join(self.data_path, 'suspicions.xz'),
                           dtype={'applicant_id': np.str})

    def __social_accounts(self):
        path = os.path.join(self.data_path, self.SOCIAL_ACCOUNTS_FILE)
        return pd.read_csv(path, dtype={'congressperson_id': np.str})

    def __congresspeople(self):
        path = os.path.join(self.data_path, self.CONGRESSPEOPLE_FILE)
        return pd.read_csv(path, dtype={'congressperson_id': np.str})
