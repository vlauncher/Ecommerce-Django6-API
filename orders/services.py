import secrets
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from orders.models import Order, VendorSubOrder, OrderItem, OrderLog
from cart.models import Cart


def generate_order_number():
    date_str = timezone.now().strftime("%Y%m%d")
    random_hex = secrets.token_hex(4).upper()
    return f"ORD-{date_str}-{random_hex}"


def create_order_from_cart(user, cart, shipping_address, billing_address, notes=""):
    """
    Atomically creates a master Order, splits vendor sub-orders,
    snapshots line items, and clears the cart.
    """
    if not cart.items.exists():
        raise ValueError("Cart is empty.")

    with transaction.atomic():
        order_number = generate_order_number()

        # Group items by vendor
        vendor_items_map = {}
        for cart_item in cart.items.select_related("variant__product__vendor").all():
            vendor = cart_item.variant.product.vendor
            if vendor not in vendor_items_map:
                vendor_items_map[vendor] = []
            vendor_items_map[vendor].append(cart_item)

        # Calculate master order subtotal
        subtotal = sum(item.subtotal for item in cart.items.all())
        shipping_total = Decimal("0.00")
        tax_total = Decimal("0.00")
        discount_total = Decimal("0.00")
        grand_total = subtotal + shipping_total + tax_total - discount_total

        # 1. Create master Order
        order = Order.objects.create(
            order_number=order_number,
            user=user,
            shipping_address=shipping_address,
            billing_address=billing_address,
            subtotal=subtotal,
            shipping_total=shipping_total,
            tax_total=tax_total,
            discount_total=discount_total,
            grand_total=grand_total,
            notes=notes,
        )
        order.place_order()
        order.save()

        # 2. Create VendorSubOrders and OrderItems
        for vendor, cart_items in vendor_items_map.items():
            v_subtotal = sum(ci.subtotal for ci in cart_items)
            commission_rate = vendor.commission_rate / Decimal("100.00")
            commission_amount = (v_subtotal * commission_rate).quantize(Decimal("0.01"))
            vendor_payout = v_subtotal - commission_amount

            sub_order = VendorSubOrder.objects.create(
                order=order,
                vendor=vendor,
                subtotal=v_subtotal,
                commission_amount=commission_amount,
                vendor_payout=vendor_payout,
            )

            for ci in cart_items:
                variant = ci.variant
                product = variant.product
                attr_dict = {
                    val.attribute.name: val.attribute_option.value if val.attribute_option else val.value_text
                    for val in variant.attribute_values.select_related("attribute", "attribute_option").all()
                }

                OrderItem.objects.create(
                    order=order,
                    sub_order=sub_order,
                    variant=variant,
                    product_name=product.name,
                    variant_name=variant.name,
                    sku=variant.sku,
                    variant_attributes=attr_dict,
                    unit_price=variant.price,
                    quantity=ci.quantity,
                    line_total=ci.subtotal,
                )

        # 3. Audit log
        OrderLog.objects.create(
            order=order,
            from_status=Order.Status.DRAFT,
            to_status=Order.Status.PENDING_PAYMENT,
            performed_by=user,
            notes="Order created via checkout.",
        )

        # 4. Clear Cart
        cart.items.all().delete()

        return order
