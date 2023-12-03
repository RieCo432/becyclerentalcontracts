import datetime
import uuid
from datetime import date
from flask import Flask, redirect, url_for, flash, render_template, request, session
from backend.forms import PersonForm, BikeForm, ContractForm, ReturnForm, FindContractForm, PaperContractForm, \
    FindPaperContractForm, LoginForm, ChangePasswordForm, UserManagementForm
from config import secret_key, debug, server_host, server_port, ssl_context, link_base, google_app_username, google_app_password
from backend.database import *
from flask_bootstrap import Bootstrap5
from bson.dbref import DBRef
from backend.user_functions import get_hashed_password
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message

from appointmentConfig import *


app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key

bootstrap = Bootstrap5(app)
app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'quartz'

login_manager = LoginManager()
login_manager.login_view = "/login"
login_manager.init_app(app)

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 587,
    "MAIL_USE_TLS": True,
    "MAIL_USE_SSL": False,
    "MAIL_USERNAME": google_app_username,
    "MAIL_PASSWORD": google_app_password
}

app.config.update(mail_settings)
mail = Mail(app)

def add_person_and_redirect_to_bike(person):
    person_id = add_person(**person)
    return redirect(url_for('bike', personId=person_id))


def add_bike_and_redirect_to_contract(bike, person_id):
    bike_id = add_bike(**bike)
    return redirect(url_for('newcontract', bikeId=bike_id, personId=person_id))


def send_email_verification_link(email_address, link):
    msg = Message(subject="Verify your email address.",
                  sender=("Becycle Appointments", "no-reply@becycle.uk"),
                  recipients=[email_address],
                  body="To finalise your appointment request, verify your email address by clicking on the link below:\n" + link)

    mail.send(msg)


def send_email_appointment_confirmed(appointment_id):
    appointment = get_appointment_one(ObjectId(appointment_id))
    msg = Message(subject="Your appointment has been accepted!",
                  sender=("Becycle Appointments", "no-reply@becycle.uk"),
                  recipients=[appointment["emailAddress"]],
                  body="Dear {} {},\nyour appointment for {} on {} has been accepted. If for any reason, you want to cancel this appointment, please click on the link below:\n{}".format(
                      appointment["firstName"],
                      appointment["lastName"],
                      appointment_titles[appointment["type"]],
                      appointment["startDateTime"],
                      link_base + "/cancel-your-appointment?ref=" + appointment["ref"]
                  ))
    mail.send(msg)


def send_email_appointment_cancelled_as_requested(appointment):
    msg = Message(subject="Your appointment has been cancelled!",
                  sender=("Becycle Appointments", "no-reply@becycle.uk"),
                  recipients=[appointment["emailAddress"]],
                  body="Dear {} {},\nyour appointment for {} on {} has been cancelled as per your request. If this was a mistake, or you did not do this, please email us at contact@becycle.uk".format(
                      appointment["firstName"],
                      appointment["lastName"],
                      appointment_titles[appointment["type"]],
                      appointment["startDateTime"]
                  ))

    mail.send(msg)

def send_email_appointment_cancelled_by_us(appointment_id):
    appointment = get_appointment_one(ObjectId(appointment_id))
    msg = Message(subject="Your appointment has been cancelled by us!",
                  sender=("Becycle Appointments", "no-reply@becycle.uk"),
                  recipients=[appointment["emailAddress"]],
                  body="Dear {} {},\nunfortunately, your appointment for {} on {} has been cancelled by us. This is usually due to us having fewer volunteers available than expected. Please proceed to {} to book a new appointment.".format(
                      appointment["firstName"],
                      appointment["lastName"],
                      appointment_titles[appointment["type"]],
                      appointment["startDateTime"],
                      link_base + "/book-appointment"
                  ))

    mail.send(msg)

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
    form.workingVolunteer.choices = ["Select"] + get_all_usernames()
    form.checkingVolunteer.choices = ["Select"] + get_checking_volunteer_usernames()
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
    form.workingVolunteer.choices = ["Select", "unknown"] + get_all_usernames()
    form.checkingVolunteer.choices = ["Select", "unknown"] + get_all_usernames()
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

        depositCollectedBy = "pseudo_holder"

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


@app.route("/book-appointment", methods=["GET"])
def book_appointment():
    return redirect(url_for("select_appointment_type"))


@app.route("/select-appointment-type", methods=["GET", "POST"])
def select_appointment_type():


    return render_template("selectAppointmentType.html", appointment_shorts=[service for service in appointment_shorts if service!="xlrep"], appointment_titles=appointment_titles, appointment_descs=appointment_descs, page="bookappointment")


@app.route("/select-appointment-time", methods=["GET"])
def select_appointment_time():
    appointment_type = request.args["type"]

    available_appointments = get_available_time_slots(appointment_type)

    return render_template("selectAppointmentTime.html", appointment_type=appointment_type, available_slots=available_appointments, page="bookappointment")


@app.route("/enter-appointment-contact-info", methods=["GET", "POST"])
def enter_appointment_contact_details():
    appointment_type = request.args["type"]
    appointment_date = request.args["date"]
    appointment_time = request.args["time"]

    year, month, day = appointment_date.split("-")
    hour, minute = appointment_time.split(":")

    start_date_time = datetime(int(year), int(month), int(day), int(hour), int(minute))

    requested_slots = ceil(appointment_durations[appointment_type] / appointment_slotUnit)
    if not can_appointment_be_on_slot(get_number_of_available_slots(), start_date_time, requested_slots):
        flash("The time you selected earlier is no longer available! Please choose a new time!", "danger")
        return redirect(url_for("select_appointment_time", type=appointment_type))

    form = PersonForm()

    if form.validate_on_submit():

        first_name = form.firstName.data.lower()
        last_name = form.lastName.data.lower()
        email_address = form.emailAddress.data.lower()


        appointment_data = {
            "firstName": first_name,
            "lastName": last_name,
            "emailAddress": email_address,
            "type": appointment_type,
            "startDateTime": start_date_time,
            "endDateTime": start_date_time + relativedelta(minutes=appointment_durations[appointment_type]),
            "emailVerified": False,
            "emailVerificationCutoff": datetime.now() + relativedelta(seconds=30),
            "appointmentConfirmed": False,
            "appointmentConfirmationEmailSent": False,
            "appointmentReminderEmailSent": False,
            "cancelled": False,
            "ref": str(uuid.uuid4())
        }

        appointment_id = add_appointment(**appointment_data)

        appointment_verify_email_link = link_base + "/verify-email-for-appointment?id=" + str(appointment_id)

        send_email_verification_link(email_address, appointment_verify_email_link)

        return render_template("appointmentConfirmEmail.html", firstName=first_name, lastName=last_name, emailAddress=email_address, appointmentTitle=appointment_titles[appointment_type], appointmentDate=appointment_date, appointmentTime=appointment_time)

    else:
        return render_template("appointmentContactDetails.html", appointment_title=appointment_titles[appointment_type], appointment_time=appointment_time, appointment_date=appointment_date, page="bookappointment", form=form)


@app.route("/verify-email-for-appointment", methods=["GET"])
def verify_email_for_appointment():
    appointment_id = ObjectId(request.args["id"])

    success = complete_email_verification(appointment_id)

    if success:
        appointment = get_appointment_one(appointment_id)
        return render_template("appointmentRequested.html", firstName=appointment["firstName"], lastName=appointment["lastName"], emailAddress=appointment["emailAddress"], appointmentTitle=appointment_titles[appointment["type"]], appointmentDate=str(appointment["startDateTime"].date()), appointmentTime=str(appointment["startDateTime"].time()))
    else:
        return "SOME ERROR OCCURED"


@app.route("/appointments", methods=["GET"])
@login_required
def view_appointments():

    if "date" in request.args:
        dateToShow = date.fromisoformat(request.args["date"])
    else:
        # assume today and then increment date until it is an opening day
        dateToShow = date.today()
        while dateToShow.weekday() not in appointment_openingDays:
            dateToShow += relativedelta(days=1)

    previous_date = dateToShow - relativedelta(days=1)
    while previous_date.weekday() not in appointment_openingDays:
        previous_date -= relativedelta(days=1)

    next_date = dateToShow + relativedelta(days=1)
    while next_date.weekday() not in appointment_openingDays:
        next_date += relativedelta(days=1)

    all_appointments_on_day = get_all_appointments_for_day(dateToShow)
    all_appointments_on_day.sort(key=lambda a: a["startDateTime"])


    first_time_slot = sorted([slot for slot in appointment_concurrency.keys() if appointment_concurrency[slot] != 0])[0]
    last_time_slot = sorted([slot for slot in appointment_concurrency.keys()])[-1]

    first_datetime_slot = datetime(year=dateToShow.year, month=dateToShow.month, day=dateToShow.day, hour=first_time_slot.hour, minute=first_time_slot.minute)
    last_datetime_slot = datetime(year=dateToShow.year, month=dateToShow.month, day=dateToShow.day, hour=last_time_slot.hour, minute=last_time_slot.minute)

    table_data = {}

    time_slot = first_datetime_slot

    while time_slot <= last_datetime_slot:
        table_data["{:02d}:{:02d}".format(time_slot.hour, time_slot.minute)] = []
        time_slot += relativedelta(minutes=appointment_slotUnit)


    for appointment in all_appointments_on_day:
        startDateTime = appointment["startDateTime"]
        endDateTime = appointment["endDateTime"]

        duration_minutes = (endDateTime - startDateTime).seconds // 60
        slots_required = duration_minutes // appointment_slotUnit

        appointment_status = "success"

        if not appointment["appointmentConfirmed"]:
            appointment_status = "warning"

        if not appointment["emailVerified"]:
            if datetime.now() < appointment["emailVerificationCutoff"]:
                appointment_status = "danger"
            else:
                appointment_status = "light"

        if appointment["cancelled"]:
            appointment_status = "light"

        #  if the email address was not verified in time, don't show the appointment
        if appointment_status == "light":
            continue


        table_data["{:02d}:{:02d}".format(startDateTime.hour, startDateTime.minute)].append({
            "title": appointment_titles[appointment["type"]],
            "name": appointment["firstName"] + " " + appointment["lastName"],
            "email": appointment["emailAddress"],
            "slots": slots_required,
            "status": appointment_status,
            "confirmed": "Yes" if appointment["appointmentConfirmed"] else "No",
            "time": "{:02d}:{:02d} - {:02d}:{:02d}".format(startDateTime.hour, startDateTime.minute, endDateTime.hour, endDateTime.minute),
            "id": str(appointment["_id"])
        })
        block_slot = startDateTime + relativedelta(minutes=appointment_slotUnit)
        for _ in range(slots_required - 1):
            table_data["{:02d}:{:02d}".format(block_slot.hour, block_slot.minute)].append(None)
            block_slot += relativedelta(minutes=appointment_slotUnit)

    max_concurrent = max([len(table_data[time_slot]) for time_slot in table_data])


    return render_template("viewAppointments.html", date=str(dateToShow), previous_date=str(previous_date), next_date=str(next_date), table_data=table_data, max_concurrent=max_concurrent, user_is_appointmentManager=current_user.appointmentManager)


@app.route("/confirm-appointment", methods=["GET"])
@login_required
def confirm_appointment():
    if "id" not in request.args:
        flash("No id was specified!", "danger")
        return redirect(url_for("view_appointments"))
    if not current_user.appointmentManager:
        flash("You do not have the access rights to manage appointments!", "danger")
        return redirect(url_for("view_appointments"))

    if confirm_appointment_one(ObjectId(request.args["id"])):
        flash("Appointment Confirmed", "success")
        send_email_appointment_confirmed(request.args["id"])
    else:
        flash("Some error occured", "danger")

    if "date" in request.args:
        return redirect(url_for("view_appointments", date=request.args["date"]))
    else:
        return redirect(url_for("view_appointments"))


@app.route("/cancel-appointment", methods=["GET"])
@login_required
def cancel_appointment():
    if "id" not in request.args:
        flash("No id was specified!", "danger")
        return redirect(url_for("view_appointments"))
    if not current_user.appointmentManager:
        flash("You do not have the access rights to manage appointments!", "danger")
        return redirect(url_for("view_appointments"))

    if cancel_appointment_one(ObjectId(request.args["id"])):
        flash("Appointment cancelled", "success")
        send_email_appointment_cancelled_by_us(request.args["id"])
    else:
        flash("Some error occured", "danger")

    if "date" in request.args:
        return redirect(url_for("view_appointments", date=request.args["date"]))
    else:
        return redirect(url_for("view_appointments"))

@app.route("/cancel-your-appointment", methods=["GET"])
def cancel_your_appointment():
    if "ref" not in request.args:
        flash("No appointment reference was specified!", "danger")
        return redirect(url_for("index"))

    appointment = get_appointment_by_ref(request.args["ref"])

    if appointment:
        if not cancel_appointment_one(appointment["_id"]):
            flash("Some error occured!")
        else:
            flash("Your appointment has been cancelled. A confirmation email will follow.")
            send_email_appointment_cancelled_as_requested(appointment)

    else:
        flash("Some error occured!")

    return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(host=server_host, port=server_port, debug=debug, ssl_context=ssl_context)
