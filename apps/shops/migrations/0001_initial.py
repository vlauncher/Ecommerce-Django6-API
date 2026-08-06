from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Shop",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("slug", models.SlugField(max_length=150, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_shops", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="ShopMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("owner", "Owner"), ("manager", "Manager"), ("staff", "Staff"), ("customer", "Customer")], default="customer", max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("shop", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="shops.shop")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shop_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("created_at",)},
        ),
        migrations.CreateModel(
            name="ShopInvitation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254)),
                ("role", models.CharField(choices=[("owner", "Owner"), ("manager", "Manager"), ("staff", "Staff"), ("customer", "Customer")], max_length=20)),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("expires_at", models.DateTimeField()),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sent_shop_invitations", to=settings.AUTH_USER_MODEL)),
                ("shop", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitations", to="shops.shop")),
            ],
            options={"indexes": [models.Index(fields=["shop", "email"], name="shops_shopi_shop_id_e92abc_idx")]},
        ),
        migrations.AddConstraint(
            model_name="shopmembership",
            constraint=models.UniqueConstraint(fields=("shop", "user"), name="unique_shop_membership"),
        ),
    ]
