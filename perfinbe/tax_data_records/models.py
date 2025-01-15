from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal
import uuid

class TaxableAccount(models.Model):
    """
    Links to portfolios that require tax tracking and defines their tax settings.
    """
    portfolio = models.OneToOneField(
        'personal_finance_portfolio.Portfolio',
        on_delete=models.CASCADE,
        related_name='tax_settings'
    )
    cost_basis_method = models.CharField(
        max_length=20,
        choices=[
            ('FIFO', 'First In, First Out'),
            ('LIFO', 'Last In, First Out'),
            ('HIFO', 'Highest In, First Out'),
            ('SPECIFIC', 'Specific Identification')
        ],
        default='FIFO'
    )
    wash_sale_tracking = models.BooleanField(
        default=True,
        help_text="Enable wash sale detection and adjustment"
    )

    def __str__(self):
        return f"Tax Settings for {self.portfolio.name}"

class TaxLot(models.Model):
    """
    Represents a specific purchase of securities for tax purposes.
    """
    account = models.ForeignKey(TaxableAccount, on_delete=models.CASCADE)
    transaction = models.OneToOneField(
        'personal_finance_portfolio.Transaction',
        on_delete=models.CASCADE,
        related_name='tax_lot'
    )
    quantity = models.IntegerField()
    acquisition_date = models.DateTimeField()
    cost_basis = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_quantity = models.IntegerField()
    adjusted_basis = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Cost basis adjusted for wash sales"
    )
    
    def __str__(self):
        return (f"Lot {self.transaction.reference_id}: "
                f"{self.remaining_quantity} @ {self.adjusted_basis}")

class TaxLotDisposition(models.Model):
    """
    Records the sale or disposal of securities from specific tax lots.
    """
    tax_lot = models.ForeignKey(
        TaxLot,
        on_delete=models.CASCADE,
        related_name='dispositions'
    )
    sale_transaction = models.ForeignKey(
        'personal_finance_portfolio.Transaction',
        on_delete=models.CASCADE,
        related_name='tax_lot_dispositions'
    )
    quantity = models.IntegerField()
    proceeds = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    holding_period = models.DurationField(
        help_text="Time between acquisition and sale"
    )
    
    def save(self, *args, **kwargs):
        if not self.holding_period:
            self.holding_period = self.date - self.tax_lot.acquisition_date
        super().save(*args, **kwargs)

    def is_long_term(self):
        return self.holding_period >= timedelta(days=365)

class WashSale(models.Model):
    """
    Tracks wash sale adjustments when replacement securities are purchased
    within the wash sale window.
    """
    disposition = models.ForeignKey(
        TaxLotDisposition,
        on_delete=models.CASCADE,
        related_name='wash_sales'
    )
    replacement_lot = models.ForeignKey(
        TaxLot,
        on_delete=models.CASCADE,
        related_name='wash_sale_adjustments'
    )
    disallowed_loss = models.DecimalField(max_digits=10, decimal_places=2)
    wash_sale_window_start = models.DateTimeField()
    wash_sale_window_end = models.DateTimeField()

    def clean(self):
        # Ensure replacement lot is within 30 days before or after disposition
        window_start = self.disposition.date - timedelta(days=30)
        window_end = self.disposition.date + timedelta(days=30)
        
        if not (window_start <= self.replacement_lot.acquisition_date <= window_end):
            raise ValidationError(
                "Replacement lot must be within 30 days of disposition"
            )

class TaxableEvent(models.Model):
    """
    Records tax-relevant events like dividends, return of capital, etc.
    """
    EVENT_TYPES = [
        ('DIV_QUALIFIED', 'Qualified Dividend'),
        ('DIV_ORDINARY', 'Ordinary Dividend'),
        ('ROC', 'Return of Capital'),
        ('STCG', 'Short-Term Capital Gain'),
        ('LTCG', 'Long-Term Capital Gain'),
    ]
    
    account = models.ForeignKey(TaxableAccount, on_delete=models.CASCADE)
    transaction = models.OneToOneField(
        'personal_finance_portfolio.Transaction',
        on_delete=models.CASCADE,
        related_name='taxable_event'
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    
    class Meta:
        indexes = [
            models.Index(fields=['account', 'date', 'event_type'])
        ]

class Form1099B(models.Model):
    """
    Generates and stores Form 1099-B data for tax reporting.
    """
    account = models.ForeignKey(TaxableAccount, on_delete=models.CASCADE)
    tax_year = models.IntegerField()
    dispositions = models.ManyToManyField(TaxLotDisposition)
    
    # Short-term transactions
    st_covered_proceeds = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    st_covered_basis = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    st_uncovered_proceeds = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    
    # Long-term transactions
    lt_covered_proceeds = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    lt_covered_basis = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    lt_uncovered_proceeds = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    
    # Wash sale adjustments
    wash_sale_adjustments = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    
    class Meta:
        unique_together = ('account', 'tax_year')
        indexes = [
            models.Index(fields=['account', 'tax_year'])
        ]

    def calculate_totals(self):
        """Recalculates all totals based on linked dispositions."""
        st_proceeds = Decimal('0')
        st_basis = Decimal('0')
        lt_proceeds = Decimal('0')
        lt_basis = Decimal('0')
        wash_adjustments = Decimal('0')
        
        for disp in self.dispositions.all():
            if disp.is_long_term():
                lt_proceeds += disp.proceeds
                lt_basis += (disp.quantity * disp.tax_lot.adjusted_basis)
            else:
                st_proceeds += disp.proceeds
                st_basis += (disp.quantity * disp.tax_lot.adjusted_basis)
            
            wash_adjustments += sum(
                ws.disallowed_loss for ws in disp.wash_sales.all()
            )
        
        self.lt_covered_proceeds = lt_proceeds
        self.lt_covered_basis = lt_basis
        self.st_covered_proceeds = st_proceeds
        self.st_covered_basis = st_basis
        self.wash_sale_adjustments = wash_adjustments
        self.save()