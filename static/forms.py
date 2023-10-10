from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField, DateTimeField, EmailField, SelectField


class PersonForm(FlaskForm):
    firstName = StringField("First Name")
    lastName = StringField("Last Name")
    emailAddress = EmailField("Email Address")

    submit = SubmitField("Submit")


class BikeForm(FlaskForm):
    make = StringField("Make")
    model = StringField("Model")
    colour = StringField("Colour")
    decals = StringField("Decals")
    serialNumber = StringField("Serial Number")

    submit = SubmitField("Submit")


class ContractForm(FlaskForm):
    person = StringField("Person")
    bike = StringField("Bike")
    startDate = DateTimeField("Lease Start Date")
    endDate = DateTimeField("Lease End Date")
    depositAmountPaid = IntegerField("Deposit Amount Paid")
    depositCollectedBy = SelectField("Deposit Collected By", choices=["Select", "Alex1", "Colin", "Scott"])
    notes = StringField("Notes")
    condition = SelectField("Condition", choices=["Select", "Poor", "Fair", "Good", "Excellent"])
    workingVolunteer = StringField("Working Volunteer")
    checkingVolunteer = StringField("Checking Volunteer")

    submit = SubmitField("Submit")


class FindContractForm(FlaskForm):
    firstName = StringField("First Name")
    lastName = StringField("Last Name")
    make = StringField("Make")
    model = StringField("Model")

    submit = SubmitField("Search")


class ReturnForm(FlaskForm):

    returnedDate = DateTimeField("Return Date")
    volunteerReceived = StringField("Receiving Volunteer")
    depositAmountReturned = IntegerField("Deposit Amount Returned")
    depositReturnedBy = SelectField("Deposit Returned By", choices=["Select", "Alex1", "Colin", "Scott"])

    submit = SubmitField("Do Return")
