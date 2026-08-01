from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers
from catalog.models import ProductVariant
from cart.models import Cart, CartItem, SavedForLater
from cart.serializers import (
    CartSerializer,
    CartItemSerializer,
    CartItemAddUpdateSerializer,
    SavedForLaterSerializer,
)


def get_or_create_cart(request):
    """Retrieve or initialize cart for authenticated user or guest session."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart


@extend_schema(tags=["Cart"])
class CartDetailView(generics.RetrieveAPIView):
    """Retrieve current shopping cart for user or guest."""

    permission_classes = [permissions.AllowAny]
    serializer_class = CartSerializer

    def get_object(self):
        return get_or_create_cart(self.request)


@extend_schema(tags=["Cart"])
class CartItemAddView(generics.CreateAPIView):
    """Add a product variant SKU to cart."""

    permission_classes = [permissions.AllowAny]
    serializer_class = CartItemAddUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant_id = serializer.validated_data["variant_id"]
        quantity = serializer.validated_data["quantity"]
        variant = generics.get_object_or_404(ProductVariant, id=variant_id, is_active=True)

        cart = get_or_create_cart(request)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, variant=variant,
            defaults={"quantity": quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save(update_fields=["quantity"])

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


@extend_schema(tags=["Cart"])
class CartItemUpdateDeleteView(generics.GenericAPIView):
    """Update item quantity or remove item from cart."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=inline_serializer("CartItemQuantity", {"quantity": drf_serializers.IntegerField(min_value=1)}),
        responses={200: CartSerializer},
    )
    def patch(self, request, pk):
        cart = get_or_create_cart(request)
        item = generics.get_object_or_404(CartItem, pk=pk, cart=cart)
        quantity = request.data.get("quantity")
        if quantity and int(quantity) > 0:
            item.quantity = int(quantity)
            item.save(update_fields=["quantity"])
        return Response(CartSerializer(cart).data)

    @extend_schema(responses={200: CartSerializer})
    def delete(self, request, pk):
        cart = get_or_create_cart(request)
        item = generics.get_object_or_404(CartItem, pk=pk, cart=cart)
        item.delete()
        return Response(CartSerializer(cart).data)


@extend_schema(tags=["Cart"])
class CartClearView(generics.GenericAPIView):
    """Remove all items from shopping cart."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: CartSerializer})
    def delete(self, request):
        cart = get_or_create_cart(request)
        cart.items.all().delete()
        return Response(CartSerializer(cart).data)


@extend_schema(tags=["Cart"])
class CartMergeView(generics.GenericAPIView):
    """Merge guest cart items into authenticated user cart on login."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=inline_serializer("CartMergeRequest", {"session_key": drf_serializers.CharField()}),
        responses={200: CartSerializer},
    )
    def post(self, request):
        guest_session_key = request.data.get("session_key")
        if not guest_session_key:
            return Response({"detail": "session_key is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            guest_cart = Cart.objects.get(session_key=guest_session_key)
        except Cart.DoesNotExist:
            return Response(CartSerializer(get_or_create_cart(request)).data)

        user_cart = get_or_create_cart(request)
        for guest_item in guest_cart.items.all():
            user_item, created = CartItem.objects.get_or_create(
                cart=user_cart, variant=guest_item.variant,
                defaults={"quantity": guest_item.quantity},
            )
            if not created:
                user_item.quantity += guest_item.quantity
                user_item.save(update_fields=["quantity"])

        guest_cart.delete()
        return Response(CartSerializer(user_cart).data)


@extend_schema(tags=["Saved Items"])
class SavedForLaterListView(generics.ListCreateAPIView):
    """List or save items for later."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SavedForLaterSerializer

    def get_queryset(self):
        return SavedForLater.objects.filter(user=self.request.user).select_related("variant__product")

    def create(self, request, *args, **kwargs):
        variant_id = request.data.get("variant_id")
        variant = generics.get_object_or_404(ProductVariant, id=variant_id)
        saved_item, _ = SavedForLater.objects.get_or_create(user=request.user, variant=variant)
        return Response(SavedForLaterSerializer(saved_item).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Saved Items"])
class SavedForLaterDeleteView(generics.DestroyAPIView):
    """Remove saved item."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SavedForLaterSerializer

    def get_queryset(self):
        return SavedForLater.objects.filter(user=self.request.user)

