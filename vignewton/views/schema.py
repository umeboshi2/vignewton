import colander
import deform

def deferred_choices(node, kw):
    choices = kw['choices']
    return deform.widget.SelectWidget(values=choices)

def make_select_widget(choices):
    return deform.widget.SelectWidget(values=choices)


class AddUserSchema(colander.Schema):
    user = colander.SchemaNode(
        colander.Integer(),
        title="User",
        widget=deferred_choices,
        description="User to add",
        )
    
    
class CreditAmountSchema(colander.Schema):
    amount = colander.SchemaNode(
        colander.String(),
        title='Amount',
        description="Amount of creditsffff",
        widget=deform.widget.TextInputWidget(mask='$990',
                                             mask_placeholder='0'),
        )
    
class AccountCreditAmountSchema(colander.Schema):
    user = colander.SchemaNode(
        colander.String(),
        title='User',
        widget=deferred_choices,
        description="Amount of User's credits",
        )
    amount = colander.SchemaNode(
        colander.Integer(),
        title='Amount',
        description="Amount of credits",
        )
    
    
