from django.db import models
from django.core.validators import EmailValidator


class Technician(models.Model):
    """External technicians/companies that perform maintenance"""
    company_name = models.CharField(max_length=200, verbose_name="Company Name")
    technician_name = models.CharField(max_length=200, verbose_name="Technician Name")
    email = models.EmailField(validators=[EmailValidator()], blank=True)
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Phone Number")
    alternate_phone = models.CharField(max_length=20, blank=True, verbose_name="Alternate Phone")
    address = models.TextField(blank=True, verbose_name="Physical Address")
    specialization = models.CharField(max_length=200, blank=True, verbose_name="Specialization/Expertise")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['company_name', 'technician_name']
        verbose_name = 'Technician'
        verbose_name_plural = 'Technicians'

    def __str__(self):
        return f"{self.company_name} - {self.technician_name}"


class TechnicianAssistant(models.Model):
    """Assistants working under a technician"""
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name='assistants')
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=100, blank=True, verbose_name="Role/Position")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Technician Assistant'
        verbose_name_plural = 'Technician Assistants'

    def __str__(self):
        return f"{self.name} (Assistant to {self.technician.technician_name})"


class TechnicianService(models.Model):
    """Services/repairs performed by technicians with costs"""
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name='services')
    service_name = models.CharField(max_length=200, verbose_name="Service/Repair Name")
    description = models.TextField(blank=True)
    typical_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Typical Cost (KES)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['service_name']
        verbose_name = 'Technician Service'
        verbose_name_plural = 'Technician Services'

    def __str__(self):
        return f"{self.service_name} - {self.technician.company_name}"


class TechnicianRecommendation(models.Model):
    """Recommendations made by technicians"""
    RECOMMENDATION_TYPES = [
        ('REPAIR', 'Repair'),
        ('REPLACE', 'Replace'),
        ('UPGRADE', 'Upgrade'),
        ('MAINTENANCE', 'Regular Maintenance'),
        ('DISPOSE', 'Dispose'),
        ('OTHER', 'Other'),
    ]
    
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name='recommendations')
    category_name = models.CharField(max_length=200, blank=True, verbose_name="Category / Item (optional)",
                                     help_text='e.g. Laptops, Printers, Network Switch')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    description = models.TextField(verbose_name="Recommendation Details")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Estimated Cost (KES)")
    priority = models.CharField(max_length=20, choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('URGENT', 'Urgent')], default='MEDIUM')
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Technician Recommendation'
        verbose_name_plural = 'Technician Recommendations'

    def __str__(self):
        label = self.category_name or 'General'
        return f"{self.get_recommendation_type_display()} for {label} by {self.technician.technician_name}"
