# shalom_enterprise/dashboard.py
from django.utils.translation import gettext_lazy as _

def dashboard_callback(request, context):
    """
    Callback to prepare custom variables for index template
    """
    # Add your custom cards here
    context.update({
        'custom_cards': [
            {
                'title': _('Total Sales'),
                'value': '$12,345',
                'icon': 'point_of_sale',
                'url': '/admin/sales/',
                'description': _('Last 30 days'),
                'color': 'success',
            },
            {
                'title': _('New Customers'),
                'value': '24',
                'icon': 'people',
                'url': '/admin/customers/',
                'description': _('This month'),
                'color': 'info',
            },
            {
                'title': _('Pending Orders'),
                'value': '5',
                'icon': 'shopping_cart',
                'url': '/admin/orders/',
                'description': _('Requiring attention'),
                'color': 'warning',
            },
        ]
    })
    return context