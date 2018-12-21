# Needed to serialize and deserialize data
import json
from flask import request
# Import things from Flask that we need.
from accounting import app, db
from dateutil.parser import parse as date_parse
from models import Contact, Invoice, Policy, Payment

def to_json(o):
    if isinstance(o, list):
        return json.dumps(
            [i.to_dict() for i in o],
            default=str
        )
    return json.dumps(o, default=str)

# Routing for the server.
@app.route("/policies/search", methods=["GET"])
def search():
    query = request.args.get('query')
    query = "%{}%".format(query)
    policies = Policy.query\
        .filter(Policy.policy_number.ilike(query))\
        .all()

    agents = [p.agent_relation for p in policies]
    serialized = [p.to_dict() for p in policies]
    print(agents)
    # Replace agent id in policies dicts with objects
    for s, a in zip(serialized, agents):
        if s['agent'] is not None:
            s['agent'] = a.to_dict()

    return json.dumps(serialized, default=str)

@app.route("/policies/<id>/invoices")
def invoices(id):
    date = date_parse(
        request.args.get('date')
    )
    invoices = Invoice.query\
        .filter_by(policy_id=id)\
        .filter(Invoice.bill_date <= date)\
        .filter(Invoice.deleted == False)\
        .order_by(Invoice.bill_date)\
        .all()

    return to_json(invoices)

@app.route("/policies/<id>/payments")
def payments(id):
    payments = Payment.query\
        .filter_by(policy_id=id)\
        .all()

    return to_json(payments)

