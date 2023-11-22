from flask_wtf import FlaskForm
from wtforms import (SubmitField, IntegerField, StringField, DateTimeField, EmailField, SelectField, RadioField,
                     DateField, HiddenField, PasswordField, BooleanField, FormField, FieldList, Form)
from wtforms.validators import DataRequired, NoneOf, EqualTo
from backend.validators import (validate_deposit_bearer_having_sufficient_funds, validate_deposit_amount_not_negative, \
                                validate_deposit_amount_returned_not_higher_than_deposit_amount_returned, validate_password_correct, \
                                validate_username_exists, data_required_if_registering_new_user, \
                                validate_username_available, passwords_match_if_registering_new_user, validate_deposit_collector_password,
                                validate_working_volunteer_password, validate_checking_volunteer_password,
                                validate_checking_volunteer_not_working_volunteer, validate_receiving_volunteer_password,
                                validate_deposit_provider_password)

from backend.database import get_deposit_bearers_usernames, get_all_usernames, get_checking_volunteer_usernames


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
    depositCollectedBy = SelectField("Deposit Collected By", [NoneOf(["Select"])], choices=["Select"] + get_deposit_bearers_usernames())
    depositBearerPassword = PasswordField("Password", [DataRequired(), validate_deposit_collector_password()])
    notes = StringField("Notes")
    condition = SelectField("Condition", [NoneOf(["Select"])], choices=["Select", "Poor", "Fair", "Good", "Excellent"])
    workingVolunteer = SelectField("Working Volunteer", [DataRequired(), NoneOf(["Select"])], choices = ["Select"] + get_all_usernames())
    workingVolunteerPassword = PasswordField("Password", [validate_working_volunteer_password()])
    checkingVolunteer = SelectField("Checking Volunteer",[DataRequired(), NoneOf("Select"), validate_checking_volunteer_not_working_volunteer()], choices=["Select"] + get_checking_volunteer_usernames())
    checkingVolunteerPassword = PasswordField("Password", [validate_checking_volunteer_password()])

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
    volunteerReceived = SelectField("Receiving Volunteer", [DataRequired()], choices=["Select"] + get_all_usernames())
    volunteerReceivedPassword = PasswordField("Password", [DataRequired(), validate_receiving_volunteer_password()])
    depositAmountReturned = IntegerField("Deposit Amount Returned", [validate_deposit_amount_not_negative(), validate_deposit_amount_returned_not_higher_than_deposit_amount_returned()])
    depositReturnedBy = SelectField("Deposit Returned By", [NoneOf(["Select"]), validate_deposit_bearer_having_sufficient_funds()], choices=["Select"] + get_deposit_bearers_usernames())
    depositBearerPassword = PasswordField("Password", [DataRequired(), validate_deposit_provider_password()])

    submit = SubmitField("Do Return")


class LoginForm(FlaskForm):

    username = StringField("Username", [DataRequired(), validate_username_exists()])
    password = PasswordField("Password", [DataRequired(), validate_password_correct()])

    submit = SubmitField("Login")


class ChangePasswordForm(FlaskForm):
    username = StringField("Username", [DataRequired(), validate_username_exists()])
    old_password = PasswordField("Old password", [DataRequired(), validate_password_correct()])
    new_password = PasswordField("New password", [DataRequired()])
    repeat_password = PasswordField("Repeat password", [DataRequired(), EqualTo("new_password")])

    submit = SubmitField("Change Password")


class UserRolesForm(FlaskForm):
    username = HiddenField("", [DataRequired(), validate_username_exists()])
    admin = BooleanField("")
    depositBearer = BooleanField("")
    rentalChecker = BooleanField("")
    appointmentManager = BooleanField("")

class RegisterUserForm(FlaskForm):
    username = StringField("Username", [validate_username_available()])
    password = PasswordField("Password", [data_required_if_registering_new_user()])
    repeat_password = PasswordField("Repeat Password", [data_required_if_registering_new_user(), passwords_match_if_registering_new_user()])

class UserManagementForm(FlaskForm):
    user_roles_forms = FieldList(FormField(UserRolesForm))
    new_user_form = FormField(RegisterUserForm)

    submit = SubmitField("Submit")




