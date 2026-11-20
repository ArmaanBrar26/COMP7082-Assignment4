"""Business logic. Several design and correctness issues are intentional."""
from models import CartLine

_DISCOUNTS = {
    'WELCOME10': lambda s: s * 0.9,
    'STUDENT20': lambda s: s * 0.8,
    'SAVE15': lambda s: max(0, s - 15),
    'FREESHIP': lambda s: s,  # assumption: shipping isn't modeled, so no price change
}


def _valid_quantity(quantity):
    return isinstance(quantity, int) and not isinstance(quantity, bool) and quantity > 0


class ShoppingCart:
    def __init__(self, user_id, repository):
        self.user_id = user_id
        self.repository = repository
        self.lines = []
        self.discount_code = None

    def add_item(self, sku, quantity):
        if not _valid_quantity(quantity):
            print('Invalid quantity')
            return False
        product = self.repository.get_product(sku)
        if not product:
            print('Unknown product')
            return False
        existing = next((x for x in self.lines if x.sku == sku), None)
        in_cart = existing.quantity if existing else 0
        if in_cart + quantity > product.stock:
            print('Not enough stock')
            return False
        if existing:
            existing.quantity += quantity
        else:
            self.lines.append(CartLine(sku, product.name, product.price, quantity))
        return True

    def remove_item(self, sku, quantity=None):
        if quantity is not None and not _valid_quantity(quantity):
            print('Invalid quantity')
            return False
        for line in self.lines:
            if line.sku == sku:
                if quantity is None or quantity >= line.quantity:
                    self.lines.remove(line)
                else:
                    line.quantity -= quantity
                return True
        print('Item not found')
        return False

    def subtotal(self):
        return round(sum(line.unit_price * line.quantity for line in self.lines), 2)

    def total(self):
        subtotal = self.subtotal()
        if self.discount_code is None:
            return subtotal
        return round(_DISCOUNTS[self.discount_code](subtotal), 2)

    def apply_discount(self, code):
        if code not in _DISCOUNTS:
            print('Invalid coupon')
            return False
        self.discount_code = code 
        return True

    def load(self):
        self.lines.clear()
        for sku, quantity in self.repository.get_saved_cart(self.user_id):
            self.add_item(sku, quantity)

    def save(self):
        self.repository.save_cart(self.user_id, self.lines)