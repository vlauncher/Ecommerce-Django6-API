import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from catalog.models import Category, Product, ProductImage, ProductVariant, ProductType
from inventory.models import StockRecord, Warehouse
from vendors.models import Vendor

User = get_user_model()

user = User.objects.filter(email='v2dent@gmail.com').first()
if not user:
    user = User.objects.create_user(
        email='v2dent@gmail.com',
        first_name='Samson',
        last_name='Amos',
        is_active=True
    )

vendor, _ = Vendor.objects.get_or_create(
    owner=user,
    defaults={
        'store_name': 'V2Dent Tech & Gear Store',
        'slug': 'v2dent-store',
        'description': 'Official Storefront for High-Performance Laptops, Fashion & Computer Hardware',
        'is_verified': True
    }
)

prod_type, _ = ProductType.objects.get_or_create(name='Standard Physical Item', slug='standard-physical-item')
warehouse, _ = Warehouse.objects.get_or_create(name='Main Fulfillment Hub', code='WH-MAIN')

categories_data = [
    {'name': 'Laptops & Computers', 'slug': 'laptops-computers', 'description': 'High performance gaming & workstation laptops'},
    {'name': 'Fashion & Clothing', 'slug': 'fashion-clothing', 'description': 'Modern minimalist streetwear & jackets'},
    {'name': 'Graphics Cards & GPUs', 'slug': 'gpus-hardware', 'description': 'NVIDIA RTX & AMD Radeon Graphics Accelerators'}
]

categories_map = {}
for cat in categories_data:
    obj = Category.objects.filter(slug=cat['slug']).first()
    if not obj:
        obj = Category.objects.add_root(name=cat['name'], slug=cat['slug'], description=cat['description'])
    categories_map[cat['slug']] = obj

products_data = [
    # LAPTOPS
    {
        'title': 'Razer Blade 16 Gaming Laptop',
        'slug': 'razer-blade-16-gaming-laptop',
        'category': 'laptops-computers',
        'price': '2999.99',
        'description': 'NVIDIA GeForce RTX 4090, Intel Core i9 13950HX, 32GB DDR5 RAM, 2TB NVMe SSD, Dual-Mode Mini-LED Display.',
        'image': 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?auto=format&fit=crop&w=800&q=80',
        'sku': 'RZ-BLADE16-4090'
    },
    {
        'title': 'MacBook Pro 16" M3 Max',
        'slug': 'macbook-pro-16-m3-max',
        'category': 'laptops-computers',
        'price': '3499.00',
        'description': '16-core CPU, 40-core GPU, 48GB Unified Memory, 1TB SSD. Liquid Retina XDR Display in Space Black.',
        'image': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=800&q=80',
        'sku': 'MBP-16-M3MAX'
    },
    {
        'title': 'Dell XPS 15 OLED Workstation',
        'slug': 'dell-xps-15-oled-workstation',
        'category': 'laptops-computers',
        'price': '2199.50',
        'description': '3.5K OLED Touchscreen, Intel Core i7-13700H, RTX 4060 8GB, 32GB RAM, CNC Machined Aluminum Chassis.',
        'image': 'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=800&q=80',
        'sku': 'DELL-XPS15-OLED'
    },
    {
        'title': 'ASUS ROG Zephyrus G14 OLED',
        'slug': 'asus-rog-zephyrus-g14-oled',
        'category': 'laptops-computers',
        'price': '1599.99',
        'description': 'Ultra-portable gaming beast powered by AMD Ryzen 9 8945HS & RTX 4070, 3K 120Hz OLED display.',
        'image': 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=800&q=80',
        'sku': 'ASUS-ROG-G14'
    },

    # CLOTHING
    {
        'title': 'Urban Techwear Waterproof Jacket',
        'slug': 'urban-techwear-waterproof-jacket',
        'category': 'fashion-clothing',
        'price': '245.00',
        'description': '3-Layer Gore-Tex membrane, articulated tactical pockets, Fidlock magnetic buckles, storm hood.',
        'image': 'https://images.unsplash.com/photo-1544441893-675973e31985?auto=format&fit=crop&w=800&q=80',
        'sku': 'TECHWEAR-JXT-01'
    },
    {
        'title': 'Minimalist Heavyweight Oversized Hoodie',
        'slug': 'minimalist-heavyweight-oversized-hoodie',
        'category': 'fashion-clothing',
        'price': '110.00',
        'description': '500 GSM French Terry Cotton, dropped shoulders, double-lined hood, premium ribbed cuffs.',
        'image': 'https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=800&q=80',
        'sku': 'HOODIE-500GSM-BLK'
    },
    {
        'title': 'Japanese Denim Raw Selvedge Jeans',
        'slug': 'japanese-denim-raw-selvedge-jeans',
        'category': 'fashion-clothing',
        'price': '185.00',
        'description': '14.5oz Kurabo Mills Raw Indigo Denim, red line selvedge detail, custom brass hardware.',
        'image': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=800&q=80',
        'sku': 'JPN-SELVEDGE-14OZ'
    },

    # GPUS
    {
        'title': 'NVIDIA GeForce RTX 4090 Founders Edition',
        'slug': 'nvidia-geforce-rtx-4090-founders-edition',
        'category': 'gpus-hardware',
        'price': '1599.99',
        'description': '24GB GDDR6X, Ada Lovelace Architecture, DLSS 3 Frame Generation, 4K Ray Tracing Dominance.',
        'image': 'https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?auto=format&fit=crop&w=800&q=80',
        'sku': 'NV-RTX4090-FE'
    },
    {
        'title': 'ASUS ROG Strix RTX 4080 Super OC',
        'slug': 'asus-rog-strix-rtx-4080-super-oc',
        'category': 'gpus-hardware',
        'price': '1249.99',
        'description': '16GB GDDR6X, Axial-tech fans, diecast shroud & backplate, dual BIOS switch.',
        'image': 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=800&q=80',
        'sku': 'STRIX-RTX4080S-OC'
    },
    {
        'title': 'AMD Radeon RX 7900 XTX Nitro+',
        'slug': 'amd-radeon-rx-7900-xtx-nitro',
        'category': 'gpus-hardware',
        'price': '999.00',
        'description': '24GB GDDR6, RDNA 3 Chiplet Architecture, ARGB lightbar, vapor chamber cooling.',
        'image': 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=800&q=80',
        'sku': 'SAPPHIRE-7900XTX-NITRO'
    }
]

created_count = 0
for item in products_data:
    cat = categories_map[item['category']]
    prod, created = Product.objects.get_or_create(
        slug=item['slug'],
        defaults={
            'vendor': vendor,
            'product_type': prod_type,
            'category': cat,
            'name': item['title'],
            'description': item['description'],
            'min_price': item['price'],
            'max_price': item['price'],
            'status': 'published'
        }
    )
    if created:
        created_count += 1
    
    # Attach product image
    ProductImage.objects.get_or_create(
        product=prod,
        image=item['image'],
        defaults={'is_primary': True}
    )

    # Attach variant
    variant, _ = ProductVariant.objects.get_or_create(
        product=prod,
        sku=item['sku'],
        defaults={
            'name': item['title'],
            'price': item['price'],
            'is_active': True
        }
    )

    # Attach StockRecord
    StockRecord.objects.get_or_create(
        variant=variant,
        warehouse=warehouse,
        defaults={'quantity': 50, 'low_stock_threshold': 5}
    )

print(f"SUCCESSFULLY SEEDED {created_count} NEW PRODUCTS AND CATEGORIES FOR VENDOR {vendor.store_name} ({user.email})")
