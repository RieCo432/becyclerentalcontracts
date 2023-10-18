from flask import Flask, redirect, url_for, flash, render_template, request
from backend.forms import PersonForm, BikeForm, ContractForm, ReturnForm, FindContractForm
from datetime import datetime
from dateutil.relativedelta import relativedelta
from config import secret_key, debug, server_host, server_port
from backend.database import *


app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key


def add_person_and_redirect_to_bike(person):
    person_id = add_person(**person)
    return redirect(url_for('bike', personId=person_id))


def add_bike_and_redirect_to_contract(bike, person_id):
    bike_id = add_bike(**bike)
    return redirect(url_for('newcontract', bikeId=bike_id, personId=person_id))


@app.route('/')
@app.route('/index')
def hello_world():  # put application's code here
    return render_template("index.html", page="index")


@app.route('/newrental', methods=["GET"])
def newrental():
    return redirect(url_for('person'))


@app.route('/person', methods=["GET", "POST"])
def person():
    form = PersonForm()
    if form.validate_on_submit():
        person = {"firstName": form.firstName.data, "lastName": form.lastName.data, "emailAddress": form.emailAddress.data}


        if get_persons_count(**person) == 0:
            return add_person_and_redirect_to_bike(person)
        else:
            persons = get_persons(**person)
            #potential_matches = []
            #for person in persons:
            #    potential_matches.append({"firstName": person["firstName"], "lastName": person["lastName"], "emailAddress": person["emailAddress"], "id": person["_id"]})
            return render_template('chooseLendeeForRental.html', potentialMatches=persons, originalData=person, page="newrental")

    else:
        return render_template('lendeeDetails.html', form=form, page="newrental")


@app.route('/addperson', methods=["GET"])
def register_person():
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

        if get_bikes_count(**bike) == 0:
            return add_bike_and_redirect_to_contract(bike, person_id)
        else:
            return render_template("chooseBikeForRental.html", potentialMatches=get_bikes(**bike), originalData=bike, personId=person_id, page="newrental")

    else:
        return render_template('bikeDetails.html', form=form, page="newrental")


@app.route('/addbike', methods=["GET"])
def register_bike():
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
    bike = get_one_bike(_id=bike_id)
    person = get_one_person(_id=person_id)

    if form.validate_on_submit():
        contract = {"bike": bike, "person": person, "condition": form.condition.data, "contractType": form.contractType.data, "depositAmountPaid": form.depositAmountPaid.data, "endDate": form.endDate.data, "notes": form.notes.data, "startDate": form.startDate.data, "checkingVolunteer": form.checkingVolunteer.data, "depositAmountReturned": None, "volunteerReceived": None, "workingVolunteer": form.workingVolunteer.data, "depositCollectedBy": form.depositCollectedBy.data, "depositReturnedBy": None, "returnedDate": None}

        contract_id = add_contract(**contract)

        flash("Contract recorded")
        return redirect(url_for("viewcontract", contractId=contract_id))
    else:

        form.person.data = f"{person['firstName']} {person['lastName']}"
        form.bike.data = f"{bike['make']} {bike['model']}"
        form.startDate.data = datetime.now()
        form.endDate.data = form.startDate.data + relativedelta(months=6)
        form.depositAmountPaid.data = 40
        form.contractType.data = "standard"

        return render_template('contractDetails.html', form=form, page="newrental")


@app.route('/findcontract', methods=["GET", "POST"])
def findcontract():
    form = FindContractForm()

    if form.validate_on_submit():
        first_name = form.firstName.data
        last_name = form.lastName.data
        make = form.make.data
        model = form.model.data

        contract = {"person.firstName": first_name, "person.lastName": last_name, "bike.make": make, "bike.model": model}

        num_potential_contracts = get_contracts_count(**contract)

        if num_potential_contracts == 0:
            flash("No matches!")
            return redirect(url_for("findcontract"))
        elif num_potential_contracts == 1:
            contract_id = get_contract_one(**contract)["_id"]
            return redirect(url_for('viewcontract', contractId=contract_id))
        else:
            return render_template("chooseContract.html", potentialContracts=get_contracts(**contract), page="findcontract")

    else:
        return render_template("findContract.html", form=form, page="findcontract")



@app.route('/viewcontract', methods=["GET", "POST"])
def viewcontract():
    form = ReturnForm()
    contract_id = ObjectId(request.args["contractId"])
    contract_tidy = {}
    for key, value in get_contract_one(_id=contract_id).items():
        if key.endswith("Date") and value is not None:
            contract_tidy[key] = datetime.date(value)
        else:
            contract_tidy[key] = value

    if form.validate_on_submit():
        contract_data = {
            "_id": contract_id,
            "returnedDate": form.returnedDate.data,
            "volunteerReceived": form.volunteerReceived.data,
            "depositAmountReturned": form.depositAmountReturned.data,
            "depositReturnedBy": form.depositReturnedBy.data
        }

        update_contract_one(**contract_data)

        return redirect(url_for("viewcontract", contractId=contract_id))
    else:
        form.returnedDate.data = datetime.now()
        return render_template("viewContract.html", contract=contract_tidy, form=form, page="findcontract")


@app.route('/extendcontract')
def extendcontract():
    contract_id = ObjectId(request.args["contractId"])

    contract_data = {"_id": contract_id, "endDate": datetime.now() + relativedelta(months=6)}
    update_contract_one(**contract_data)

    return redirect(url_for("viewcontract", contractId=contract_id))

@app.route("/about")
def about():
    return render_template("about.html", page="about")


if __name__ == '__main__':
    app.run(host=server_host, port=server_port, debug=debug)
