from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, variation
from .models import CartItem, Cart
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []

    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]

            try:
                variation_instance = variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation_instance)
            except variation.DoesNotExist:  
                pass

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )

    is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()

    if is_cart_item_exists:
        cart_items = CartItem.objects.filter(product=product, cart=cart)

        for cart_item in cart_items:
            # Check if all variations match
            if set(cart_item.variations.all()) == set(product_variation):
                cart_item.quantity += 1
                cart_item.save()
                break
        else:
            # If no matching cart item found, create a new one
            new_cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            new_cart_item.variations.set(product_variation)
            new_cart_item.save()
    else:
        # If no cart item exists, create a new one
        new_cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
        new_cart_item.variations.set(product_variation)
        new_cart_item.save()

    return redirect('cart')

def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)

    # Use filter instead of get to handle multiple objects
    cart_items = CartItem.objects.filter(product=product, cart=cart)

    if cart_items.exists():
        # If there are multiple items, decrease quantity of each
        for cart_item in cart_items:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()

    return redirect('cart')

def remove_cart_item(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)

    # Use filter instead of get to handle multiple objects
    cart_item = CartItem.objects.filter(product=product, cart=cart).first()

    if cart_item:
        cart_item.delete()

    return redirect('cart')
def cart(request, total=0, quantity=0, cart_item=None):
    try:
        tax = 0
        grand_total = 0
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total
    }

    return render(request, 'store/cart.html', context)