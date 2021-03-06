from accounting import db
# from sqlalchemy.ext.declarative import declarative_base
# 
# DeclarativeBase = declarative_base()

class Serializable(object):
    def to_dict(self, custom_cols=None):
        try:
            cols = custom_cols if custom_cols else self.serializable_cols
            return {
                c: getattr(self, c)
                for c in cols
            }
        except AttributeError:
            raise RuntimeError("Error in to_dict.  Make sure class "\
                "implementing Serializable has 'serializable_cols' class "\
                "variable and that it contains valid columns.  If passing "\
                "custom_cols, make sure the collection contains valid columns")

class Policy(db.Model, Serializable):
    __tablename__ = 'policies'

    __table_args__ = {}

    serializable_cols = {
        'id',
        'policy_number',
        'effective_date',
        'status',
        'billing_schedule',
        'annual_premium',
        'named_insured',
        'agent'
    }

    #column definitions
    id = db.Column(u'id', db.INTEGER(), primary_key=True, nullable=False)
    policy_number = db.Column(u'policy_number', db.VARCHAR(length=128), nullable=False)
    effective_date = db.Column(u'effective_date', db.DATE(), nullable=False)
    status = db.Column(u'status', db.Enum(u'Active', u'Canceled', u'Expired'), default=u'Active', nullable=False)
    billing_schedule = db.Column(u'billing_schedule', db.Enum(u'Annual', u'Two-Pay', u'Quarterly', u'Monthly'), default=u'Annual', nullable=False)
    annual_premium = db.Column(u'annual_premium', db.INTEGER(), nullable=False)
    named_insured = db.Column(u'named_insured', db.INTEGER(), db.ForeignKey('contacts.id'))
    agent = db.Column(u'agent', db.INTEGER(), db.ForeignKey('contacts.id'))

    def __init__(self, policy_number, effective_date, annual_premium):
        self.policy_number = policy_number
        self.effective_date = effective_date
        self.annual_premium = annual_premium

    @property
    def cancelled(self):
        return self.cancellation is not None

    invoices = db.relation('Invoice', primaryjoin="Invoice.policy_id==Policy.id")
    cancellation = db.relation('PolicyCancellation', backref="policy", uselist=False)
    agent_relation = db.relation('Contact', primaryjoin="Contact.id == Policy.agent", uselist=False)
    named_insured_relation = db.relation('Contact', primaryjoin="Contact.id == Policy.named_insured", uselist=False)


class PolicyCancellation(db.Model):
    __tablename__ = 'policy_cancellations'

    __table_args__ = {}

    # column definitions
    policy_id = db.Column(u'policy_id', db.ForeignKey('policies.id'), primary_key=True)
    # Why was this policy cancelled
    reason = db.Column(u'reason', db.Enum(u'Nonpayment', u'Underwriting', u'Client'), nullable=False)
    date = db.Column(u'date', db.DATE(), nullable=False)
    notes = db.Column(u'notes', db.VARCHAR(length=256), nullable=False, default='')

    def __init__(self, policy_id, reason, date, notes=None):
        self.policy_id = policy_id
        self.reason = reason
        self.date = date
        if notes is not None:
            self.notes = notes


class Contact(db.Model, Serializable):
    __tablename__ = 'contacts'

    __table_args__ = {}

    serializable_cols = {
        'id',
        'name',
        'role'
    }

    #column definitions
    id = db.Column(u'id', db.INTEGER(), primary_key=True, nullable=False)
    name = db.Column(u'name', db.VARCHAR(length=128), nullable=False)
    role = db.Column(u'role', db.Enum(u'Named Insured', u'Agent', u'Client'), nullable=False)

    def __init__(self, name, role):
        self.name = name
        self.role = role


class Invoice(db.Model, Serializable):
    __tablename__ = 'invoices'

    __table_args__ = {}

    serializable_cols = {
        "id",
        "policy_id",
        "bill_date",
        "due_date",
        "cancel_date",
        "amount_due",
        "deleted"
    }
    #column definitions
    id = db.Column(u'id', db.INTEGER(), primary_key=True, nullable=False)
    policy_id = db.Column(u'policy_id', db.INTEGER(), db.ForeignKey('policies.id'), nullable=False)
    bill_date = db.Column(u'bill_date', db.DATE(), nullable=False)
    due_date = db.Column(u'due_date', db.DATE(), nullable=False)
    cancel_date = db.Column(u'cancel_date', db.DATE(), nullable=False)
    amount_due = db.Column(u'amount_due', db.INTEGER(), nullable=False)
    deleted = db.Column(u'deleted', db.Boolean, default=False, server_default='0', nullable=False)

    def __init__(self, policy_id, bill_date, due_date, cancel_date, amount_due):
        self.policy_id = policy_id
        self.bill_date = bill_date
        self.due_date = due_date
        self.cancel_date = cancel_date
        self.amount_due = amount_due


class Payment(db.Model, Serializable):
    __tablename__ = 'payments'

    __table_args__ = {}

    serializable_cols = {
        "id",
        "policy_id",
        "contact_id",
        "amount_paid",
        "transaction_date"
    }
    #column definitions
    id = db.Column(u'id', db.INTEGER(), primary_key=True, nullable=False)
    policy_id = db.Column(u'policy_id', db.INTEGER(), db.ForeignKey('policies.id'), nullable=False)
    contact_id = db.Column(u'contact_id', db.INTEGER(), db.ForeignKey('contacts.id'), nullable=False)
    amount_paid = db.Column(u'amount_paid', db.INTEGER(), nullable=False)
    transaction_date = db.Column(u'transaction_date', db.DATE(), nullable=False)

    def __init__(self, policy_id, contact_id, amount_paid, transaction_date):
        self.policy_id = policy_id
        self.contact_id = contact_id
        self.amount_paid = amount_paid
        self.transaction_date = transaction_date
