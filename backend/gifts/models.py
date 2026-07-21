from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class TimeStampedModel(models.Model):
    """Common audit fields for gift-list records."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class GiftReceiver(TimeStampedModel):
    """A person for whom a user maintains one or more gift lists."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gift_receivers")
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["owner", "name"], name="unique_receiver_name_per_owner")]

    def __str__(self) -> str:
        return self.name


class GiftGiver(TimeStampedModel):
    """A person who can be assigned gifts by a list owner."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gift_givers")
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="gift_giver_profile",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["owner", "name"], name="unique_giver_name_per_owner")]

    def __str__(self) -> str:
        return self.name


class GiftList(TimeStampedModel):
    """A list created by a user for one gift receiver."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gift_lists")
    receiver = models.ForeignKey(GiftReceiver, on_delete=models.PROTECT, related_name="gift_lists")
    name = models.CharField(max_length=200)
    occasion = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    event_date = models.DateField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["is_archived", "event_date", "name"]
        constraints = [models.UniqueConstraint(fields=["owner", "receiver", "name"], name="unique_list_name_for_owner_receiver")]

    def clean(self) -> None:
        super().clean()
        if self.receiver_id and self.owner_id and self.receiver.owner_id != self.owner_id:
            raise ValidationError({"receiver": "The receiver must belong to the list owner."})

    def __str__(self) -> str:
        return self.name


class Gift(TimeStampedModel):
    """An individual desired item entered from text, a URL, or both."""

    gift_list = models.ForeignKey(GiftList, on_delete=models.CASCADE, related_name="gifts")
    name = models.CharField(max_length=300, blank=True)
    source_url = models.URLField(blank=True)
    text_entry = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    priority = models.PositiveSmallIntegerField(default=3)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_purchased = models.BooleanField(default=False)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.CheckConstraint(condition=Q(source_url__gt="") | Q(text_entry__gt="") | Q(name__gt=""), name="gift_requires_url_or_text"),
            models.CheckConstraint(condition=Q(priority__gte=1) & Q(priority__lte=5), name="gift_priority_between_one_and_five"),
        ]

    def __str__(self) -> str:
        return self.name or self.source_url or self.text_entry[:50]


class GiftAssignment(TimeStampedModel):
    """Assigns exactly one gift to a giver for a shareable portion of a list."""

    gift = models.OneToOneField(Gift, on_delete=models.CASCADE, related_name="assignment")
    giver = models.ForeignKey(GiftGiver, on_delete=models.PROTECT, related_name="gift_assignments")
    message_note = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["giver__name", "gift__sort_order", "gift__id"]

    def clean(self) -> None:
        super().clean()
        if self.gift_id and self.giver_id and self.gift.gift_list.owner_id != self.giver.owner_id:
            raise ValidationError({"giver": "The giver must belong to the gift list owner."})

    def __str__(self) -> str:
        return f"{self.gift} → {self.giver}"
