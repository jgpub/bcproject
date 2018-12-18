#!/user/bin/env python2.7

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from accounting import db
from models import Contact, Invoice, Payment, Policy

"""
#######################################################
This is the base code for the engineer project.
#######################################################
"""

class PolicyAccounting(object):
    """
     Each policy has its own instance of accounting.
    """
    def __init__(self, policy_id):
        """
        Constructor for PolicyAccounting class
        """

        #  Pull the appropriate policy from DB
        self.policy = Policy.query.filter_by(id=policy_id).one()

        if not self.policy.invoices:
            self.make_invoices()

    def return_account_balance(self, date_cursor=None):
        """
        Calculate account balance by computing the total invoices due
        for the relevant policy and subtracting the sum of the payments
        made on the policy.   If date_cursor is not specified, the 
        calculation is made consider all invoices and payments made on
        the policy up to (and including) the current date.  However, if 
        a valid date_cursor is supplied, only invoices and payments 
        occurring before the given date will be considered.  This is
        useful in calculating, for instance, the amount that remains to
        be paid on the entire policy.
        """
        if not date_cursor:
            date_cursor = datetime.now().date()

        # Pull invoices for the policy that occurred at or before the date_cursor.
        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.bill_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()

        # calculate the total invoiced
        due_now = 0
        for invoice in invoices:
            due_now += invoice.amount_due

        # Pull payments for the policy that occurred at or before the date_cursor;
        payments = Payment.query.filter_by(policy_id=self.policy.id)\
                                .filter(Payment.transaction_date <= date_cursor)\
                                .all()

        # calculate the total paid.
        for payment in payments:
            due_now -= payment.amount_paid

        return due_now

    def make_payment(self, contact_id=None, date_cursor=None, amount=0):
        """
        Logs in the database a payment made.  If no date_cursor is supplied,
        the current date is assumed to be the date on which payment was made.
        For logging payments retroactively or preemptively, a date_cursor can
        be specified. 

        The contact_id is used to specify who is making the payment.  If it is not
        specified, it is assumed to be the name of the policy holder.
        """
        if not date_cursor:
            date_cursor = datetime.now().date()

        if not contact_id:
            try:
                contact_id = self.policy.named_insured
            except:
                pass

        payment = Payment(self.policy.id,
                          contact_id,
                          amount,
                          date_cursor)
        db.session.add(payment)
        db.session.commit()

        return payment

    def evaluate_cancellation_pending_due_to_non_pay(self, date_cursor=None):
        """
         If this function returns true, an invoice
         on a policy has passed the due date without
         being paid in full. However, it has not necessarily
         made it to the cancel_date yet.
        """
        pass

    def evaluate_cancel(self, date_cursor=None):
        """
        Determines whether a policy should be cancelled due to non-payment from 
        the start of the policy up to date_cursor, which is taken to be the current
        date if not specified by the caller.
        """
        if not date_cursor:
            date_cursor = datetime.now().date()

        # pull all invoices up to and including date_cursor for the relevant
        # policy
        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.cancel_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()

        # If any invoice exists for which there was a positive balance by the
        # cancel date, then the policy can be cancelled
        for invoice in invoices:
            if not self.return_account_balance(invoice.cancel_date):
                continue
            else:
                print "THIS POLICY SHOULD HAVE CANCELED"
                break
        else:
            print "THIS POLICY SHOULD NOT CANCEL"


    def make_invoices(self):
        """
        Generates invoices for the PolicyAccount object's policy.  Note that all invoices
        are generated and stored in the database at once, rather than doing so period-by-period.
        """
        # Clear any existing invoice.
        for invoice in self.policy.invoices:
            invoice.delete()

        # Set the number of months associated with each billing schedule.
        billing_schedules = {'Annual': None, 'Two-Pay': 2, 'Semi-Annual': 3, 'Quarterly': 4, 'Monthly': 12}

        invoices = []

        # There is always at least one invoice, so we create that up front, assuming that it is for
        # a yearly billing schedule.  self.policy.amount_due is liable to change later in this function
        # if a different billing schedule is employed.
        first_invoice = Invoice(self.policy.id,
                                self.policy.effective_date, #bill_date
                                self.policy.effective_date + relativedelta(months=1), #due
                                self.policy.effective_date + relativedelta(months=1, days=14), #cancel
                                self.policy.annual_premium)
        invoices.append(first_invoice)

        # if the policy employs an annual billing scedule, there are no more invoices to create
        if self.policy.billing_schedule == "Annual":
            pass
        elif self.policy.billing_schedule in ["Two-Pay", "Semi-Annual", "Quarterly", "Monthly"]:
            # Calculate billing periodicity (number of months between billing cycles)
            # and billing frequency (how many times per year) depending on the policy's
            # billing schedule.
            billing_periodicity = billing_schedules.get(self.policy.billing_schedule)
            billing_frequency = 12 / billing_periodicity

            # Adjust the first invoice's amount due appropriately.
            first_invoice.amount_due = first_invoice.amount_due / billing_periodicity
            # For each remaining billing cycle...
            for i in range(1, billing_periodicity):
                # calculate date of invoice
                months_after_eff_date = i * billing_frequency
                bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)

                # create the invoice!
                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  self.policy.annual_premium / billing_periodicity)
                invoices.append(invoice)
        else:
            print "You have chosen a bad billing schedule."

        # Save the invoices to the Database.
        for invoice in invoices:
            db.session.add(invoice)
        db.session.commit()

################################
# The functions below are for the db and 
# shouldn't need to be edited.
################################
def build_or_refresh_db():
    db.drop_all()
    db.create_all()
    insert_data()
    print "DB Ready!"

def insert_data():
    #Contacts
    contacts = []
    mary_sue_client = Contact('Mary Sue', "Client")
    contacts.append(mary_sue_client)
    john_doe_agent = Contact('John Doe', 'Agent')
    contacts.append(john_doe_agent)
    john_doe_insured = Contact('John Doe', 'Named Insured')
    contacts.append(john_doe_insured)
    bob_smith = Contact('Bob Smith', 'Agent')
    contacts.append(bob_smith)
    anna_white = Contact('Anna White', 'Named Insured')
    contacts.append(anna_white)
    joe_lee = Contact('Joe Lee', 'Agent')
    contacts.append(joe_lee)
    ryan_bucket = Contact('Ryan Bucket', 'Named Insured')
    contacts.append(ryan_bucket)

    for contact in contacts:
        db.session.add(contact)
    db.session.commit()

    policies = []
    p1 = Policy('Policy One', date(2015, 1, 1), 365)
    p1.billing_schedule = 'Annual'
    p1.agent = bob_smith.id
    policies.append(p1)

    p2 = Policy('Policy Two', date(2015, 2, 1), 1600)
    p2.billing_schedule = 'Quarterly'
    p2.named_insured = anna_white.id
    p2.agent = joe_lee.id
    policies.append(p2)

    p3 = Policy('Policy Three', date(2015, 1, 1), 1200)
    p3.billing_schedule = 'Monthly'
    p3.named_insured = ryan_bucket.id
    p3.agent = john_doe_agent.id
    policies.append(p3)

    p4 = Policy("Policy Four", date(2015, 2, 1), 500)
    p4.billing_schedule = 'Two-Pay'
    p4.named_insured = ryan_bucket.id
    p4.agent = john_doe_agent.id
    policies.append(p4)

    for policy in policies:
        db.session.add(policy)
    db.session.commit()

    for policy in policies:
        PolicyAccounting(policy.id)

    payment_for_p2 = Payment(p2.id, anna_white.id, 400, date(2015, 2, 1))
    db.session.add(payment_for_p2)
    db.session.commit()

