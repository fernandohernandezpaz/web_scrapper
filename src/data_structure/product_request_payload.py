from .request_payload import RequestPayload


class ProductRequestPayload(RequestPayload):
    exterior_color = {}
    interior_color = {}
    doors = {}
    drivetrain = {}
    fuel_type = {}
    image_url = {}
    inventory_vehicle_type = {}
    body_style = {}
    state_of_vehicle = {}
    list_product_url = []
    make = {}
    model = {}
    mileage = {}
    price = {}
    stock_number = {}
    title = {}
    description = {}
    transmission = {}
    trim = {}
    vehicle_type = {}
    identifier = {}  # can be the vin for vehicles, hin for ships, serial model
    year = {}
    msrp = {}
    certified = {}
    engine = {}

    def __init__(self, context_request):
        if isinstance(context_request, dict):
            for key, value in context_request.items():
                setattr(self, key, value)

    def get_attrs_product(self):
        exclude_properties = [
            'list_product_url', 'webhook_domain',
            'output_format'
        ]
        attrs = []

        for attr in dir(self):
            if callable(getattr(self, attr)) or attr.startswith('__'):
                continue
            if attr in exclude_properties:
                continue

            attrs.append(attr)

        return list(set(attrs))

    def get_attr(self, attr_name: str):
        if not hasattr(self, attr_name):
            return None, None

        return getattr(self, attr_name, {}).get('type'), getattr(self, attr_name, {}).get('value')

    def get_one_css_class(self):
        for _prop in self.get_attrs_product():
            print(_prop)
            _type, _value = self.get_attr(_prop)
            if _type and _value and _type == 'class':
                if '::text' in _value or '::attr':
                    return _value.split(':')[0]
                return _value

        return None

    def __dict__(self):
        my_dict = {
            'list_product_url': self.list_product_url,
        }
        for _attr in self.get_attrs_product():
            my_dict[_attr] = getattr(self, _attr)
        return my_dict
