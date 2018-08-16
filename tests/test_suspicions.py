import datetime as dt
from unittest import TestCase, mock

from whistleblower.suspicions import Suspicions as subject_class


class TestSuspicions(TestCase):
    @mock.patch.object(subject_class, 'fetch', new_callable=mock.PropertyMock)
    @mock.patch('whistleblower.suspicions.datasets')
    @mock.patch('whistleblower.suspicions.pd')
    def test_all(self, pd_mock, datasets_mock, fetch_mock):
        subject_class().all()
        fetch_mock.assert_called_once()

    @mock.patch('whistleblower.suspicions.pd')
    def test_reimbursements(self, pd_mock):
        path = 'data/reimbursements-{}.csv'
        subject = subject_class(2010)
        subject.reimbursements()
        pd_mock.read_csv.assert_called_with(
            path.format(2010), dtype=mock.ANY, low_memory=False)

        subject = subject_class()
        subject.reimbursements()
        pd_mock.read_csv.assert_called_with(
            path.format(dt.datetime.today().year), dtype=mock.ANY, low_memory=False)
