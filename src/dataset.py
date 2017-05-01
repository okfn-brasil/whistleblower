import os
from urllib.request import urlretrieve
from zipfile import ZipFile

import numpy as np
import pandas as pd
from serenata_toolbox.xml2csv import convert_xml_to_csv

PATH = 'data'
URL = 'http://www.camara.gov.br/cotas/AnoAtual.zip'


class Reimbursements:

    FILE_BASE_NAME = 'reimbursements.xz'

    CSV_PARAMS = {
        'compression': 'xz',
        'encoding': 'utf-8',
        'index': False
    }
    DTYPE = {
        'applicant_id': np.str,
        'batch_number': np.str,
        'cnpj_cpf': np.str,
        'congressperson_document': np.str,
        'congressperson_id': np.str,
        'document_id': np.str,
        'document_number': np.str,
        'document_type': np.str,
        'leg_of_the_trip': np.str,
        'passenger': np.str,
        'reimbursement_number': np.str,
        'subquota_group_description': np.str,
        'subquota_group_id': np.str,
        'subquota_number': np.str,
        'term_id': np.str,
    }

    def __init__(self, path):
        self.path = path

    def read_csv(self, name):
        filepath = os.path.join(self.path, name)
        print('Loading {}…'.format(name))
        return pd.read_csv(filepath, dtype=self.DTYPE)

    @property
    def receipts(self):
        print('Merging all datasets…')
        datasets = ['reimbursements.xz']
        data = (self.read_csv(name) for name in datasets)
        return pd.concat(data)

    @staticmethod
    def aggregate(grouped, old, new, func):
        """
        Gets a GroupBy object, aggregates it on `old` using `func`, then rename
        the series name from `old` to `new`, returning a DataFrame.
        """
        output = grouped[old].agg(func)
        output = output.rename(index=new, inplace=True)
        return output.reset_index()

    def group(self, receipts):
        print('Dropping rows without document_value or reimbursement_number…')
        subset = ('document_value', 'reimbursement_number')
        receipts = receipts.dropna(subset=subset)
        groupby_keys = ('year', 'applicant_id', 'document_id')
        receipts = receipts.dropna(subset=subset + groupby_keys)

        print('Grouping dataset by applicant_id, document_id and year…')
        grouped = receipts.groupby(groupby_keys)

        print('Gathering all reimbursement numbers together…')
        numbers = self.aggregate(
            grouped,
            'reimbursement_number',
            'reimbursement_numbers',
            lambda x: ', '.join(set(x))
        )

        print('Summing all net values together…')
        net_total = self.aggregate(
            grouped,
            'net_value',
            'total_net_value',
            np.sum
        )

        print('Summing all reimbursement values together…')
        total = self.aggregate(
            grouped,
            'reimbursement_value',
            'reimbursement_value_total',
            np.sum
        )

        print('Generating the new dataset…')
        final = pd.merge(
            pd.merge(pd.merge(total, net_total, on=groupby_keys), numbers, on=groupby_keys),
            receipts,
            on=groupby_keys
        )
        final = final.drop_duplicates(subset=groupby_keys)
        final.rename(columns={'net_value': 'net_values',
                              'reimbursement_value': 'reimbursement_values'},
                     inplace=True)
        final = final.drop('reimbursement_number', 1)
        return final

    @staticmethod
    def unique_str(strings):
        return ', '.join(set(strings))

    def write_reimbursement_file(self, receipts):
        print('Casting changes to a new DataFrame…')
        df = pd.DataFrame(data=receipts)

        print('Writing it to file…')
        filepath = os.path.join(self.path, self.FILE_BASE_NAME)
        df.to_csv(filepath, **self.CSV_PARAMS)

        print('Done.')


def fetch():
    urlretrieve('http://www2.camara.leg.br/transparencia/cota-para-exercicio-da-atividade-parlamentar/explicacoes-sobre-o-formato-dos-arquivos-xml',
                os.path.join(PATH, 'datasets-format.html'))
    zip_file_path = os.path.join(PATH, 'AnoAtual')
    urlretrieve(URL, zip_file_path)
    zip_file = ZipFile(zip_file_path, 'r')
    zip_file.extractall(PATH)
    zip_file.close()
    os.remove(zip_file_path)


def convert_to_csv():
    for filename in ['AnoAtual']:
        xml_path = os.path.join(PATH, '{}.xml'.format(filename))
        csv_path = xml_path.replace('.xml', '.csv')
        convert_xml_to_csv(xml_path, csv_path)

def translate():
    data = pd.read_csv(os.path.join(PATH, 'AnoAtual.csv'),
                       dtype={'idedocumento': np.str,
                              'idecadastro': np.str,
                              'nucarteiraparlamentar': np.str,
                              'codlegislatura': np.str,
                              'txtcnpjcpf': np.str,
                              'numressarcimento': np.str})
    data.rename(columns={
        'idedocumento': 'document_id',
        'txnomeparlamentar': 'congressperson_name',
        'idecadastro': 'congressperson_id',
        'nucarteiraparlamentar': 'congressperson_document',
        'nulegislatura': 'term',
        'sguf': 'state',
        'sgpartido': 'party',
        'codlegislatura': 'term_id',
        'numsubcota': 'subquota_number',
        'txtdescricao': 'subquota_description',
        'numespecificacaosubcota': 'subquota_group_id',
        'txtdescricaoespecificacao': 'subquota_group_description',
        'txtfornecedor': 'supplier',
        'txtcnpjcpf': 'cnpj_cpf',
        'txtnumero': 'document_number',
        'indtipodocumento': 'document_type',
        'datemissao': 'issue_date',
        'vlrdocumento': 'document_value',
        'vlrglosa': 'remark_value',
        'vlrliquido': 'net_value',
        'nummes': 'month',
        'numano': 'year',
        'numparcela': 'installment',
        'txtpassageiro': 'passenger',
        'txttrecho': 'leg_of_the_trip',
        'numlote': 'batch_number',
        'numressarcimento': 'reimbursement_number',
        'vlrrestituicao': 'reimbursement_value',
        'nudeputadoid': 'applicant_id',
    }, inplace=True)
    data['subquota_description'] = \
        data['subquota_description'].astype('category')

    categories = {
        'ASSINATURA DE PUBLICAÇÕES':
            'Publication subscriptions',
        'COMBUSTÍVEIS E LUBRIFICANTES.':
            'Fuels and lubricants',
        'CONSULTORIAS, PESQUISAS E TRABALHOS TÉCNICOS.':
            'Consultancy, research and technical work',
        'DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR.':
            'Publicity of parliamentary activity',
        'Emissão Bilhete Aéreo':
            'Flight ticket issue',
        'FORNECIMENTO DE ALIMENTAÇÃO DO PARLAMENTAR':
            'Congressperson meal',
        'HOSPEDAGEM ,EXCETO DO PARLAMENTAR NO DISTRITO FEDERAL.':
            'Lodging, except for congressperson from Distrito Federal',
        'LOCAÇÃO OU FRETAMENTO DE AERONAVES':
            'Aircraft renting or charter of aircraft',
        'LOCAÇÃO OU FRETAMENTO DE EMBARCAÇÕES':
            'Watercraft renting or charter',
        'LOCAÇÃO OU FRETAMENTO DE VEÍCULOS AUTOMOTORES':
            'Automotive vehicle renting or charter',
        'MANUTENÇÃO DE ESCRITÓRIO DE APOIO À ATIVIDADE PARLAMENTAR':
            'Maintenance of office supporting parliamentary activity',
        'PARTICIPAÇÃO EM CURSO, PALESTRA OU EVENTO SIMILAR':
            'Participation in course, talk or similar event',
        'PASSAGENS AÉREAS':
            'Flight tickets',
        'PASSAGENS TERRESTRES, MARÍTIMAS OU FLUVIAIS':
            'Terrestrial, maritime and fluvial tickets',
        'SERVIÇO DE SEGURANÇA PRESTADO POR EMPRESA ESPECIALIZADA.':
            'Security service provided by specialized company',
        'SERVIÇO DE TÁXI, PEDÁGIO E ESTACIONAMENTO':
            'Taxi, toll and parking',
        'SERVIÇOS POSTAIS':
            'Postal services',
        'TELEFONIA':
            'Telecommunication',
        'AQUISIÇÃO DE MATERIAL DE ESCRITÓRIO.':
            'Purchase of office supplies',
        'AQUISIÇÃO OU LOC. DE SOFTWARE; SERV. POSTAIS; ASS.':
            'Software purchase or renting; Postal services; Subscriptions',
        'LOCAÇÃO DE VEÍCULOS AUTOMOTORES OU FRETAMENTO DE EMBARCAÇÕES ':
            'Automotive vehicle renting or watercraft charter',
        'LOCOMOÇÃO, ALIMENTAÇÃO E  HOSPEDAGEM':
            'Locomotion, meal and lodging',
    }
    categories = [categories[cat] for cat in data['subquota_description'].cat.categories]
    data['subquota_description'].cat.rename_categories(categories, inplace=True)
    data.to_csv(os.path.join(PATH, 'reimbursements.xz'),
                compression='xz',
                index=False,
                encoding='utf-8')

def clean():
    reimbursements = Reimbursements(PATH)
    dataset = reimbursements.group(reimbursements.receipts)
    reimbursements.write_reimbursement_file(dataset)

if __name__ == '__main__':
    fetch()
    convert_to_csv()
    translate()
    clean()
