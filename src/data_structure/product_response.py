from typing import Dict

from scrapy.item import Field, Item

# Key = Request property
# Value = Vehicle property class
MAPPER_REQUEST_INTO_VEHICLE_ITEM: Dict = {
    'inventory_vehicle_type': 'inventory_vehicle_type',
    'body_style': 'body_style',
    'state_of_vehicle': 'state_of_vehicle',
    'year': 'year',
    'identifier': 'identifier',
    'make': 'make',
    'model': 'model',
    'trim': 'trim',
    'exterior_color': 'exterior_color',
    'interior_color': 'interior_color',
    'fuel_type': 'fuel_type',
    'doors': 'doors',
    'price': 'price',
    'msrp': 'msrp',
    'image_url': 'image_url',
    'description': 'description',
    'drivetrain': 'drivetrain',
    'transmission': 'transmission',
    'title': 'title',
    'stock_number': 'stock_number',
    'mileage': 'mileage',
    'certified': 'certified',
    'engine': 'engine',
}


class Product(Item):
    inventory_vehicle_type = Field()
    body_style = Field()
    state_of_vehicle = Field()
    year = Field()
    make = Field()
    model = Field()
    identifier = Field()
    exterior_color = Field()
    interior_color = Field()
    date_sold = Field()
    description = Field()
    doors = Field()
    drivetrain = Field()
    final_url = Field()  # product url
    fuel_type = Field()
    image_type = Field()
    image_url = Field()
    mileage = Field()
    mileage_unit = Field()
    price = Field()
    title = Field()
    transmission = Field()
    trim = Field()
    type = Field()
    vehicle_type = Field()
    stock_number = Field()
    certified = Field()
    msrp = Field()
    engine = Field()
    item_category = Field()

    def to_dict(self):
        return dict(self)

    def set_value(self, key: str, value):
        key_mapped = MAPPER_REQUEST_INTO_VEHICLE_ITEM.get(key)
        if not key_mapped:
            return None

        self[key_mapped] = value

