import json
from functools import wraps
from urllib.parse import urlencode

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.db import IntegrityError
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.encoding import force_str
from django.utils.dateparse import parse_date
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_GET, require_http_methods

from .models import Gift, GiftAssignment, GiftGiver, GiftList, GiftReceiver


def payload(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}


def error(message, status=400):
    return JsonResponse({"detail": message}, status=status)


@require_GET
def healthz(request):
    return JsonResponse({"status": "ok"})


def api_login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error("Authentication required.", 401)
        return view(request, *args, **kwargs)

    return wrapped


def gift_data(gift):
    try:
        assignment = gift.assignment
    except GiftAssignment.DoesNotExist:
        assignment = None
    return {
        "id": gift.id,
        "name": gift.name,
        "detail": gift.text_entry,
        "url": gift.source_url,
        "giver_id": assignment.giver_id if assignment else None,
    }


def list_data(gift_list):
    gifts = list(gift_list.gifts.select_related("assignment__giver").all())
    return {
        "id": gift_list.id,
        "receiver": gift_list.receiver.name,
        "occasion": gift_list.occasion,
        "date": gift_list.event_date.isoformat() if gift_list.event_date else "Upcoming",
        "gifts": [gift_data(gift) for gift in gifts],
    }


@require_GET
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})


@require_http_methods(["POST"])
def register(request):
    data = payload(request)
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not username or not email or len(password) < 8:
        return error("Name, email, and an 8-character password are required.")
    if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
        return error("An account with that name or email already exists.")
    user = User.objects.create_user(username=username, email=email, password=password)
    # An invited giver automatically receives access after registering with their invite email.
    GiftGiver.objects.filter(email__iexact=email, account__isnull=True).update(account=user)
    login(request, user)
    return JsonResponse({"user": {"id": user.id, "name": user.get_full_name() or user.username, "email": user.email}}, status=201)


@require_http_methods(["POST"])
def login_view(request):
    data = payload(request)
    identifier = data.get("email", "").strip()
    user = User.objects.filter(email__iexact=identifier).first()
    user = authenticate(request, username=user.username if user else identifier, password=data.get("password", ""))
    if not user:
        return error("Email or password is incorrect.", 401)
    login(request, user)
    return JsonResponse({"user": {"id": user.id, "name": user.get_full_name() or user.username, "email": user.email}})


@require_http_methods(["POST"])
def password_reset(request):
    """Send a reset link without revealing whether the email has an account."""
    email = payload(request).get("email", "").strip().lower()
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user:
        uid = urlsafe_base64_encode(str(user.pk).encode())
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL}/?{urlencode({'reset_uid': uid, 'reset_token': token})}"
        send_mail(
            "Reset your GoGoGiftList password",
            "We received a request to reset your GoGoGiftList password.\n\n"
            f"Choose a new password: {reset_url}\n\n"
            "If you did not request this, you can safely ignore this email.",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    return JsonResponse({"detail": "If an account exists for that email, a reset link has been sent."})


@require_http_methods(["POST"])
def password_reset_confirm(request):
    data = payload(request)
    try:
        user_id = force_str(urlsafe_base64_decode(data.get("uid", "")))
        user = User.objects.get(pk=user_id, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return error("This password-reset link is invalid or has expired.")
    if not default_token_generator.check_token(user, data.get("token", "")):
        return error("This password-reset link is invalid or has expired.")
    password = data.get("password", "")
    try:
        validate_password(password, user)
    except ValidationError as exc:
        return error(" ".join(exc.messages))
    user.set_password(password)
    user.save(update_fields=["password"])
    return JsonResponse({"detail": "Your password has been reset. You can now sign in."})


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return JsonResponse({"ok": True})


@api_login_required
@require_GET
def me(request):
    user = request.user
    return JsonResponse({"user": {"id": user.id, "name": user.get_full_name() or user.username, "email": user.email}})


@api_login_required
@require_http_methods(["GET", "POST"])
def lists(request):
    if request.method == "GET":
        records = GiftList.objects.filter(owner=request.user).select_related("receiver")
        return JsonResponse({"lists": [list_data(record) for record in records]})
    data = payload(request)
    receiver_name = data.get("receiver", "").strip()
    occasion = data.get("occasion", "").strip()
    if not receiver_name or not occasion:
        return error("A receiver and occasion are required.")
    receiver, _ = GiftReceiver.objects.get_or_create(owner=request.user, name=receiver_name)
    try:
        record = GiftList.objects.create(
            owner=request.user,
            receiver=receiver,
            name=data.get("name", "").strip() or occasion,
            occasion=occasion,
            event_date=parse_date(data.get("date", "")) if data.get("date") else None,
        )
    except IntegrityError:
        return error("That receiver already has a list with this name.")
    return JsonResponse({"list": list_data(record)}, status=201)


@api_login_required
@require_http_methods(["POST"])
def gifts(request, list_id):
    gift_list = GiftList.objects.filter(id=list_id, owner=request.user).first()
    if not gift_list:
        return error("Gift list not found.", 404)
    data = payload(request)
    name = data.get("name", "").strip()
    detail = data.get("detail", "").strip()
    url = data.get("url", "").strip()
    if not (name or detail or url):
        return error("Enter a gift name, detail, or URL.")
    gift = Gift.objects.create(gift_list=gift_list, name=name, text_entry=detail, source_url=url, sort_order=gift_list.gifts.count())
    return JsonResponse({"gift": gift_data(gift)}, status=201)


@api_login_required
@require_http_methods(["GET", "POST"])
def givers(request):
    if request.method == "GET":
        records = GiftGiver.objects.filter(owner=request.user)
        return JsonResponse({"givers": [{"id": item.id, "name": item.name, "email": item.email} for item in records]})
    data = payload(request)
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    if not name or not email:
        return error("A name and email are required.")
    account = User.objects.filter(email__iexact=email).first()
    try:
        giver = GiftGiver.objects.create(owner=request.user, name=name, email=email, account=account)
    except IntegrityError:
        return error("That gift giver already exists.")
    return JsonResponse({"giver": {"id": giver.id, "name": giver.name, "email": giver.email}}, status=201)


@api_login_required
@require_http_methods(["POST"])
def assignment(request, gift_id):
    gift = Gift.objects.filter(id=gift_id, gift_list__owner=request.user).first()
    if not gift:
        return error("Gift not found.", 404)
    giver_id = payload(request).get("giver_id")
    if not giver_id:
        GiftAssignment.objects.filter(gift=gift).delete()
        return JsonResponse({"gift": gift_data(gift)})
    giver = GiftGiver.objects.filter(id=giver_id, owner=request.user).first()
    if not giver:
        return error("Gift giver not found.", 404)
    assignment, _ = GiftAssignment.objects.update_or_create(gift=gift, defaults={"giver": giver})
    gift.assignment = assignment
    return JsonResponse({"gift": gift_data(gift)})


@api_login_required
@require_GET
def giver_assignments(request):
    assignments = GiftAssignment.objects.filter(giver__account=request.user).select_related("gift__gift_list__receiver", "giver")
    return JsonResponse({"assignments": [{
        "id": item.gift.id,
        "name": item.gift.name,
        "detail": item.gift.text_entry,
        "url": item.gift.source_url,
        "receiver": item.gift.gift_list.receiver.name,
        "occasion": item.gift.gift_list.occasion,
    } for item in assignments]})
