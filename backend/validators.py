from wtforms.validators import ValidationError
from backend.database import get_deposit_bearer_balance, get_deposit_amount_paid

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
            raise ValueError("Deposit amount cannot be negative.")

    return _deposit_amount_is_not_negative