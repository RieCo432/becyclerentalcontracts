from flask import Flask, redirect, url_for, flash, render_template, request
from backend.forms import PersonForm, BikeForm, ContractForm, ReturnForm, FindContractForm, PaperContractForm, \
    FindPaperContractForm
from dateutil.relativedelta import relativedelta
from config import secret_key, debug, server_host, server_port
from backend.database import *
from flask_bootstrap import Bootstrap5
from bson.dbref import DBRef


app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key

bootstrap = Bootstrap5(app)
app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'quartz'


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
    if len(request.args) == 0:
        if form.validate_on_submit():
            person = {"firstName": form.firstName.data.lower(), "lastName": form.lastName.data.lower(), "emailAddress": form.emailAddress.data.lower()}

            if get_persons_count(**person) == 0:
                return add_person_and_redirect_to_bike(person)
            else:
                persons = get_persons(**person)
                return render_template('chooseLendeeForRental.html', potentialMatches=persons, originalData=person, page="newrental")

        else:
            return render_template('lendeeDetails.html', form=form, page="newrental")
    elif "personId" in request.args:
        personId = ObjectId(request.args["personId"])

        if form.validate_on_submit():
            person = {"firstName": form.firstName.data.lower(), "lastName": form.lastName.data.lower(),
                      "emailAddress": form.emailAddress.data.lower(), "_id": personId}

            update_person_one(**person)

            return redirect(url_for("viewcontract", contractId=request.args["contractId"]))

        else:
            person = get_one_person(_id=personId)
            form.firstName.data = person["firstName"]
            form.lastName.data = person["lastName"]
            form.emailAddress.data = person["emailAddress"]
            return render_template('lendeeDetails.html', form=form, page="findcontract")



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
    if "personId" in request.args:
        person_id = ObjectId(request.args["personId"])
        if form.validate_on_submit():
            bike = {"make": form.make.data.lower(), "model": form.model.data.lower(), "colour": form.colour.data.lower(), "decals": form.decals.data.lower(), "serialNumber": form.serialNumber.data.lower()}

            if get_bikes_count(**bike) == 0:
                return add_bike_and_redirect_to_contract(bike, person_id)
            else:
                return render_template("chooseBikeForRental.html", potentialMatches=get_bikes(**bike), originalData=bike, personId=person_id, page="newrental")

        else:
            return render_template('bikeDetails.html', form=form, page="newrental")
    elif "bikeId" in request.args:
        bikeId = ObjectId(request.args["bikeId"])

        if form.validate_on_submit():
            bike = {"make": form.make.data.lower(), "model": form.model.data.lower(),
                    "colour": form.colour.data.lower(), "decals": form.decals.data.lower(),
                    "serialNumber": form.serialNumber.data.lower(), "_id": bikeId}

            update_bike_one(**bike)

            return redirect(url_for("viewcontract", contractId=request.args["contractId"]))

        else:
            bike = get_one_bike(_id=bikeId)

            form.make.data = bike["make"]
            form.model.data = bike["model"]
            form.colour.data = bike["colour"]
            form.decals.data = bike["decals"]
            form.serialNumber.data = bike["serialNumber"]

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
    bike = get_one_bike(_id=ObjectId(bike_id))
    person = get_one_person(_id=ObjectId(person_id))

    if form.validate_on_submit():
        startDate = form.startDate.data
        startDateTime = datetime(startDate.year, startDate.month, startDate.day)

        endDate = form.endDate.data
        endDateTime = datetime(endDate.year, endDate.month, endDate.day)

        contract = {"bike": DBRef(collection="bikes", id=bike_id), "person": DBRef(collection="persons", id=person_id), "condition": form.condition.data.lower(), "contractType": form.contractType.data.lower(), "depositAmountPaid": form.depositAmountPaid.data, "endDate": endDateTime, "notes": form.notes.data.lower(), "startDate": startDateTime, "checkingVolunteer": form.checkingVolunteer.data.lower(), "depositAmountReturned": None, "volunteerReceived": None, "workingVolunteer": form.workingVolunteer.data.lower(), "depositCollectedBy": form.depositCollectedBy.data.lower(), "depositReturnedBy": None, "returnedDate": None}

        contract_id = add_contract(**contract)

        flash("Contract recorded")
        return redirect(url_for("viewcontract", contractId=contract_id))
    else:

        form.person.data = f"{person['firstName']} {person['lastName']}"
        form.bike.data = f"{bike['make']} {bike['model']}"
        form.startDate.data = datetime.today()
        form.endDate.data = form.startDate.data + relativedelta(months=6)
        form.depositAmountPaid.data = 40
        form.contractType.data = "Select"

        return render_template('contractDetails.html', form=form, page="newrental")


@app.route('/findcontract', methods=["GET", "POST"])
def findcontract():
    form = FindContractForm()

    if form.validate_on_submit():
        first_name = form.firstName.data.lower()
        last_name = form.lastName.data.lower()
        make = form.make.data.lower()
        model = form.model.data.lower()

        person_data = {"firstName": first_name, "lastName": last_name}
        persons = get_persons(**person_data)
        person_ids = [person["_id"] for person in persons]

        bike_data = {"make": make, "model": model}
        bikes = get_bikes(**bike_data)
        bike_ids = [bike["_id"] for bike in bikes]

        num_potential_contracts = get_contracts_count(bike=bike_ids, person=person_ids)

        if num_potential_contracts == 0:
            flash("No matches!")
            return redirect(url_for("findcontract"))
        elif num_potential_contracts == 1:
            contract_id = get_contract_one(bike=bike_ids, person=person_ids)["_id"]
            return redirect(url_for('viewcontract', contractId=contract_id))
        else:
            return render_template("chooseContract.html", potentialContracts=get_contracts(bike=bike_ids, person=person_ids), page="findcontract")

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
        returnedDate = form.returnedDate.data
        returnedDateTime = datetime(returnedDate.year, returnedDate.month, returnedDate.day)

        contract_data = {
            "_id": contract_id,
            "returnedDate": returnedDateTime,
            "volunteerReceived": form.volunteerReceived.data.lower(),
            "depositAmountReturned": form.depositAmountReturned.data,
            "depositReturnedBy": form.depositReturnedBy.data.lower()
        }

        update_contract_one(**contract_data)

        return redirect(url_for("viewcontract", contractId=contract_id))
    else:
        form.contractId.data = contract_id
        form.returnedDate.data = datetime.today()
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


@app.route('/addpapercontract', methods=["GET", "POST"])
def add_paper_contract():
    form = PaperContractForm()
    if form.validate_on_submit():

        startDate = form.startDate.data
        endDate = startDate + relativedelta(months=6)

        startDateTime = datetime(startDate.year, startDate.month, startDate.day)
        endDateTime = datetime(endDate.year, endDate.month, endDate.day)

        depositAmountPaid = form.depositAmountPaid.data
        contractType = form.contractType.data.lower()
        workingVolunteer = form.workingVolunteer.data.lower()
        checkingVolunteer = form.checkingVolunteer.data.lower()

        firstName = form.firstName.data.lower()
        if firstName == "":
            firstName = "NOTPROVIDED"
        lastName = form.lastName.data.lower()
        if lastName == "":
            lastName = "NOTPROVIDED"
        emailAddress = form.emailAddress.data.lower()
        if emailAddress == "":
            emailAddress = "NOTPROVIDED"

        make = form.make.data.lower()
        if make == "":
            make = "NOTPROVIDED"
        model = form.model.data.lower()
        if model == "":
            model = "NOTPROVIDED"
        colour = form.colour.data.lower()
        if colour == "":
            colour = "NOTPROVIDED"
        decals = form.decals.data.lower()
        if decals == "":
            decals = "NOTPROVIDED"
        serialNumber = form.serialNumber.data.lower()
        if serialNumber == "":
            serialNumber = "NOTPROVIDED"

        notes = form.notes.data.lower()

        condition = form.condition.data.lower()
        if condition == "select":
            condition = "NOTPROVIDED"

        person_data = {"firstName": firstName, "lastName": lastName, "emailAddress": emailAddress}
        person_id = add_person(**person_data)

        bike_data = {"make": make, "model": model, "colour": colour, "decals": decals, "serialNumber": serialNumber}
        bike_id = add_bike(**bike_data)

        depositCollectedBy = "PSEUDO_HOLDER"

        contract = {"bike": DBRef(collection="bikes", id=bike_id), "person": DBRef(collection="persons", id=person_id),
                    "condition": condition, "contractType": contractType, "depositAmountPaid": depositAmountPaid,
                    "endDate": endDateTime, "notes": notes, "startDate": startDateTime,
                    "checkingVolunteer": checkingVolunteer, "depositAmountReturned": None, "volunteerReceived": None,
                    "workingVolunteer": workingVolunteer, "depositCollectedBy": depositCollectedBy,
                    "depositReturnedBy": None, "returnedDate": None}

        contract_id = add_contract(**contract)

        return render_template("showPaperContractId.html", contractID=contract_id, page="addpapercontract")
    else:
        form.contractType.data = "Select"
        return render_template("addPaperContract.html", form=form, page="addpapercontract")


@app.route("/findpapercontract", methods=["GET", "POST"])
def find_paper_contract():
    form = FindPaperContractForm()

    if form.validate_on_submit():
        contract = get_contract_one(_id=ObjectId(form.contractId.data.lower()))

        if contract:
            return redirect(url_for("viewcontract", contractId=contract["_id"]))
        else:
            return redirect(url_for("find_paper_contract"))

    else:
        return render_template("findPaperContract.html", form=form, page="findpapercontract")


@app.route("/bookkeeping", methods=["GET"])
def bookkeeping():
    book = get_bookkeeping()
    days = list(book.keys())
    days.sort(reverse=True)
    return render_template("bookkeeping.html", book=book, days=days, page="bookkeeping")


if __name__ == '__main__':
    app.run(host=server_host, port=server_port, debug=debug)
