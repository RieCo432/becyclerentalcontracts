from wtforms.validators import ValidationError
from backend.database import get_deposit_bearer_balance, get_deposit_amount_paid, check_if_username_exists, get_user_by_username
from backend.user_functions import check_user_password, check_user_pin

def validate_deposit_bearer_having_sufficient_funds():

    def _deposit_bearer_has_enough_funds(form, field):
        if get_deposit_bearer_balance(field.data.lower()) < form.depositAmountReturned.data:
            raise ValidationError("The selected deposit bearer has insufficient funds to return the desired deposit.")

    return _deposit_bearer_has_enough_funds

def validate_deposit_amount_returned_not_higher_than_deposit_amount_returned():

    def _deposit_amount_returned_is_not_higher_than_deposit_amount_paid(form, field):
        if field.data > get_deposit_amount_paid(form.contractId.data):
            raise ValidationError("The returned deposit is higher than the deposit that was collected.")

    return _deposit_amount_returned_is_not_higher_than_deposit_amount_paid

def validate_deposit_amount_not_negative():

    def _deposit_amount_is_not_negative(form, field):
        if field.data < 0:
            raise ValidationError("Deposit amount cannot be negative.")

    return _deposit_amount_is_not_negative


def validate_password_correct():

    def _password_is_correct(form, field):
        if not check_user_password(form.username.data, field.data):
            raise ValidationError("Incorrect password.")

    return _password_is_correct


def validate_username_exists():

    def _user_exists(form, field):
        if not check_if_username_exists(field.data):
            raise ValidationError("Username does not exist.")

    return _user_exists


def validate_username_available():

    def _user_exists(form, field):
        if field.data != "" and check_if_username_exists(field.data):
            raise ValidationError("Username already exists.")

    return _user_exists

def data_required_if_registering_new_user():

    def _data_required(form, field):
        if form.username.data != "" and field.data == "":
            raise ValidationError("This field is required!")

    return _data_required

def passwords_match_if_registering_new_user():

    def _passwords_match(form, field):
        if form.username.data != "" and field.data != form.password.data:
            raise ValidationError("Passwords do not match!")

    return _passwords_match

def validate_deposit_collector_password():

    def _password_is_valid(form, field):
        if not check_user_password(form.depositCollectedBy.data, field.data):
            raise ValidationError("Incorrect password!")

    return _password_is_valid


def validate_working_volunteer_password_or_pin():
    def _password_or_pin_is_valid(form, field):
        if not (check_user_pin(form.workingVolunteer.data, field.data) or check_user_password(form.workingVolunteer.data, field.data)):
            raise ValidationError("Incorrect password or PIN!")

    return _password_or_pin_is_valid


def validate_checking_volunteer_password_or_pin():
    def _password_or_pin_is_valid(form, field):
        if not (check_user_pin(form.checkingVolunteer.data, field.data) or check_user_password(form.checkingVolunteer.data, field.data)):
            raise ValidationError("Incorrect password or PIN!")

    return _password_or_pin_is_valid

def validate_checking_volunteer_not_working_volunteer():

    def _two_different_volunteers(form, field):
        if form.workingVolunteer.data == form.checkingVolunteer.data:
            raise ValidationError("Checking volunteer must be different from working volunteer.")

    return _two_different_volunteers

def validate_receiving_volunteer_password_or_pin():

    def _password_or_pin_is_valid(form, field):
        if not (check_user_pin(form.volunteerReceived.data, field.data) or check_user_password(form.volunteerReceived.data, field.data)):
            raise ValidationError("Incorrect password or pin.")

    return _password_or_pin_is_valid

def validate_deposit_provider_password():

    def _password_is_valid(form, field):
        if not check_user_password(form.depositReturnedBy.data, field.data):
            raise ValidationError("Password incorrect.")

    return _password_is_valid

def validate_max_bookahead_bigger_than_min():

    def _max_bookahead_is_bigger(form, field):
        if not field.data > form.book_ahead_min.data:
            raise ValidationError("Maximum Book Ahead must be bigger than minimum")

    return _max_bookahead_is_bigger

def validate_is_4_digits():

    def _is_4_digits(form, field):
        if len(field.data) != 4:
            raise ValidationError("PIN must be 4 digits long!")

        for char in field.data:
            if char not in "0123456789":
                raise ValidationError("PIN can only contain numbers!")

    return _is_4_digits

def validate_from_deposit_bearer_password():

    def _from_deposit_bearer_password_is_correct(form, field):
        if not (form.from_username.data == "bank account" or check_user_password(form.from_username.data, field.data)):
            raise ValidationError("Password incorrect!")

    return _from_deposit_bearer_password_is_correct


def validate_to_deposit_bearer_password():
    def _to_deposit_bearer_password_is_correct(form, field):
        if not (form.to_username.data == "bank account" or check_user_password(form.to_username.data, field.data)):
            raise ValidationError("Password incorrect!")

    return _to_deposit_bearer_password_is_correct

def validate_to_deposit_bearer_not_equal_to_from():

    def _to_deposit_bearer_is_not_from(form, field):
        if field.data == form.from_username.data:
            raise ValidationError("To and From must be different")

    return _to_deposit_bearer_is_not_from

def validate_from_deposit_bearer_has_sufficient_balance():

    def _from_deposit_bearer_has_sufficient_balance(form, field):
        if form.from_username.data != "bank account" and get_deposit_bearer_balance(form.from_username.data) < field.data:
            raise ValidationError("Amount exceeds deposit bearer balance")

    return _from_deposit_bearer_has_sufficient_balance

def validate_to_bankaccount_if_from_is_treasurer():

    def _from_is_treasurer_if_destination_is_bankaccount(form, field):
        if field.data == "bank account" and not get_user_by_username(form.from_username.data).treasurer:
            raise ValidationError("Only treasurers can transfer deposits to the bank account")


    return _from_is_treasurer_if_destination_is_bankaccount


def validate_from_bankaccount_if_to_is_treasurer():

    def _to_is_treasurer_if_origin_is_bankaccount(form, field):
        if field.data == "bank account" and not get_user_by_username(form.to_username.data).treasurer:
            raise ValidationError("Only treasurers can draw deposits from the bank account")

    return _to_is_treasurer_if_origin_is_bankaccount

def validate_required_if_to_is_not_bank_account():

    def _to_is_bank_account_or_password_required(form, field):
        if form.to_username.data != "bank account" and not len(field.data):
            raise ValidationError("Password is required")

    return _to_is_bank_account_or_password_required

def validate_required_if_from_is_not_bank_account():
    def _from_is_bank_account_or_password_required(form, field):
        if form.from_username.data != "bank account" and not len(field.data):
            raise ValidationError("Password is required")

    return _from_is_bank_account_or_password_required


