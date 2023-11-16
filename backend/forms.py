from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField, DateTimeField, EmailField, SelectField, RadioField, DateField, HiddenField
from wtforms.validators import DataRequired, NoneOf
from backend.validators import validate_deposit_bearer_having_sufficient_funds, validate_deposit_amount_not_negative, validate_deposit_amount_returned_not_higher_than_deposit_amount_returned


class PersonForm(FlaskForm):
    firstName = StringField("First Name", [DataRequired()])
    lastName = StringField("Last Name", [DataRequired()])
    emailAddress = EmailField("Email Address")

    submit = SubmitField("Submit")


class BikeForm(FlaskForm):
    make = StringField("Make", [DataRequired()])
    model = StringField("Model", [DataRequired()])
    colour = StringField("Colour", [DataRequired()])
    decals = StringField("Decals")
    serialNumber = StringField("Serial Number", [DataRequired()])

    submit = SubmitField("Submit")


class ContractForm(FlaskForm):
    person = StringField("Person", render_kw={'READONLY': ''})
    bike = StringField("Bike", render_kw={'READONLY': ''})
    startDate = DateField("Lease Start Date", render_kw={'READONLY': ''})
    endDate = DateField("Lease End Date", render_kw={'READONLY': ''})
    contractType = RadioField("Contract Type", [DataRequired()], choices=["standard", "kids", "refugee"])
    depositAmountPaid = IntegerField("Deposit Amount Paid", [validate_deposit_amount_not_negative()])
    depositCollectedBy = SelectField("Deposit Collected By", [NoneOf(["Select"])], choices=["Select", "Alex1", "Colin", "Scott"])
    notes = StringField("Notes")
    condition = SelectField("Condition", [NoneOf(["Select"])], choices=["Select", "Poor", "Fair", "Good", "Excellent"])
    workingVolunteer = StringField("Working Volunteer", [DataRequired()])
    checkingVolunteer = StringField("Checking Volunteer",[DataRequired()])

    submit = SubmitField("Submit")


class PaperContractForm(FlaskForm):
    startDate = DateField("Lease Start Date", [DataRequired()])
    depositAmountPaid = IntegerField("Deposit Amount Paid", [validate_deposit_amount_not_negative()])
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
    contractId = StringField("Contract ID", [DataRequired()])

    submit = SubmitField("Search")


class FindContractForm(FlaskForm):
    firstName = StringField("First Name")
    lastName = StringField("Last Name")
    make = StringField("Bike Make")
    model = StringField("Bike Model")

    submit = SubmitField("Search")


class ReturnForm(FlaskForm):

    contractId = HiddenField("Contract Id", [DataRequired()])
    returnedDate = DateField("Return Date", [DataRequired()], render_kw={'READONLY': ''})
    volunteerReceived = StringField("Receiving Volunteer", [DataRequired()])
    depositAmountReturned = IntegerField("Deposit Amount Returned", [validate_deposit_amount_not_negative(), validate_deposit_amount_returned_not_higher_than_deposit_amount_returned()])
    depositReturnedBy = SelectField("Deposit Returned By", [NoneOf(["Select"]), validate_deposit_bearer_having_sufficient_funds()], choices=["Select", "Alex1", "Colin", "Scott"])

    submit = SubmitField("Do Return")
