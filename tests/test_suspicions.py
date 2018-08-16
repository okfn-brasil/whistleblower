import datetime as dt
from unittest import TestCase, mock

from whistleblower.suspicions import Suspicions as subject_class


class TestSuspicions(TestCase):
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
