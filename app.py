from flask import Flask, redirect, url_for, flash, render_template, request
from static.forms import PersonForm, BikeForm, ContractForm, ReturnForm, FindContractForm
from pymongo import MongoClient
from datetime import datetime
from dateutil.relativedelta import relativedelta
from bson.objectid import ObjectId
from config import db_user, db_pwd, db_host, db_port, secret_key

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key


def get_collection(collection):
    client = MongoClient(f"mongodb://{db_user}:{db_pwd}@{db_host}:{db_port}")
    db = client["becycleDB"]
    return db[collection]


def add_person_and_redirect_to_bike(person):
    persons = get_collection("persons")
    person_id = persons.insert_one(person).inserted_id
    return redirect(url_for('bike', personId=person_id))


def add_bike_and_redirect_to_contract(bike, person_id):
    bikes = get_collection("bikes")
    bike_id = bikes.insert_one(bike).inserted_id
    return redirect(url_for('newcontract', bikeId=bike_id, personId=person_id))


@app.route('/')
@app.route('/index')
def hello_world():  # put application's code here
    return render_template("index.html")


@app.route('/newrental', methods=["GET"])
def newrental():
    return redirect(url_for('person'))


@app.route('/person', methods=["GET", "POST"])
def person():
    form = PersonForm()
    if form.validate_on_submit():
        person = {"firstName": form.firstName.data, "lastName": form.lastName.data, "emailAddress": form.emailAddress.data}
        persons = get_collection("persons")

        filter = {"$or": [{"firstName": person["firstName"]}, {"lastName": person["lastName"]}, {"emailAddress": person["emailAddress"]}]}

        num_potential_matches = persons.count_documents(filter)

        if num_potential_matches == 0:
            return add_person_and_redirect_to_bike(person)
        else:
            cursor = persons.find(filter)
            potential_matches = []
            for doc in cursor:
                potential_matches.append({"firstName": doc["firstName"], "lastName": doc["lastName"], "emailAddress": doc["emailAddress"], "id": doc["_id"]})
            return render_template('chooseLendeeForRental.html', potentialMatches=potential_matches, originalData=person)

    else:
        return render_template('lendeeDetails.html', form=form)


@app.route('/addperson', methods=["GET"])
def add_person():
    first_name = request.args["firstName"]
    last_name = request.args["lastName"]
    email_address = request.args["emailAddress"]
    person = {"firstName": first_name, "lastName": last_name, "emailAddress": email_address}

    return add_person_and_redirect_to_bike(person)


@app.route('/bike', methods=["GET", "POST"])
def bike():
    form = BikeForm()
    person_id = ObjectId(request.args["personId"])
    if form.validate_on_submit():
        bike = {"make": form.make.data, "model": form.model.data, "colour": form.colour.data, "decals": form.decals.data, "serialNumber": form.serialNumber.data}
        bikes = get_collection("bikes")

        filter = {"$or": [{"make": bike["make"]}, {"model": bike["model"]}, {"colour": bike["colour"]}, {"decals": bike["decals"]}, {"serialNumber": bike["serialNumber"]}]}

        num_potential_matches = bikes.count_documents(filter)

        if num_potential_matches == 0:
            return add_bike_and_redirect_to_contract(bike, person_id)
        else:
            cursor = bikes.find(filter)
            potential_matches = []
            for doc in cursor:
                potential_matches.append({"make": doc["make"], "model": doc["model"], "colour": doc["colour"], "decals": doc["decals"], "serialNumber": doc["serialNumber"], "id": doc["_id"]})

            return render_template("chooseBikeForRental.html", potentialMatches=potential_matches, originalData=bike, personId=person_id)

    else:
        return render_template('bikeDetails.html', form=form)


@app.route('/addbike', methods=["GET"])
def add_bike():
    person_id = request.args["personId"]

    make = request.args["make"]
    model = request.args["model"]
    colour = request.args["colour"]
    decals = request.args["decals"]
    serial_number = request.args["serialNumber"]

    bike = {"make": make, "model": model, "colour": colour, "decals": decals, "serialNumber": serial_number}

    return add_bike_and_redirect_to_contract(bike, person_id)


@app.route('/newcontract', methods=["GET", "POST"])
def newcontract():
    form = ContractForm()
    person_id = ObjectId(request.args["personId"])
    bike_id = ObjectId(request.args["bikeId"])
    bikes = get_collection("bikes")
    bike = bikes.find_one({"_id": bike_id})

    persons = get_collection("persons")
    person = persons.find_one({"_id": person_id})

    if form.validate_on_submit():
        contract = {"bike": bike, "person": person, "condition": form.condition.data, "contractType": form.contractType.data, "depositAmountPaid": form.depositAmountPaid.data, "endDate": form.endDate.data, "notes": form.notes.data, "startDate": form.startDate.data, "checkingVolunteer": form.checkingVolunteer.data, "depositAmountReturned": None, "volunteerReceived": None, "workingVolunteer": form.workingVolunteer.data, "depositCollectedBy": form.depositCollectedBy.data, "depositReturnedBy": None, "returnedDate": None}

        contracts = get_collection("contracts")
        contract_id = contracts.insert_one(contract).inserted_id

        flash("Contract recorded")
        return redirect(url_for("viewcontract", contractId=contract_id))
    else:

        form.person.data = f"{person['firstName']} {person['lastName']}"
        form.bike.data = f"{bike['make']} {bike['model']}"
        form.startDate.data = datetime.now()
        form.endDate.data = form.startDate.data + relativedelta(months=6)
        form.depositAmountPaid.data = 40
        form.contractType.data = "standard"

        return render_template('contractDetails.html', form=form)


@app.route('/findcontract', methods=["GET", "POST"])
def findcontract():
    form = FindContractForm()

    if form.validate_on_submit():
        first_name = form.firstName.data
        last_name = form.lastName.data
        make = form.make.data
        model = form.model.data

        person_details = []
        if first_name !="":
            person_details.append({"person.firstName": first_name})
        if last_name != "":
            person_details.append({"person.lastName": last_name})
        bike_details = []
        if make != "":
            bike_details.append({"bike.make": make})
        if model != "":
            bike_details.append({"bike.model": model})

        all_details = []
        if len(person_details) > 0:
            all_details.append({"$or": person_details})
        if len(bike_details) > 0:
            all_details.append({"$or": bike_details})

        filter = {"$and": all_details}

        contracts = get_collection("contracts")

        num_potential_contracts = contracts.count_documents(filter)
        if num_potential_contracts == 0:
            flash("No matches!")
            form = FindContractForm()
            return redirect(url_for("findcontract"))
        elif num_potential_contracts == 1:
            contract_id = contracts.find_one(filter)["_id"]
            return redirect(url_for('viewcontract', contractId=contract_id))
        else:
            cursor = contracts.find(filter)
            potential_contracts = []
            for doc in cursor:
                potential_contracts.append({"id": doc["_id"], "firstName": doc["person"]["firstName"], "lastName": doc["person"]["lastName"], "emailAddress": doc["person"]["emailAddress"], "make": doc["bike"]["make"], "model": doc["bike"]["model"], "colour": doc["bike"]["colour"], "decals": doc["bike"]["decals"], "serialNumber": doc["bike"]["serialNumber"]})

            return render_template("chooseContract.html", potentialContracts=potential_contracts)

    else:
        return render_template("findContract.html", form=form)



@app.route('/viewcontract', methods=["GET", "POST"])
def viewcontract():
    form = ReturnForm()
    contract_id = ObjectId(request.args["contractId"])
    contracts = get_collection("contracts")
    contract = contracts.find_one({"_id": contract_id})
    contract_tidy = {}
    for key, value in contract.items():
        if key.endswith("Date") and value is not None:
            contract_tidy[key] = datetime.date(value)
        else:
            contract_tidy[key] = value

    if form.validate_on_submit():
        contracts.update_one({"_id": contract_id}, {"$set": {
            "returnedDate": form.returnedDate.data,
            "volunteerReceived": form.volunteerReceived.data,
            "depositAmountReturned": form.depositAmountReturned.data,
            "depositReturnedBy": form.depositReturnedBy.data
        }})
        return redirect(url_for("viewcontract", contractId=contract_id))
    else:
        form.returnedDate.data = datetime.now()
        return render_template("viewContract.html", contract=contract_tidy, form=form)


@app.route('/extendcontract')
def extendcontract():
    contract_id = ObjectId(request.args["contractId"])
    contracts = get_collection("contracts")

    contracts.update_one({"_id": contract_id}, {"$set": {"endDate": datetime.now() + relativedelta(months=6)}})
    flash("Contract Extended for 6 Months")

    return redirect(url_for("viewcontract", contractId=contract_id))


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=80)
