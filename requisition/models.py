from django.db import models
from django.contrib.auth.models import User


class Requisition(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('On Hold', 'On Hold'),
        ('Bought', 'Bought'),
    ]
    
    COMPANY_CHOICES = [
        ('Tera', 'Tera'),
        ('Flux', 'Flux'),
        ('Tamuwa', 'Tamuwa'),
    ]

    req_no = models.CharField(max_length=20, db_index=True, verbose_name="Requisition No.")
    company = models.CharField(max_length=20, choices=COMPANY_CHOICES, default='Tamuwa', verbose_name="Company")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, verbose_name="Summary / Description")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requisitions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['req_no', 'company']  # Same req_no allowed for different companies

    def __str__(self):
        return f"[{self.company}] {self.req_no} – {self.title}"

    @property
    def total_amount(self):
        """Only count approved items in the grand total."""
        return sum(item.total_price for item in self.items.all() if item.is_approved)

    @property
    def total_amount_all(self):
        """Full total including non-approved items (for reference)."""
        return sum(item.total_price for item in self.items.all())

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class RequisitionItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ('Asset', 'Asset'),
        ('Service', 'Service'),
    ]
    
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES, default='Asset', verbose_name="Type")
    item_name = models.CharField(max_length=200, verbose_name="Item / Service")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    is_approved = models.BooleanField(default=True, verbose_name="Approved")
    rejection_reason = models.CharField(
        max_length=255, blank=True, default='',
        verbose_name="Reason (if not approved)"
    )
    # Track if this item has been processed (added to assets for assets, completed for services)
    is_processed = models.BooleanField(default=False, verbose_name="Processed")
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_items')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item_name} x{self.quantity}"

    @property
    def total_price(self):
        return self.unit_price * self.quantity
