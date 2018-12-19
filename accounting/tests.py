#!/user/bin/env python2.7

import unittest
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from accounting import db
from models import Contact, Invoice, Payment, Policy
from utils import PolicyAccounting

"""
#######################################################
Test Suite for Accounting
#######################################################
"""

class TestBillingSchedules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_agent = Contact('Test Agent', 'Agent')
        cls.test_insured = Contact('Test Insured', 'Named Insured')
        db.session.add(cls.test_agent)
        db.session.add(cls.test_insured)
        db.session.commit()

        cls.policy = Policy('Test Policy', date(2015, 1, 1), 1200)
        db.session.add(cls.policy)
        cls.policy.named_insured = cls.test_insured.id
        cls.policy.agent = cls.test_agent.id
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.delete(cls.test_insured)
        db.session.delete(cls.test_agent)
        db.session.delete(cls.policy)
        db.session.commit()

    def setUp(self):
        pass

    def tearDown(self):
        for invoice in self.policy.invoices:
            db.session.delete(invoice)
        db.session.commit()

    def test_annual_billing_schedule(self):
        self.policy.billing_schedule = "Annual"
        #No invoices currently exist
        self.assertFalse(self.policy.invoices)
        #Invoices should be made when the class is initiated
        pa = PolicyAccounting(self.policy.id)
        self.assertEquals(len(self.policy.invoices), 1)
        self.assertEquals(self.policy.invoices[0].amount_due, self.policy.annual_premium)

    def test_monthly_billing_schedule(self):
        self.policy.billing_schedule = "Monthly"
        #No invoices currently exist
        self.assertFalse(self.policy.invoices)
        #Invoices should be made when the class is initiated
        pa = PolicyAccounting(self.policy.id)
        self.assertEquals(len(self.policy.invoices), 12)
        self.assertEquals(self.policy.invoices[0].amount_due, self.policy.annual_premium / 12)
        # let's make sure the bill dates are correct
        true_bill_dates = set([
            date(2015, 1, 1),
            date(2015, 2, 1),
            date(2015, 3, 1),
            date(2015, 4, 1),
            date(2015, 5, 1),
            date(2015, 6, 1),
            date(2015, 7, 1),
            date(2015, 8, 1),
            date(2015, 9, 1),
            date(2015, 10, 1),
            date(2015, 11, 1),
            date(2015, 12, 1)
        ])

        bill_dates = set([invoice.bill_date for invoice in self.policy.invoices])
        self.assertEquals(true_bill_dates, bill_dates)

        # now we check due dates
        true_due_dates = set([
            x + relativedelta(months=1) for x in true_bill_dates
        ])

        due_dates = set([invoice.due_date for invoice in self.policy.invoices])
        self.assertEquals(true_due_dates, due_dates)

        # Finally we check cancel dates
        true_cancel_dates = set([
            x + relativedelta(months=1, days=14) for x in true_bill_dates
        ])

        cancel_dates = set([invoice.cancel_date for invoice in self.policy.invoices])
        self.assertEquals(true_cancel_dates, cancel_dates)

class TestReturnAccountBalance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_agent = Contact('Test Agent', 'Agent')
        cls.test_insured = Contact('Test Insured', 'Named Insured')
        db.session.add(cls.test_agent)
        db.session.add(cls.test_insured)
        db.session.commit()

        cls.policy = Policy('Test Policy', date(2015, 1, 1), 1200)
        cls.policy.named_insured = cls.test_insured.id
        cls.policy.agent = cls.test_agent.id
        db.session.add(cls.policy)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.delete(cls.test_insured)
        db.session.delete(cls.test_agent)
        db.session.delete(cls.policy)
        db.session.commit()

    def setUp(self):
        self.payments = []

    def tearDown(self):
        for invoice in self.policy.invoices:
            db.session.delete(invoice)
        for payment in self.payments:
            db.session.delete(payment)
        db.session.commit()

    def test_annual_on_eff_date(self):
        self.policy.billing_schedule = "Annual"
        pa = PolicyAccounting(self.policy.id)
        self.assertEquals(pa.return_account_balance(date_cursor=self.policy.effective_date), 1200)

    def test_quarterly_on_eff_date(self):
        self.policy.billing_schedule = "Quarterly"
        pa = PolicyAccounting(self.policy.id)
        self.assertEquals(pa.return_account_balance(date_cursor=self.policy.effective_date), 300)

    def test_quarterly_on_last_installment_bill_date(self):
        self.policy.billing_schedule = "Quarterly"
        pa = PolicyAccounting(self.policy.id)
        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .order_by(Invoice.bill_date).all()
        self.assertEquals(pa.return_account_balance(date_cursor=invoices[3].bill_date), 1200)

    def test_quarterly_on_second_installment_bill_date_with_full_payment(self):
        self.policy.billing_schedule = "Quarterly"
        pa = PolicyAccounting(self.policy.id)
        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .order_by(Invoice.bill_date).all()
        self.payments.append(pa.make_payment(contact_id=self.policy.named_insured,
                                             date_cursor=invoices[1].bill_date, amount=600))
        self.assertEquals(pa.return_account_balance(date_cursor=invoices[1].bill_date), 0)


class TestEvaluateCancellationPending(unittest.TestCase):
    """
    Tests for PolicyAccount.evaluate_cancellation_pending_due_to_non_pay
    """

    @classmethod
    def setUpClass(cls):
        cls.test_agent = Contact('Test Agent', 'Agent')
        cls.test_insured = Contact('Test Insured', 'Named Insured')
        db.session.add(cls.test_agent)
        db.session.add(cls.test_insured)
        db.session.commit()

        cls.policy = Policy('Test Policy', date(2015, 1, 1), 1200)
        cls.policy.billing_schedule = "Monthly"
        cls.policy.named_insured = cls.test_insured.id
        cls.policy.agent = cls.test_agent.id
        db.session.add(cls.policy)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.delete(cls.test_insured)
        db.session.delete(cls.test_agent)
        db.session.delete(cls.policy)
        db.session.commit()

    def setUp(self):
        self.payments = []

    def tearDown(self):
        for invoice in self.policy.invoices:
            db.session.delete(invoice)
        for payment in self.payments:
            db.session.delete(payment)
        db.session.commit()

    def test_good_standing_no_payment(self):
        """
        Test the method when the account is in good standing and no payment
        has been made.
        """
        pa = PolicyAccounting(self.policy.id);

        # Note that on 2015/1/2 the account is in good standing even 
        # when no payment has been made
        d = date(2015, 1, 10)
        
        self.assertFalse(
            pa.evaluate_cancellation_pending_due_to_non_pay(date_cursor=d)
        )

    def test_good_standing_payment(self):
        """
        Test the method when the account is in good standing and a payment
        has been made
        """
        pa = PolicyAccounting(self.policy.id);
        self.payments.append(pa.make_payment(contact_id=self.policy.named_insured,
                                             date_cursor=date(2015, 1, 15), 
                                             amount=100))

        # First billing cycle should be covered by above payment, so
        # a date in the middle of the second cycle should be good
        d = date(2015, 2, 10)
        # print(pa.return_account_balance(d))
        self.assertFalse(
            pa.evaluate_cancellation_pending_due_to_non_pay(date_cursor=d)
        )

    def test_pending_no_payment_before_cancellation(self):
        """
        Test the method when the account is pending cancellation and before 
        cancellation date has been reached.
        """
        pa = PolicyAccounting(self.policy.id)
        # No payment made and we are past the due date, but before cancellation
        d = date(2015, 2, 10)
        self.assertTrue(
            pa.evaluate_cancellation_pending_due_to_non_pay(date_cursor=d)
        )

    def test_pending_payment_before_cancellation(self):
        """
        Test the method when a payment has been made on the invoice 
        but the account is pending cancellation and before 
        cancellation date has been reached.
        """
        pa = PolicyAccounting(self.policy.id)
        self.payments.append(pa.make_payment(contact_id=self.policy.named_insured,
                                             date_cursor=date(2015, 1, 15), 
                                             amount=100))

        # Second payment made and we are past the due date, but before cancellation
        d = date(2015, 3, 10)
        self.assertTrue(
            pa.evaluate_cancellation_pending_due_to_non_pay(date_cursor=d)
        )


    def test_pending_no_payment_before_cancellation_edge(self):
        """
        Same as above, but testing edge case of date_cursor == due_date
        """
        pa = PolicyAccounting(self.policy.id)
        # No payment made and we are past the due date, but before cancellation
        d = date(2015, 2, 1)
        self.assertTrue(
            pa.evaluate_cancellation_pending_due_to_non_pay(date_cursor=d)
        )

    def test_pending_payment_before_cancellation_edge(self):
        """
        Same as above, but when an insufficient payment has been made
        """
        pa = PolicyAccounting(self.policy.id)
        self.payments.append(pa.make_payment(contact_id=self.policy.named_insured,
                                             date_cursor=date(2015, 1, 15), 
                                             amount=100))
        # No payment made and we are past the due date, but before cancellation
        d = date(2015, 3, 1)
        self.assertTrue(
            pa.evaluate_cancellation_pending_due_to_non_pay(date_cursor=d)
        )

    def test_pending_no_payment_after_cancellation(self):
        """
        Test the method when the account is pending cancellation and after
        cancellation date has been reached.
        """
        pa = PolicyAccounting(self.policy.id)
        # No payment made and we are past the due date, but before cancellation
        d = date(2015, 2, 15)
        self.assertTrue(
            pa.evaluate_cancellation_pending_due_to_non_pay(date_cursor=d)
        )

    def test_pending_no_payment_after_cancellation_edge(self):
        """
        Test the method when the account is pending cancellation and after
        cancellation date has been reached.
        """
        pa = PolicyAccounting(self.policy.id)
        # No payment made and we are past the due date, but before cancellation
        d = date(2015, 2, 14)
        self.assertTrue(
            pa.evaluate_cancellation_pending_due_to_non_pay(date_cursor=d)
        )

    


