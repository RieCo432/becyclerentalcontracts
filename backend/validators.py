from wtforms.validators import ValidationError
from backend.database import get_deposit_bearer_balance

def validate_deposit_bearer_having_sufficient_funds():

    def _deposit_bearer_has_enough_funds(form, field):
        if get_deposit_bearer_balance(field.data) < form.depositAmountReturned.data:
            raise ValidationError("The selected deposit bearer has insufficient funds to return the desired deposit.")

    return _deposit_bearer_has_enough_funds