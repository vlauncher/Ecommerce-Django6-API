from django.test import TestCase
from django.contrib.auth import get_user_model
from catalog.models import Category, ProductType, Product, ProductVariant
from vendors.models import Vendor
from inventory.models import Warehouse, StockRecord
from inventory.services import reserve_stock_atomic, InsufficientStockError

User = get_user_model()


class InventoryServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="seller@example.com", password="Password123!", is_active=True)
        self.vendor = Vendor.objects.create(owner=self.user, store_name="Stock Shop", slug="stock-shop", status=Vendor.Status.ACTIVE)
        self.category = Category.add_root(name="Gadgets", slug="gadgets")
        self.product_type = ProductType.objects.create(name="Gadget", slug="gadget")
        self.product = Product.objects.create(vendor=self.vendor, product_type=self.product_type, category=self.category, name="Camera", slug="camera", status=Product.Status.ACTIVE)
        self.variant = ProductVariant.objects.create(product=self.product, sku="CAM-01", price="500.00")
        self.warehouse = Warehouse.objects.create(name="Main Hub", code="HUB-01")
        self.stock_record = StockRecord.objects.create(variant=self.variant, warehouse=self.warehouse, quantity=10, reserved=0)

    def test_atomic_stock_reservation(self):
        reserve_stock_atomic(self.variant.id, self.warehouse.id, quantity=3, reference_id="ORD-123")
        self.stock_record.refresh_from_db()
        self.assertEqual(self.stock_record.reserved, 3)
        self.assertEqual(self.stock_record.available_quantity, 7)

    def test_insufficient_stock_error(self):
        with self.assertRaises(InsufficientStockError):
            reserve_stock_atomic(self.variant.id, self.warehouse.id, quantity=15)
