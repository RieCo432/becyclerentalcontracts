from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField, DateTimeField, EmailField, SelectField, RadioField, DateField
from wtforms.validators import DataRequired


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
    startDate = DateField("Lease Start Date")
    endDate = DateField("Lease End Date")
    contractType = RadioField("Contract Type", choices=["standard", "kids", "refugee"])
    depositAmountPaid = IntegerField("Deposit Amount Paid")
    depositCollectedBy = SelectField("Deposit Collected By", choices=["Select", "Alex1", "Colin", "Scott"])
    notes = StringField("Notes")
    condition = SelectField("Condition", choices=["Select", "Poor", "Fair", "Good", "Excellent"])
    workingVolunteer = StringField("Working Volunteer")
    checkingVolunteer = StringField("Checking Volunteer")

    submit = SubmitField("Submit")


class PaperContractForm(FlaskForm):
    startDate = DateField("Lease Start Date", [DataRequired()])
    depositAmountPaid = IntegerField("Deposit Amount Paid", [DataRequired()])
    contractType = RadioField("Contract Type", [DataRequired()], choices=["standard", "kids", "refugee"])
    workingVolunteer = StringField("Working Volunteer", [DataRequired()])
    checkingVolunteer = StringField("Checking Volunteer", [DataRequired()])

    firstName = StringField("First Name")
    lastName = StringField("Last Name")
    emailAddress = EmailField("Email Address")

    make = StringField("Make")
    model = StringField("Model")
    colour = StringField("Colour")
    decals = StringField("Decals")
    serialNumber = StringField("Serial Number")

    notes = StringField("Notes")
    condition = SelectField("Condition", choices=["Select", "Poor", "Fair", "Good", "Excellent"])


    submit = SubmitField("Submit")


class FindPaperContractForm(FlaskForm):
    contractId = StringField("Contract ID")

    submit = SubmitField("Submit")


class FindContractForm(FlaskForm):
    firstName = StringField("First Name")
    lastName = StringField("Last Name")
    make = StringField("Make")
    model = StringField("Model")

    submit = SubmitField("Search")


class ReturnForm(FlaskForm):

    returnedDate = DateField("Return Date")
    volunteerReceived = StringField("Receiving Volunteer")
    depositAmountReturned = IntegerField("Deposit Amount Returned")
    depositReturnedBy = SelectField("Deposit Returned By", choices=["Select", "Alex1", "Colin", "Scott"])

    submit = SubmitField("Do Return")
