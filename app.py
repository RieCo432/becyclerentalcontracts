import uuid

from flask import Flask, redirect, url_for, flash, render_template, request, session
from wtforms import ValidationError
from wtforms.validators import EqualTo

from backend.forms import PersonForm, BikeForm, ContractForm, ReturnForm, FindContractForm, PaperContractForm, \
    FindPaperContractForm, LoginForm, ChangePasswordForm, UserManagementForm
from dateutil.relativedelta import relativedelta

from backend.validators import validate_username_available
from config import secret_key, debug, server_host, server_port
from backend.database import *
from flask_bootstrap import Bootstrap5
from bson.dbref import DBRef
from backend.user_functions import get_hashed_password
from flask_login import LoginManager, login_user, login_required, logout_user, current_user



app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key

bootstrap = Bootstrap5(app)
app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'quartz'

login_manager = LoginManager()
login_manager.login_view = "/login"
login_manager.init_app(app)


def add_person_and_redirect_to_bike(person):
    person_id = add_person(**person)
    return redirect(url_for('bike', personId=person_id))


def add_bike_and_redirect_to_contract(bike, person_id):
    bike_id = add_bike(**bike)
    return redirect(url_for('newcontract', bikeId=bike_id, personId=person_id))


@app.route('/')
@app.route('/index')
def index():  # put application's code here
    return render_template("index.html", page="index")


@app.route('/newrental', methods=["GET"])
@login_required
def newrental():
    return redirect(url_for('person'))


@app.route('/person', methods=["GET", "POST"])
@login_required
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
@login_required
def register_person():
    first_name = request.args["firstName"]
    last_name = request.args["lastName"]
    email_address = request.args["emailAddress"]
    person = {"firstName": first_name, "lastName": last_name, "emailAddress": email_address}

    return add_person_and_redirect_to_bike(person)


@app.route('/bike', methods=["GET", "POST"])
@login_required
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
@login_required
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
@login_required
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

        contract = {"bike": DBRef(collection="bikes", id=bike_id), "person": DBRef(collection="persons", id=person_id),
                    "condition": form.condition.data.lower(), "contractType": form.contractType.data.lower(),
                    "depositAmountPaid": form.depositAmountPaid.data, "endDate": endDateTime,
                    "notes": form.notes.data.lower(), "startDate": startDateTime,
                    "checkingVolunteer": form.checkingVolunteer.data.lower(), "depositAmountReturned": None,
                    "volunteerReceived": None, "workingVolunteer": form.workingVolunteer.data.lower(),
                    "depositCollectedBy": form.depositCollectedBy.data.lower(), "depositReturnedBy": None,
                    "returnedDate": None, "contractSentToEmail": False, "expiryReminderSentToEmail": False}

        contract_id = add_contract(**contract)

        flash("Contract recorded", "success")
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
@login_required
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
            flash("No matches!", "danger")
            return redirect(url_for("findcontract"))
        elif num_potential_contracts == 1:
            contract_id = get_contract_one(bike=bike_ids, person=person_ids)["_id"]
            return redirect(url_for('viewcontract', contractId=contract_id))
        else:
            return render_template("chooseContract.html", potentialContracts=get_contracts(bike=bike_ids, person=person_ids), page="findcontract")

    else:
        return render_template("findContract.html", form=form, page="findcontract")


@app.route('/viewcontract', methods=["GET", "POST"])
@login_required
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
@login_required
def extendcontract():
    contract_id = ObjectId(request.args["contractId"])

    contract_data = {"_id": contract_id, "endDate": datetime.now() + relativedelta(months=6)}
    update_contract_one(**contract_data)

    return redirect(url_for("viewcontract", contractId=contract_id))

@app.route("/about")
def about():
    return render_template("about.html", page="about")


@app.route('/addpapercontract', methods=["GET", "POST"])
@login_required
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
                    "depositReturnedBy": None, "returnedDate": None, "contractSentToEmail": False,
                    "expiryReminderSentToEmail": False}

        contract_id = add_contract(**contract)

        return render_template("showPaperContractId.html", contractID=contract_id, page="addpapercontract")
    else:
        form.contractType.data = "Select"
        return render_template("addPaperContract.html", form=form, page="addpapercontract")


@app.route("/findpapercontract", methods=["GET", "POST"])
@login_required
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
@login_required
def bookkeeping():
    book = get_bookkeeping()
    days = list(book.keys())
    days.sort(reverse=True)
    return render_template("bookkeeping.html", book=book, days=days, page="bookkeeping")


@login_manager.user_loader
def load_user(user_id):
    try:
        return get_user_by_id(user_id)
    except Exception:
        return None

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        login_user(get_user_by_username(form.username.data), remember=True)
        session["token"] = str(uuid.uuid4())
        return redirect(url_for("index"))
    else:
        return render_template("staffLogin.html", form=form, page="login")

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    del session["token"]
    logout_user()
    return redirect(url_for("index"))


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def changePassword():
    form = ChangePasswordForm()
    form.username.data = current_user.username

    if form.validate_on_submit():
        hashed_password = get_hashed_password(form.new_password.data)
        success = update_user_password(form.username.data, hashed_password)

        if success:
            flash("Password updated", "success")
        else:
            flash("An error occured", "danger")

        return redirect(url_for("index"))

    else:
        return render_template("changePassword.html", form=form)


@app.route("/user-management", methods=["GET", "POST"])
@login_required
def user_management():
    users = get_all_users()

    user_roles = [{
        "username": user.username,
        "admin": user.admin,
        "depositBearer": user.depositBearer,
        "rentalChecker": user.rentalChecker,
        "appointmentManager": user.appointmentManager
    } for user in users]

    form = UserManagementForm(user_roles_forms=user_roles)

    if form.validate_on_submit():
        if current_user.admin:
            for user_roles_form in form.user_roles_forms:
                updated_user_data = {
                    "username": user_roles_form.username.data,
                    "admin": user_roles_form.admin.data,
                    "depositBearer": user_roles_form.depositBearer.data,
                    "rentalChecker": user_roles_form.rentalChecker.data,
                    "appointmentManager": user_roles_form.appointmentManager.data
                }

                if updated_user_data["username"] == current_user.username and not updated_user_data["admin"]:
                    flash("You cannot remove your own admin status.", "danger")
                else:
                    success = update_user(**updated_user_data)

                    if success:
                        flash("User roles updated", "success")
                    else:
                        flash("Some error has occured.", "danger")

            if form.new_user_form.username.data != "":

                user_data = {
                        "username": form.new_user_form.username.data,
                        "password": get_hashed_password(form.new_user_form.password.data),
                        "admin": False,
                        "depositBearer": False,
                        "rentalChecker": False,
                        "appointmentManager": False
                }

                success = add_user(**user_data)
                if success:
                    flash("User Added", "success")
                else:
                    flash("Some error has occured.", "danger")

        else:
            flash("The current user is not an admin!", "danger")

        return redirect(url_for("user_management"))

    return render_template("userManagement.html",
                               form=form)



if __name__ == '__main__':
    app.run(host=server_host, port=server_port, debug=debug)
