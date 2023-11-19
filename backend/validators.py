from wtforms.validators import ValidationError
from backend.database import get_deposit_bearer_balance, get_deposit_amount_paid, check_if_username_exists
from backend.user_functions import check_user_password

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